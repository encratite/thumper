import functools
import pettingzoo.utils.env
from gymnasium.spaces import Discrete, MultiDiscrete, Box, Space, Dict
from gymnasium.utils import EzPickle
from pettingzoo.utils.env import AgentID, ObsType
from pettingzoo import AECEnv
from pettingzoo.utils import wrappers
import numpy as np
from game import ThumperGame
from constants import Constant, Action, ActionType, Cost
from action import EnvironmentAction

def env(**kwargs):
	environment = raw_env(**kwargs)
	environment = wrappers.TerminateIllegalWrapper(environment, illegal_reward=-1)
	environment = wrappers.AssertOutOfBoundsWrapper(environment)
	environment = wrappers.OrderEnforcingWrapper(environment)
	return environment

class raw_env(AECEnv, EzPickle):
	metadata = {
		"render_modes": [],
		"name": "Thumper-v0",
		"is_parallelizable": False,
		"render_fps": 1,
	}

	def __init__(self, render_mode: str | None = None, screen_height: int | None = 800):
		EzPickle.__init__(self, render_mode, screen_height)
		super().__init__()
		self.game = ThumperGame()
		self.last_game_players = None
		self.last_action = None
		self.agents: list[AgentID] = [f"player_{str(i)}" for i in range(Constant.PLAYER_COUNT)]
		self.possible_agents = self.agents[:]
		self._reset_common()
		# Current round (1 to 9), one-hot encoded, so 0 to 1 each
		one_hot_encoding = Constant.MAX_ROUNDS * [2]
		nvec = one_hot_encoding
		# Conflict reward
		nvec += one_hot_encoding
		for i in range(Constant.PLAYER_COUNT):
			nvec += [
				# Action type counts (0 - 4)
				5,
				5,
				5,
				# Solari (0 - 10+)
				11,
				# Spice (0 - 10+)
				11,
				# Troops in garrison (0 - 10+)
				11,
				# Troops deployed (0 - 10+)
				11,
				# Influence (-5 or less to 10+)
				16,
				# Swordmaster (0 to 1)
				2,
				# Palace (0 to 1)
				2,
				# Holtzman Shield (0 to 1)
				2,
				# Agents left (0 to 3)
				4,
				# Victory points (0 to 12)
				13
			]
		self._initialize_actions()
		total_actions = len(self.actions)
		self.observation_spaces: dict[AgentID, Dict] = {
			name: Dict({
				"observation": MultiDiscrete(nvec, dtype=np.int8),
				"action_mask": Box(low=0, high=1, shape=(total_actions,), dtype=np.int8)
			})
			for name in self.agents
		}

	@functools.lru_cache(maxsize=None)
	def observation_space(self, agent: AgentID) -> Space:
		return self.observation_spaces[agent]

	@functools.lru_cache(maxsize=None)
	def action_space(self, agent: AgentID) -> Space:
		return self.action_spaces[agent]

	def observe(self, agent: AgentID) -> ObsType | None:
		observation = self._get_observation()
		action_mask = [1 if action.enabled(self.game) else 0 for action in self.actions]
		output = {
			"observation": observation,
			"action_mask": action_mask
		}
		return output

	def reset(self, seed: int | None = None, options: dict | None = None) -> None:
		self._reset_common()
		self.last_game_players = self.game.players
		self.game.reset()

	def step(self, action: pettingzoo.utils.env.ActionType) -> None:
		assert not self.game.game_ended
		assert 0 <= action < len(self.actions)
		environment_action = self.actions[action]
		environment_action.perform(self.game)
		self.agent_selection = self.agents[self.game.current_player_index]
		self.last_action = environment_action.action_enum
		self.rewards = {}
		for i in range(Constant.PLAYER_COUNT):
			player = self.game.players[i]
			reward = player.get_reward()
			name = self.agents[i]
			self.rewards[name] = reward
		self.terminations = {name: self.game.game_ended for name in self.agents}

	def action_masks(self):
		masks = [action.enabled(self.game) for action in self.actions]
		return masks

	def get_last_game_players(self):
		if self.last_game_players is not None:
			output = self.last_game_players
			self.last_game_players = None
			return output
		else:
			return None

	def get_shapes(self):
		agent = self.agents[0]
		state_shape = self.observation_spaces[agent]["observation"].shape
		action_shape = self.action_spaces[agent].n
		return state_shape, action_shape

	def get_action_space(self):
		agent = self.agents[0]
		action_space = self.action_spaces[agent]
		return action_space

	def _reset_common(self):
		self.agent_selection = self.agents[0]
		self.rewards = {name: 0 for name in self.agents}
		self.terminations = {name: False for name in self.agents}
		self.truncations = {name: False for name in self.agents}
		self.infos = {name: {} for name in self.agents}

	def _initialize_actions(self):
		actions = [
			EnvironmentAction(
				self.game.construct_palace,
				ActionType.ECONOMIC,
				Action.CONSTRUCT_PALACE,
				solari=Cost.CONSTRUCT_PALACE,
				enabled=self.game.construct_palace_enabled
			),
			EnvironmentAction(
				self.game.harvester,
				ActionType.ECONOMIC,
				Action.HARVESTER
			),
			EnvironmentAction(
				self.game.refinery,
				ActionType.ECONOMIC,
				Action.REFINERY
			),
			EnvironmentAction(
				self.game.spice_silo,
				ActionType.ECONOMIC,
				Action.SPICE_SILO
			),
			EnvironmentAction(
				self.game.sell_melange,
				ActionType.ECONOMIC,
				Action.SELL_MELANGE,
				spice=1,
				argument=1
			),
			EnvironmentAction(
				self.game.sell_melange,
				ActionType.ECONOMIC,
				Action.SELL_MELANGE,
				spice=2,
				argument=2
			),
			EnvironmentAction(
				self.game.sell_melange,
				ActionType.ECONOMIC,
				Action.SELL_MELANGE,
				spice=3,
				argument=3
			),
			EnvironmentAction(
				self.game.secure_contract,
				ActionType.ECONOMIC,
				Action.SECURE_CONTRACT
			),
			EnvironmentAction(
				self.game.holtzman_shield,
				ActionType.MILITARY,
				Action.HOLTZMAN_SHIELD,
				spice=Cost.HOLTZMAN_SHIELD,
				enabled=self.game.holtzman_shield_enabled
			),
			EnvironmentAction(
				self.game.stone_burner,
				ActionType.MILITARY,
				Action.STONE_BURNER,
				spice=Cost.STONE_BURNER,
				enabled=self.game.stone_burner_enabled,
				enabled_argument=True,
				expand=(1, Constant.PLAYER_COUNT)
			),
			EnvironmentAction(
				self.game.hire_mercenaries,
				ActionType.MILITARY,
				Action.HIRE_MERCENARIES,
				solari=Cost.HIRE_MERCENARIES,
				troops_produced=Constant.HIRE_MERCENARIES_TROOPS_PRODUCED,
				deployment_limit=Constant.HIRE_MERCENARIES_DEPLOYMENT_LIMIT,
				expand=(0, 3)
			),
			EnvironmentAction(
				self.game.quick_strike,
				ActionType.MILITARY,
				Action.QUICK_STRIKE,
				troops_produced=Constant.QUICK_STRIKE_TROOPS_PRODUCED,
				deployment_limit=Constant.QUICK_STRIKE_DEPLOYMENT_LIMIT,
				expand=(0, 2)
			),
			EnvironmentAction(
				self.game.recruitment_center,
				ActionType.MILITARY,
				Action.RECRUITMENT_CENTER
			),
			EnvironmentAction(
				self.game.troop_transports,
				ActionType.MILITARY,
				Action.TROOP_TRANSPORTS,
				enabled=self.game.has_garrison,
				troops_produced=Constant.TROOP_TRANSPORTS_TROOPS_PRODUCED,
				deployment_limit=Constant.TROOP_TRANSPORTS_DEPLOYMENT_LIMIT,
				expand=(0, 4)
			),
			EnvironmentAction(
				self.game.loot_villages,
				ActionType.MILITARY,
				Action.LOOT_VILLAGES
			),
			EnvironmentAction(
				self.game.swordmaster,
				ActionType.POLITICAL,
				Action.SWORDMASTER,
				solari=Cost.SWORDMASTER,
				enabled=self.game.swordmaster_enabled
			),
			EnvironmentAction(
				self.game.sardaukar,
				ActionType.POLITICAL,
				Action.SARDAUKAR,
				spice=Cost.SARDAUKAR
			),
			EnvironmentAction(
				self.game.audience_with_emperor,
				ActionType.POLITICAL,
				Action.AUDIENCE_WITH_EMPEROR,
				spice=Cost.AUDIENCE_WITH_EMPEROR
			),
			EnvironmentAction(
				self.game.mobilization,
				ActionType.POLITICAL,
				Action.MOBILIZATION,
				solari=Cost.MOBILIZATION,
				enabled=self.game.has_garrison,
				troops_produced=Constant.MOBILIZATION_TROOPS_PRODUCED,
				deployment_limit=Constant.MOBILIZATION_DEPLOYMENT_LIMIT,
				expand=(0, 5)
			),
			EnvironmentAction(
				self.game.seek_allies,
				ActionType.POLITICAL,
				Action.SEEK_ALLIES,
				solari=Cost.SEEK_ALLIES
			),
			EnvironmentAction(
				self.game.political_maneuvering,
				ActionType.POLITICAL,
				Action.POLITICAL_MANEUVERING,
				argument=ActionType.ECONOMIC
			),
			EnvironmentAction(
				self.game.political_maneuvering,
				ActionType.POLITICAL,
				Action.POLITICAL_MANEUVERING,
				argument=ActionType.MILITARY
			),
			EnvironmentAction(
				self.game.political_maneuvering,
				ActionType.POLITICAL,
				Action.POLITICAL_MANEUVERING,
				argument=ActionType.POLITICAL
			),
			EnvironmentAction(
				self.game.pass_turn,
				None,
				None
			)
		]
		self.actions = []
		for action in actions:
			if action.expand is not None:
				minimum, maximum = action.expand
				for i in range(minimum, maximum + 1):
					expanded_action = action.argument_copy(i)
					self.actions.append(expanded_action)
			else:
				self.actions.append(action)
		# The action space consists of indexes into self.actions
		total_actions = len(self.actions)
		self.action_spaces = {name: Discrete(total_actions) for name in self.agents}

	def _get_observation(self):
		# One-hot encoding of the current round
		observation = self._get_one_hot_encoding(self.game.round)
		# One-hot encoding of the randomized conflict rewards
		conflict = self.game.conflicts[self.game.round - 1]
		observation += self._get_one_hot_encoding(conflict.id)
		# Resources, etc., of each player
		for player in self.game.players:
			observation += self._get_player_observation(player)
		return np.array(observation, dtype=np.int8)

	def _get_one_hot_encoding(self, value):
		observation = []
		for i in range(Constant.MAX_ROUNDS):
			value = 1 if value == i + 1 else 0
			observation.append(value)
		return observation

	def _get_player_observation(self, player):
		def adjust(x):
			return min(x, 10)

		def adjust_influence(x):
			return max(min(x + 5, 15), 0)

		swordmaster = self._from_bool(player.swordmaster)
		palace = self._from_bool(player.palace)
		holtzman_shield = self._from_bool(player.holtzman_shield)
		observation = self._from_action_types(player)
		observation += [
			adjust(player.spice),
			adjust(player.solari),
			adjust(player.troops_garrison),
			adjust(player.troops_deployed),
			adjust_influence(player.influence),
			swordmaster,
			palace,
			holtzman_shield,
			player.agents_left,
			player.victory_points
		]
		return observation

	def _from_bool(self, value):
		return 1 if value else 0

	def _from_action_types(self, player):
		actions = [
			ActionType.ECONOMIC,
			ActionType.MILITARY,
			ActionType.POLITICAL
		]
		observations = len(actions) * [0]
		for action in player.actions:
			index = actions.index(action)
			observations[index] += 1
		return observations