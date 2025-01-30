import random
from tensordict import TensorDict
from torchrl.envs.common import EnvBase
from torch import tensor, uint8, int8
from torchrl.data import Composite, Categorical, OneHot, Binary, Unbounded
from game import ThumperGame
from constants import *

class ThumperEnvironment(EnvBase):
	"""
	Creates an OpenAI gym environment for the Thumper proof of concept game.
	The models are only meant to be trained for a particular position on the table.
	All other players are assumed to be controlled by other reinforcement learning models that were trained in an identical fashion.
	If no other models are provided (i.e. models = None), the environment will randomize the actions of the other players instead.
	This is initially done to bootstrap the training of all models.
	The DQN agent corresponding to the specified position (i.e. models[position]) is not used by the environment.

	Arguments:
		position: an int from 0 to PLAYER_COUNT - 1 that determines the player's position on the table
		models: a list of PLAYER_COUNT DQN agents that represent the AIs that will control the other players
	"""
	def __init__(self, position, models=None, device=None):
		super().__init__(device=device)
		self.position = position
		self.models = models
		self.game = ThumperGame()
		player_spec = Composite(
			device=device,
			economic_actions=Categorical(5, dtype=uint8, device=device),
			military_actions=Categorical(5, dtype=uint8, device=device),
			political_actions=Categorical(5, dtype=uint8, device=device),
			spice=Categorical(11, dtype=uint8, device=device),
			solari=Categorical(11, dtype=uint8, device=device),
			troops_garrison=Categorical(11, dtype=uint8, device=device),
			troops_deployed=Categorical(11, dtype=uint8, device=device),
			influence=Categorical(16, dtype=int8, device=device),
			swordmaster=Binary(1, device=device),
			palace=Binary(1, device=device),
			agents_left=Categorical(4, dtype=uint8, device=device),
			victory_points=Categorical(13, dtype=uint8, device=device),
		)
		self.full_observation_spec = Composite(
			device=device,
			round=OneHot(8, device=device),
			players=player_spec.expand(4)
		)
		self.full_state_spec = self.full_observation_spec.clone()
		self.full_reward_spec = Unbounded(shape=(1,), device=device)
		self.full_done_spec = Composite(
			done=Binary(1, device=device),
			terminated=Binary(1, device=device),
			device=device
		)
		self._initialize_actions(device)

	def _set_seed(self, seed):
		if seed is not None:
			raise NotImplementedError("This environment does not support seeds")

	def _reset(self, tensor_dict, **kwargs):
		assert tensor_dict is None
		self.game.reset()
		# The game must be reset to a state in which it is the target player's turn
		self._perform_enemy_moves()
		assert self.game.round == 1
		observation = self._get_observation()
		return observation

	def _step(self, tensor_dict):
		action = int(tensor_dict["action"])
		assert not self.game.game_ended
		assert 0 <= action < len(self.actions)
		environment_action = self.actions[action]
		victory_points_before = self._get_victory_points()
		environment_action.perform(self.game)
		self._perform_enemy_moves()
		victory_points_after = self._get_victory_points()
		reward = victory_points_after - victory_points_before
		output = self._get_observation()
		output["reward"] = reward
		output["done"] = self.game.game_ended
		output["terminated"] = self.game.game_ended
		return output

	def _initialize_actions(self, device):
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
				expand=(1, 4)
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
		total_actions = len(self.actions)
		# The action space consists of indexes into self.actions
		self.full_action_space = Categorical(total_actions, dtype=uint8, device=device)

	def _get_observation(self):
		players = [self._get_player_observation(player) for player in self.game.players]
		observation = TensorDict({
			"round": self.game.round,
			"players": players
		})
		return observation

	def _get_player_observation(self, player):
		def adjust(x):
			# For negative influence
			resource_min = -5
			resource_max = 10
			return max(min(x, resource_max), resource_min)

		action_type_counts = self._count_action_types(player)
		swordmaster = self._from_bool(player.swordmaster)
		palace = self._from_bool(player.palace)
		observation = TensorDict({
			"economic_actions": action_type_counts[ActionType.ECONOMIC],
			"military_actions": action_type_counts[ActionType.MILITARY],
			"political_actions": action_type_counts[ActionType.POLITICAL],
			"spice": adjust(player.spice),
			"solari": adjust(player.solari),
			"troops_garrison": adjust(player.troops_garrison),
			"troops_deployed": adjust(player.troops_deployed),
			"influence": adjust(player.influence),
			"swordmaster": swordmaster,
			"palace": palace,
			"agents_left": player.agents_left,
			"victory_points": player.victory_points
		})
		return observation

	def _from_bool(self, value):
		return 1 if value else 0

	def _count_action_types(self, player):
		counts = {
			ActionType.ECONOMIC: 0,
			ActionType.MILITARY: 0,
			ActionType.POLITICAL: 0
		}
		for action in player.actions:
			counts[action] += 1
		return counts

	def _perform_enemy_move(self):
		assert not self.game.game_ended
		assert self.game.current_player_index != self.position
		if self.models is not None:
			raise NotImplementedError()
		else:
			# No other DQN agents are available yet, perform a random action
			available_actions = [action for action in self.actions if action.enabled(self.game)]
			random_action = random.choice(available_actions)
			random_action.perform(self.game)

	def _perform_enemy_moves(self):
		count = 0
		while not self.game.game_ended and self.game.current_player_index != self.position:
			self._perform_enemy_move()
			count += 1

	def _get_victory_points(self):
		return self.game.players[self.position].victory_points

class EnvironmentAction:
	def __init__(self, action, action_type, action_enum, solari=0, spice=0, garrison=0, enabled=None, argument=None, expand=None, troops_produced=None, deployment_limit=None):
		self.action = action
		self.action_type = action_type
		self.action_enum = action_enum
		self.solari = solari
		self.spice = spice
		self.garrison = garrison
		self.enabled_check = enabled
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
			argument=argument,
			troops_produced=self.troops_produced,
			deployment_limit=self.deployment_limit
		)

	def enabled(self, game):
		player = game.current_player
		enabled = not game.game_ended
		# print(enabled)
		enabled = enabled and game.current_player.agents_left > 0
		# print(enabled)
		enabled = enabled and (self.action_enum is None or self.action_enum in game.available_actions)
		# print(enabled)
		# print(f"self.action_enum: {self.action_enum}")
		# print(f"game.available_actions: {game.available_actions}")
		# print(f"self.action_type: {self.action_type}")
		# print(f"player.actions: {player.actions}")
		enabled = enabled and (self.action_type is None or self.action_type in player.actions)
		# print(enabled)
		enabled = enabled and player.spice >= self.spice
		# print(enabled)
		enabled = enabled and player.solari >= self.solari
		# print(enabled)
		enabled = enabled and player.troops_garrison >= self.garrison
		# print(enabled)
		enabled = enabled and (self.enabled_check is None or self.enabled_check())
		# print(enabled)
		enabled = enabled and (self.troops_produced is None or self.deployment_limit is None or self._valid_deployment(game))
		# print(enabled)
		return enabled

	def perform(self, game):
		print(f"Attempting to perform action: {self.action}")
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