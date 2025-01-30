from argparse import ArgumentError
import random

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
	The DQN agent corresponding to the specified position (i.e. models[position]) is not used by the environment.

	Arguments:
		position: an int from 0 to PLAYER_COUNT - 1 that determines the player's position on the table
		opponent_models: a list of PLAYER_COUNT DQN agents that represent the AIs that will control the other players
	"""
	def __init__(self, position, opponent_models=None):
		self.position_index = position - 1
		self.opponent_models = opponent_models
		self.game = ThumperGame()
		# Current round (1 to 8), one-hot encoded, so 0 to 1 each
		nvec = MAX_ROUNDS * [2]
		for i in range(PLAYER_COUNT):
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
				# Agents left (0 to 3)
				4,
				# Victory points (0 to 12)
				13
			]
		self.observation_space = gym.spaces.MultiDiscrete(nvec, dtype=np.int8)
		self._initialize_actions()

	def reset(self, seed=None, options=None):
		super().reset(seed=seed)
		self.game.reset()
		# The game must be reset to a state in which it is the target player's turn
		self._perform_opponent_moves()
		assert self.game.round == 1
		observation = self._get_observation()
		info = self._get_info()
		return observation, info

	def step(self, action):
		assert not self.game.game_ended
		assert 0 <= action < len(self.actions)
		environment_action = self.actions[action]
		victory_points_before = self._get_victory_points()
		environment_action.perform(self.game)
		self._perform_opponent_moves()
		victory_points_after = self._get_victory_points()
		observation = self._get_observation()
		reward = victory_points_after - victory_points_before
		terminated = self.game.game_ended
		truncated = False
		info = self._get_info()
		return observation, reward, terminated, truncated, info

	def action_masks(self):
		masks = [action.enabled(self.game) for action in self.actions]
		return masks

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
				spice=Cost.SELL_MELANGE
			),
			EnvironmentAction(
				self.game.secure_contract,
				ActionType.ECONOMIC,
				Action.SECURE_CONTRACT
			),
			EnvironmentAction(
				self.game.stone_burner,
				ActionType.MILITARY,
				Action.STONE_BURNER,
				spice=Cost.STONE_BURNER,
				enabled=self.game.stone_burner_enabled,
				enabled_argument=True,
				expand=(1, PLAYER_COUNT)
			),
			EnvironmentAction(
				self.game.hire_mercenaries,
				ActionType.MILITARY,
				Action.HIRE_MERCENARIES,
				solari=Cost.HIRE_MERCENARIES,
				troops_produced=HIRE_MERCENARIES_TROOPS_PRODUCED,
				deployment_limit=HIRE_MERCENARIES_DEPLOYMENT_LIMIT,
				expand=(0, 3)
			),
			EnvironmentAction(
				self.game.quick_strike,
				ActionType.MILITARY,
				Action.QUICK_STRIKE,
				troops_produced=QUICK_STRIKE_TROOPS_PRODUCED,
				deployment_limit=QUICK_STRIKE_DEPLOYMENT_LIMIT,
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
				troops_produced=TROOP_TRANSPORTS_TROOPS_PRODUCED,
				deployment_limit=TROOP_TRANSPORTS_DEPLOYMENT_LIMIT,
				expand=(0, 4)
			),
			EnvironmentAction(
				self.game.loot_villages,
				ActionType.MILITARY,
				Action.LOOT_VILLAGES,
				enabled=self.game.has_garrison
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
				troops_produced=MOBILIZATION_TROOPS_PRODUCED,
				deployment_limit=MOBILIZATION_DEPLOYMENT_LIMIT,
				expand=(0, 5)
			),
			EnvironmentAction(
				self.game.seek_allies,
				ActionType.POLITICAL,
				Action.SEEK_ALLIES
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
		self.action_space = gym.spaces.Discrete(total_actions)

	def _get_observation(self):
		# One-hot encoding of the current round
		observation = []
		for i in range(MAX_ROUNDS):
			value = 1 if self.game.round == i + 1 else 0
			observation.append(value)
		# Resources, etc., of each player
		for player in self.game.players:
			observation += self._get_player_observation(player)
		return np.array(observation, dtype=np.int8)

	def _get_player_observation(self, player):
		def adjust(x):
			return min(x, 10)

		def adjust_influence(x):
			return max(min(x + 5, 15), 0)

		swordmaster = self._from_bool(player.swordmaster)
		palace = self._from_bool(player.palace)
		observation = self._from_action_types(player)
		observation += [
			adjust(player.spice),
			adjust(player.solari),
			adjust(player.troops_garrison),
			adjust(player.troops_deployed),
			adjust_influence(player.influence),
			swordmaster,
			palace,
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

	def _perform_opponent_move(self):
		assert not self.game.game_ended
		assert self.game.current_player_index != self.position_index
		if self.opponent_models is not None:
			observation = self._get_observation()
			opponent_model = self.opponent_models[self.game.current_player_index]
			action_masks = self.action_masks()
			action_index, _info = opponent_model.predict(observation, deterministic=True, action_masks=action_masks)
			action = self.actions[action_index]
			action.perform(self.game)
		else:
			available_actions = [action for action in self.actions if action.enabled(self.game)]
			random_action = random.choice(available_actions)
			random_action.perform(self.game)

	def _perform_opponent_moves(self):
		count = 0
		while not self.game.game_ended and self.game.current_player_index != self.position_index:
			self._perform_opponent_move()
			count += 1

	def _get_victory_points(self):
		return self.game.players[self.position_index].victory_points

	def _get_info(self):
		info = {}
		return info

class EnvironmentAction:
	def __init__(self, action, action_type, action_enum, solari=0, spice=0, garrison=0, enabled=None, enabled_argument=False, argument=None, expand=None, troops_produced=None, deployment_limit=None):
		self.action = action
		self.action_type = action_type
		self.action_enum = action_enum
		self.solari = solari
		self.spice = spice
		self.garrison = garrison
		self.enabled_check = enabled
		self.enabled_argument = enabled_argument
		self.argument = argument
		self.expand = expand
		self.troops_produced = troops_produced
		self.deployment_limit = deployment_limit

	def argument_copy(self, argument):
		return EnvironmentAction(
			self.action,
			self.action_type,
			self.action_enum,
			solari=self.solari,
			spice=self.spice,
			enabled=self.enabled_check,
			enabled_argument=self.enabled_argument,
			argument=argument,
			troops_produced=self.troops_produced,
			deployment_limit=self.deployment_limit
		)

	def enabled(self, game):
		player = game.current_player
		enabled = not game.game_ended
		enabled = enabled and game.current_player.agents_left > 0
		enabled = enabled and (self.action_enum is None or self.action_enum in game.available_actions)
		enabled = enabled and (self.action_type is None or self.action_type in player.actions)
		enabled = enabled and player.spice >= self.spice
		enabled = enabled and player.solari >= self.solari
		enabled = enabled and player.troops_garrison >= self.garrison
		if self.enabled_argument:
			enabled = enabled and (self.enabled_check is None or self.enabled_check(self.argument))
		else:
			enabled = enabled and (self.enabled_check is None or self.enabled_check())
		enabled = enabled and (self.troops_produced is None or self.deployment_limit is None or self._valid_deployment(game))
		return enabled

	def perform(self, game):
		assert self.enabled(game)
		if self.argument is None:
			self.action()
		else:
			self.action(self.argument)

	def _valid_deployment(self, game):
		troops_deployed = self.argument
		if troops_deployed < 0 or troops_deployed > self.deployment_limit:
			return False
		if game.current_player.troops_garrison + self.troops_produced < troops_deployed:
			return False
		return True