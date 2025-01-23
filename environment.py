import gymnasium as gym
import numpy as np
from game import ThumperGame
from constants import *

class ThumperEnvironment(gym.Env):
	"""
	Creates an OpenAI gym environment for the Thumper proof of concept game.
	The models are only meant to be trained for a particular position on the table.
	All other players are assumed to be controlled by other reinforcement learning models that were trained in an identical fashion.
	If no other models are provided (i.e. models = None), the environment will randomize the actions of the other players instead.
	This is initially done to bootstrap the training of all models.
	The DQN agent corresponding to the specified position (i.e. models[position - 1]) is not used by the environment.

	Arguments:
		position: an int from 1 to PLAYER_COUNT that determines the player's position on the table
		models: a list of PLAYER_COUNT DQN agents that represent the AIs that will control the other players
	"""
	def __init__(self, position, models=None):
		self.position = position
		self.models = models
		self.game = None
		# Current round (1 to 8)
		nvec = [8]
		for i in range(PLAYER_COUNT):
			nvec += [
				# Action type counts (0 - 4)
				5, 5, 5,
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
				# Agents left (0 to 3)
				4,
				# Victory points (0 to 12)
				13
			]
		self.observation_space = gym.spaces.MultiDiscrete(nvec)
		self._initialize_actions()

	def reset(self):
		self.game = ThumperGame()
		observation = self._get_observation()
		info = {}
		return observation, info

	def step(self, action):
		raise NotImplementedError()
		observation = self._get_observation()
		reward = 0
		terminated = self.game.game_ended
		truncated = False
		info = {}
		return observation, reward, terminated, truncated, info

	def _initialize_actions(self):
		actions = [
			EnvironmentAction(self.game.construct_palace, ActionType.ECONOMIC, Action.CONSTRUCT_PALACE, solari=Cost.CONSTRUCT_PALACE, enabled=self.game.construct_palace_enabled),
			EnvironmentAction(self.game.harvester, ActionType.ECONOMIC, Action.HARVESTER),
			EnvironmentAction(self.game.refinery, ActionType.ECONOMIC, Action.REFINERY),
			EnvironmentAction(self.game.spice_silo, ActionType.ECONOMIC, Action.SPICE_SILO),
			EnvironmentAction(self.game.sell_melange, ActionType.ECONOMIC, Action.SELL_MELANGE, spice=Cost.SELL_MELANGE),
			EnvironmentAction(self.game.secure_contract, ActionType.ECONOMIC, Action.SECURE_CONTRACT),
			EnvironmentAction(self.game.stone_burner, ActionType.MILITARY, Action.STONE_BURNER, spice=Cost.STONE_BURNER, enabled=self.game.stone_burner_enabled, expand=(1, 4)),
			EnvironmentAction(self.game.hire_mercenaries, ActionType.MILITARY, Action.HIRE_MERCENARIES, solari=Cost.HIRE_MERCENARIES, troops_produced=HIRE_MERCENARIES_TROOPS_PRODUCED, deployment_limit=HIRE_MERCENARIES_DEPLOYMENT_LIMIT, expand=(0, 3)),
			EnvironmentAction(self.game.quick_strike, ActionType.MILITARY, Action.QUICK_STRIKE, troops_produced=QUICK_STRIKE_TROOPS_PRODUCED, deployment_limit=QUICK_STRIKE_DEPLOYMENT_LIMIT, expand=(0, 2)),
			EnvironmentAction(self.game.recruitment_center, ActionType.MILITARY, Action.RECRUITMENT_CENTER),
			EnvironmentAction(self.game.troop_transports, ActionType.MILITARY, Action.TROOP_TRANSPORTS, troops_produced=TROOP_TRANSPORTS_TROOPS_PRODUCED, deployment_limit=TROOP_TRANSPORTS_DEPLOYMENT_LIMIT, expand=(0, 4)),
			EnvironmentAction(self.game.loot_villages, ActionType.MILITARY, Action.LOOT_VILLAGES, enabled=self.game.has_garrison),
			EnvironmentAction(self.game.swordmaster, ActionType.POLITICAL, Action.SWORDMASTER, solari=Cost.SWORDMASTER, enabled=self.game.swordmaster_enabled),
			EnvironmentAction(self.game.sardaukar, ActionType.POLITICAL, Action.SARDAUKAR, spice=Cost.SARDAUKAR),
			EnvironmentAction(self.game.audience_with_emperor, ActionType.POLITICAL, Action.AUDIENCE_WITH_EMPEROR, spice=Cost.AUDIENCE_WITH_EMPEROR),
			EnvironmentAction(self.game.mobilization, ActionType.POLITICAL, Action.MOBILIZATION, solari=Cost.MOBILIZATION, troops_produced=MOBILIZATION_TROOPS_PRODUCED, deployment_limit=MOBILIZATION_DEPLOYMENT_LIMIT, expand=(0, 5)),
			EnvironmentAction(self.game.seek_allies, ActionType.POLITICAL, Action.SEEK_ALLIES),
			EnvironmentAction(self.game.political_maneuvering, ActionType.POLITICAL, Action.POLITICAL_MANEUVERING)
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
		# There's one additional pseudo-action for rewards from conflicts and the endgame influence rewards
		total_actions = len(self.actions) + 1
		# The action space consists of indexes into self.actions
		self.action_space = gym.spaces.Discrete(total_actions)

	def _get_observation(self):
		# One-hot encoding of the current round
		observations = []
		for i in range(MAX_ROUNDS):
			value = 1 if self.game.round == i + 1 else 0
			observations.append(value)
		# Resources, etc., of each player
		for player in self.game.players:
			observations += self._get_player_observations(player)
		return np.array(observations, dtype=np.int8)

	def _get_player_observations(self, player):
		swordmaster = self._from_bool(player.swordmaster)
		palace = self._from_bool(player.palace)
		observations = [
			player.spice,
			player.solari,
			player.troops_garrison,
			player.troops_deployed,
			player.influence,
			swordmaster,
			palace,
			player.agents_left,
			player.victory_points
		]
		observations += self._from_action_types(player)
		return observations

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

class EnvironmentAction:
	def __init__(self, action, action_enum, action_type, solari=0, spice=0, garrison=0, enabled=None, argument=None, expand=None, troops_produced=None, deployment_limit=None):
		self.action = action
		self.action_enum = action_enum
		self.action_type = action_type
		self.solari = solari
		self.spice = spice
		self.garrison = garrison
		self.enabled_check = enabled
		self.argument = argument
		self.expand = expand
		self.troops_produced = troops_produced
		self.deployment_limit = deployment_limit

	def argument_copy(self, argument):
		return EnvironmentAction(self.action, self.action_enum, self.action_type, solari=self.solari, spice=self.spice, enabled=self.enabled_check, argument=argument, troops_produced=self.troops_produced, deployment_limit=self.deployment_limit)

	def enabled(self, game):
		player = game.current_player
		enabled = not game.game_ended
		available = self.action_enum in game.available_actions
		enabled = enabled and available
		enabled = enabled and self.action_type in player.actions
		enabled = enabled and player.spice >= self.spice
		enabled = enabled and player.solari >= self.solari
		enabled = enabled and player.troops_garrison >= self.garrison
		enabled = enabled and (self.enabled is None or self.enabled_check())
		enabled = enabled and (self.troops_produced is None or self.deployment_limit is None or self._valid_deployment(game))
		return enabled

	def _valid_deployment(self, game):
		troops_deployed = self.argument
		if troops_deployed < 0 or troops_deployed > self.deployment_limit:
			return False
		if game.current_player.troops_garrison + self.troops_produced < troops_deployed:
			return False
		return True