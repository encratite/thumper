from constants import *
from player import ThumperPlayer
from error import ThumperError
from conflict import ConflictReward

class ThumperGame:
	def __init__(self):
		self.players = [ThumperPlayer() for _ in range(PLAYER_COUNT)]
		# The current round (1 - 10)
		self.round = 1
		# The player who was the first player in the current round, as an index into players
		self.first_player_index = 0
		# The player whose current turn it is, as an index into players
		self.current_player_index = 0
		self.current_player = self.players[self.current_player_index]
		self.spice_silo = 1
		self.game_ended = False
		self._reset_available_actions()
		self._set_conflict_rewards()

	def construct_palace(self):
		self._check_game_ended()
		if self.current_player.palace:
			raise ThumperError("Player has already constructed their palace")
		self._perform_action(ActionType.ECONOMIC, Action.CONSTRUCT_PALACE, spice=6)
		self.current_player.palace = True
		self._next_turn()

	def harvester(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.HARVESTER)
		self.current_player.spice += 3
		self._next_turn()

	def refinery(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.REFINERY)
		self.current_player.spice += 2
		self.current_player.solari += 1
		self._next_turn()

	def spice_silo(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.SPICE_SILO)
		self.current_player.spice += self.spice_silo
		self._next_turn()

	def sell_melange(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.SELL_MELANGE, spice=3)
		self.current_player.solari += 8
		self._next_turn()

	def secure_contract(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.SECURE_CONTRACT)
		self.current_player.solari += 3
		self._next_turn()

	# target is the ID of the target player (1 - 4)
	def stone_burner(self, target):
		self._check_game_ended()
		target_index = target - 1
		if target < 1 or target > PLAYER_COUNT or target_index == self.current_player_index:
			raise ThumperError("Invalid target player index")
		target_player = self.players[target_index]
		if target_player.troops_garrison == 0:
			raise ThumperError("Stone Burner can only be used against players that have troops in their garrison")
		self._perform_action(ActionType.MILITARY, Action.STONE_BURNER, spice=4)
		target_player.troops_garrison = max(target_player.troops_garrison, 0)
		self.current_player.influence -= 1
		self._next_turn()

	def hire_mercenaries(self, troops_deployed):
		self._check_game_ended()
		troops_produced = 2
		deployment_limit = 3
		self._check_troops(troops_produced, troops_deployed, deployment_limit)
		self._perform_action(ActionType.MILITARY, Action.HIRE_MERCENARIES, solari=2)
		self._produce_and_deploy_troops(troops_produced, troops_deployed)
		self._next_turn()

	def quick_strike(self, troops_deployed):
		self._check_game_ended()
		troops_produced = 1
		deployment_limit = 2
		self._check_troops(troops_produced, troops_deployed, deployment_limit)
		self._perform_action(ActionType.MILITARY, Action.QUICK_STRIKE)
		self._produce_and_deploy_troops(troops_produced, troops_deployed)
		self._next_turn()

	def recruitment_center(self):
		self._check_game_ended()
		self._perform_action(ActionType.MILITARY, Action.RECRUITMENT_CENTER)
		self.current_player.troops_garrison += 1
		self._next_turn()

	def troop_transports(self, troops_deployed):
		self._check_game_ended()
		troops_produced = 0
		deployment_limit = 4
		self._check_garrison()
		self._check_troops(troops_produced, troops_deployed, deployment_limit)
		self._perform_action(ActionType.MILITARY, Action.TROOP_TRANSPORTS)
		self._deploy_troops(troops_deployed)
		self._next_turn()

	def recruit_agent(self):
		self._check_game_ended()
		if self.current_player.third_agent:
			raise ThumperError("Player already recruited their third agent")
		self._perform_action(ActionType.POLITICAL, Action.RECRUIT_AGENT)
		self.current_player.third_agent = True
		self.current_player.agents_left += 1
		self._next_turn()

	def sardaukar(self):
		self._check_game_ended()
		self._perform_action(ActionType.POLITICAL, Action.SARDAUKAR, spice=4)
		self.current_player.influence += 1
		self.current_player.troops_garrison += 3
		self._next_turn()

	def audience_with_emperor(self):
		self._check_game_ended()
		self._perform_action(ActionType.POLITICAL, Action.AUDIENCE_WITH_EMPEROR, spice=3)
		self.current_player.influence += 2
		self._next_turn()

	def mobilization(self, troops_deployed):
		self._check_game_ended()
		troops_produced = 0
		deployment_limit = 5
		self._check_garrison()
		self._check_troops(troops_produced, troops_deployed, deployment_limit)
		self._perform_action(ActionType.POLITICAL, Action.MOBILIZATION, solari=2)
		self._deploy_troops(troops_deployed)
		self._next_turn()

	def seek_allies(self):
		self._check_game_ended()
		self._perform_action(ActionType.POLITICAL, Action.SEEK_ALLIES)
		self.current_player.influence += 1
		self._next_turn()

	# action_index is the 1-based index into the player's remaining actions
	# action_type is the desired action to change it to
	def political_maneuvering(self, action_index, action_type):
		self._check_game_ended()
		actions = self.current_player.actions
		if action_index < 1 or action_index > len(actions):
			raise ThumperError("Invalid action index")
		if type(action_type) is not Action:
			raise ThumperError("Action type is not an action type enum")
		self._perform_action(ActionType.POLITICAL, Action.POLITICAL_MANEUVERING)
		actions[action_index - 1] = action_type
		self._next_turn()

	def _reset_available_actions(self):
		self.available_actions = list(Action)

	def _perform_action(self, action_type, action, spice=0, solari=0):
		if self.game_ended:
			raise ThumperError("Unable to perform action, the game has already ended")
		if action_type not in self.current_player.actions:
			raise ThumperError(f"Action \"{ActionType(action_type).name}\" is not available for this player")
		elif action not in self.available_actions:
			raise ThumperError(f"Action \"{Action(action).name}\" is not available anymore")
		if self.current_player.spice < spice:
			raise ThumperError(f"Player has only {self.current_player.spice} spice which is not enough to perform this action")
		if self.current_player.solari < solari:
			raise ThumperError(f"Player has only {self.current_player.solari} solari which is not enough to perform this action")
		self.current_player.actions.remove(action_type)
		self.available_actions.remove(action)
		self.current_player.spice -= spice
		self.current_player.solari -= solari

	def _check_game_ended(self):
		if self.game_ended:
			raise ThumperError("Tried to perform an action after the game had already ended")

	def _check_garrison(self):
		if self.current_player.troops_garrison < 1:
			raise ThumperError("Player must have at least one troop in garrison in order to use troop transports")

	def _check_troops(self, troops_produced, troops_deployed, deployment_limit):
		if troops_deployed < 0 or troops_deployed > deployment_limit:
			raise ThumperError("Invalid number of troops specified")
		if self.current_player.troops_garrison + troops_produced < troops_deployed:
			raise ThumperError("Not enough troops available")

	def _produce_and_deploy_troops(self, troops_produced, troops_deployed):
		self.current_player.troops_garrison += troops_produced
		self._deploy_troops(troops_deployed)

	def _deploy_troops(self, troops_deployed):
		if self.current_player.troops_garrison < troops_deployed:
			raise ThumperError("Not enough troops available")
		self.current_player.troops_garrison -= troops_deployed
		self.current_player.troops_deployed += troops_deployed

	def _next_turn(self):
		if self.current_player.agents_left <= 0:
			raise ThumperError("Performed an action even though the player had no actions left")
		self.current_player.agents_left -= 1
		for i in range(PLAYER_COUNT):
			player_index = (self.current_player_index + 1 + i) % PLAYER_COUNT
			player = self.players[player_index]
			if player.agents_left > 0:
				# There is still a player who has an agent left
				self.current_player = player
				self.current_player_index = player_index
				return
		# There are no players with any agents left, resolve the conflict
		self._resolve_conflict()
		if self.round < MAX_ROUNDS:
			self.round += 1
			self.first_player_index = (self.first_player_index + 1) % PLAYER_COUNT
			self.current_player_index = self.first_player_index
			self.current_player = self.players[self.current_player_index]
			if Action.SPICE_SILO in self.available_actions:
				self.spice_silo = min(self.spice_silo + 1, MAX_SPICE_SILO)
			else:
				self.spice_silo = 1
			self._reset_available_actions()
			for player in self.players:
				player.reset()
		else:
			self.game_ended = True

	def _resolve_conflict(self):
		conflict_rewards = self.conflict_rewards[self.round - 1]
		conflict_players = filter(lambda p: p.troops_deployed > 0, self.players)
		reward_groups = {}
		for player in conflict_players:
			key = player.troops_deployed
			if key in reward_groups:
				reward_groups[key].append(player)
			else:
				reward_groups[key] = [player]
		reward_group_keys = sorted(reward_groups.keys(), reverse=True)
		for key in reward_group_keys:
			if len(conflict_rewards) == 0:
				# There are no conflict rewards left, abort
				break
			reward_group = reward_groups[key]
			if len(reward_group) == 1:
				# A single player won the reward
				winner = reward_group[0]
				reward = conflict_rewards[0]
				winner.apply_reward(reward)
				conflict_rewards = conflict_rewards[1:]
			else:
				# Multiple players tied for the reward, so their reward level drops by one
				conflict_rewards = conflict_rewards[1:]
				if len(conflict_rewards) > 0:
					# Distribute the rewards among all players who tied
					reward = conflict_rewards[0]
					for player in reward_group:
						player.apply_reward(reward)

	def _set_conflict_rewards(self):
		rewards = []
		# Round 1
		rewards.append([
			ConflictReward(0, 1, 0, 2),
			ConflictReward(0, 0, 0, 3),
			ConflictReward(0, 0, 0, 2)
		])
		# Round 2
		rewards.append([
			ConflictReward(1, 0, 0, 0),
			ConflictReward(0, 0, 1, 2),
			ConflictReward(0, 0, 1, 0)
		])
		# Round 3
		rewards.append([
			ConflictReward(0, 0, 0, 6),
			ConflictReward(0, 0, 0, 4),
			ConflictReward(0, 0, 0, 2)
		])
		# Round 4
		rewards.append([
			ConflictReward(1, 0, 0, 0),
			ConflictReward(0, 0, 2, 0),
			ConflictReward(0, 0, 0, 1)
		])
		# Round 5
		rewards.append([
			ConflictReward(0, 2, 0, 0),
			ConflictReward(0, 0, 2, 0),
			ConflictReward(0, 0, 1, 0)
		])
		# Round 6
		rewards.append([
			ConflictReward(1, 0, 0, 0),
			ConflictReward(0, 0, 2, 0),
			ConflictReward(0, 0, 1, 0)
		])
		# Round 7
		rewards.append([
			ConflictReward(2, 0, 0, 0),
			ConflictReward(0, 0, 5, 0),
			ConflictReward(0, 0, 3, 0)
		])
		# Round 8
		rewards.append([
			ConflictReward(2, 0, 0, 0),
			ConflictReward(1, 0, 0, 0),
			ConflictReward(0, 0, 3, 0)
		])
		self.conflict_rewards = rewards