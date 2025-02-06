import random
from constants import *
from player import ThumperPlayer
from error import ThumperError
from conflict import Conflict, ConflictReward

class ThumperGame:
	PRINT_END_OF_GAME_STATS = False

	def __init__(self):
		# Add placeholders to make PyCharm stop whining about prop
		self.players = None
		self.round = None
		self.first_player_index = None
		self.current_player_index = None
		self.current_player = None
		self.spice_in_silo = None
		self.game_ended = None
		self.reset()

	def reset(self):
		self.players = [ThumperPlayer() for _ in range(PLAYER_COUNT)]
		# The current round (1 - 8)
		self.round = 1
		# The player who was the first player in the current round, as an index into players
		self.first_player_index = 0
		# The player whose current turn it is, as an index into players
		self.current_player_index = 0
		self.current_player = self.players[self.current_player_index]
		self.spice_in_silo = 1
		self.game_ended = False
		self._reset_available_actions()
		self._set_conflict_rewards()

	def construct_palace(self):
		self._check_game_ended()
		if self.current_player.palace:
			raise ThumperError("Player has already constructed their palace")
		self._perform_action(ActionType.ECONOMIC, Action.CONSTRUCT_PALACE, solari=Cost.CONSTRUCT_PALACE)
		self.current_player.palace = True
		self._next_turn()

	def harvester(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.HARVESTER)
		self.current_player.gain_spice(3)
		self._next_turn()

	def refinery(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.REFINERY)
		self.current_player.gain_spice(2)
		self.current_player.gain_solari(1)
		self._next_turn()

	def spice_silo(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.SPICE_SILO)
		self.current_player.gain_spice(self.spice_in_silo)
		self._next_turn()

	def sell_melange(self, amount):
		self._check_game_ended()
		match amount:
			case 1:
				solari = 3
			case 2:
				solari = 6
			case 3:
				solari = 8
			case _:
				raise ThumperError("Invalid amount of spice specified")
		self._perform_action(ActionType.ECONOMIC, Action.SELL_MELANGE, spice=amount)
		self.current_player.gain_solari(solari)
		self._next_turn()

	def secure_contract(self):
		self._check_game_ended()
		self._perform_action(ActionType.ECONOMIC, Action.SECURE_CONTRACT)
		self.current_player.gain_solari(3)
		self._next_turn()

	def holtzman_shield(self):
		self._check_game_ended()
		if self.current_player.holtzman_shield:
			raise ThumperError("Player has already purchased Holtzman Shield upgrade")
		self._perform_action(ActionType.MILITARY, Action.HOLTZMAN_SHIELD, spice=Cost.HOLTZMAN_SHIELD)
		self.current_player.holtzman_shield = True
		self.current_player.troops_garrison += 1
		self._next_turn()

	# target is the ID of the target player (1 - 4)
	def stone_burner(self, target):
		self._check_game_ended()
		target_index = target - 1
		if target < 1 or target > PLAYER_COUNT or target_index == self.current_player_index:
			raise ThumperError("Invalid target player index")
		target_player = self.players[target_index]
		if target_player.troops_garrison == 0 and target_player.troops_deployed == 0:
			raise ThumperError("Stone Burner can only be used against players that have at least one troop")
		self._perform_action(ActionType.MILITARY, Action.STONE_BURNER, spice=Cost.STONE_BURNER)
		troops_to_kill = 3
		while troops_to_kill > 0 and target_player.troops_deployed > 0:
			target_player.troops_deployed -= 1
			troops_to_kill -= 1
		while troops_to_kill > 0 and target_player.troops_garrison > 0:
			target_player.troops_garrison -= 1
			troops_to_kill -= 1
		self.current_player.influence -= 1
		self._next_turn()

	def hire_mercenaries(self, troops_deployed):
		self._check_game_ended()
		self._check_troops(HIRE_MERCENARIES_TROOPS_PRODUCED, troops_deployed, HIRE_MERCENARIES_DEPLOYMENT_LIMIT)
		self._perform_action(ActionType.MILITARY, Action.HIRE_MERCENARIES, solari=Cost.HIRE_MERCENARIES)
		self._produce_and_deploy_troops(HIRE_MERCENARIES_TROOPS_PRODUCED, troops_deployed)
		self._next_turn()

	def quick_strike(self, troops_deployed):
		self._check_game_ended()
		self._check_troops(QUICK_STRIKE_TROOPS_PRODUCED, troops_deployed, QUICK_STRIKE_DEPLOYMENT_LIMIT)
		self._perform_action(ActionType.MILITARY, Action.QUICK_STRIKE)
		self._produce_and_deploy_troops(QUICK_STRIKE_TROOPS_PRODUCED, troops_deployed)
		self._next_turn()

	def recruitment_center(self):
		self._check_game_ended()
		self._perform_action(ActionType.MILITARY, Action.RECRUITMENT_CENTER)
		self.current_player.troops_garrison += 1
		self._next_turn()

	def troop_transports(self, troops_deployed):
		self._check_game_ended()
		self._check_garrison()
		self._check_troops(TROOP_TRANSPORTS_TROOPS_PRODUCED, troops_deployed, TROOP_TRANSPORTS_DEPLOYMENT_LIMIT)
		self._perform_action(ActionType.MILITARY, Action.TROOP_TRANSPORTS)
		self._deploy_troops(troops_deployed)
		self._next_turn()

	def loot_villages(self):
		self._check_game_ended()
		self._perform_action(ActionType.MILITARY, Action.LOOT_VILLAGES)
		self.current_player.gain_spice(1)
		self.current_player.gain_solari(4)
		self.current_player.influence -= 1
		self._next_turn()

	def swordmaster(self):
		self._check_game_ended()
		if self.current_player.swordmaster:
			raise ThumperError("Player already recruited their swordmaster")
		self._perform_action(ActionType.POLITICAL, Action.SWORDMASTER)
		self.current_player.swordmaster = True
		self.current_player.agents_left += 1
		self.current_player.add_action_type()
		self._next_turn()

	def sardaukar(self):
		self._check_game_ended()
		self._perform_action(ActionType.POLITICAL, Action.SARDAUKAR, spice=Cost.SARDAUKAR)
		self.current_player.influence += 1
		self.current_player.troops_garrison += 4
		self._next_turn()

	def audience_with_emperor(self):
		self._check_game_ended()
		self._perform_action(ActionType.POLITICAL, Action.AUDIENCE_WITH_EMPEROR, spice=Cost.AUDIENCE_WITH_EMPEROR)
		self.current_player.influence += 2
		self._next_turn()

	def mobilization(self, troops_deployed):
		self._check_game_ended()
		self._check_garrison()
		self._check_troops(MOBILIZATION_TROOPS_PRODUCED, troops_deployed, MOBILIZATION_DEPLOYMENT_LIMIT)
		self._perform_action(ActionType.POLITICAL, Action.MOBILIZATION, solari=Cost.MOBILIZATION)
		self.current_player.influence += 1
		self._deploy_troops(troops_deployed)
		self._next_turn()

	def seek_allies(self):
		self._check_game_ended()
		self._perform_action(ActionType.POLITICAL, Action.SEEK_ALLIES, solari=Cost.SEEK_ALLIES)
		self.current_player.influence += 1
		self._next_turn()

	# action_type is the desired action type to add
	def political_maneuvering(self, action_type):
		self._check_game_ended()
		actions = self.current_player.actions
		if type(action_type) is not ActionType:
			raise ThumperError("Action type is not an action type enum")
		self._perform_action(ActionType.POLITICAL, Action.POLITICAL_MANEUVERING)
		self.current_player.gain_solari(1)
		actions.append(action_type)
		self._next_turn()

	def pass_turn(self):
		self._check_game_ended()
		self._next_turn()

	def construct_palace_enabled(self):
		return not self.current_player.palace

	def holtzman_shield_enabled(self):
		return not self.current_player.holtzman_shield

	def stone_burner_enabled(self, target):
		player = self.players[target - 1]
		return player is not self.current_player and player.troops_garrison > 0

	def stone_burner_enabled_no_target(self):
		for i in range(PLAYER_COUNT):
			if i == self.current_player_index:
				continue
			target = i + 1
			if self.stone_burner_enabled(target):
				return True
		return False

	def has_garrison(self):
		return self.current_player.troops_garrison > 0

	def swordmaster_enabled(self):
		return not self.current_player.swordmaster

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
		self.current_player.take_turn()
		for i in range(PLAYER_COUNT):
			player_index = (self.current_player_index + 1 + i) % PLAYER_COUNT
			player = self.players[player_index]
			if player.agents_left > 0:
				# There is still a player who has an agent left
				self.current_player = player
				self.current_player_index = player_index
				self._update_victory_points()
				return
		# There are no players with any agents left, resolve the conflict
		self._resolve_conflict()
		if self.round < MAX_ROUNDS:
			self.round += 1
			self.first_player_index = (self.first_player_index + 1) % PLAYER_COUNT
			self.current_player_index = self.first_player_index
			self.current_player = self.players[self.current_player_index]
			if Action.SPICE_SILO in self.available_actions:
				self.spice_in_silo = min(self.spice_in_silo + 1, MAX_SPICE_SILO)
			else:
				self.spice_in_silo = 1
			self._reset_available_actions()
			for player in self.players:
				player.reset()
		else:
			self.game_ended = True
		self._update_victory_points()
		if self.game_ended:
			self._on_game_end()

	def _on_game_end(self):
		if ThumperGame.PRINT_END_OF_GAME_STATS:
			print("Game ended:")
			for player in self.players:
				print(f"Victory points: {player.victory_points} ({player.conflict_victory_points} from conflicts), influence: {player.influence}, spice: {player.spice}, solari: {player.solari}, swordmaster: {player.swordmaster}, palace: {player.palace}, turns taken: {player.turns}")

	def _resolve_conflict(self):
		conflict = self.conflicts[self.round - 1]
		conflict_rewards = conflict.rewards
		conflict_players = filter(lambda p: p.troops_deployed > 0, self.players)
		reward_groups = {}
		for player in conflict_players:
			key = player.troops_deployed
			if player.holtzman_shield:
				key += 1
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
		rewards1 = [
			ConflictReward(0, 1, 0, 2),
			ConflictReward(0, 0, 0, 3),
			ConflictReward(0, 0, 0, 2)
		]
		rewards2 = [
			ConflictReward(1, 0, 0, 0),
			ConflictReward(0, 0, 1, 2),
			ConflictReward(0, 0, 1, 0)
		]
		rewards3 = [
			ConflictReward(0, 0, 0, 6),
			ConflictReward(0, 0, 0, 4),
			ConflictReward(0, 0, 0, 2)
		]
		rewards4 = [
			ConflictReward(1, 0, 0, 0),
			ConflictReward(0, 0, 2, 0),
			ConflictReward(0, 0, 0, 1)
		]
		rewards5 = [
			ConflictReward(0, 2, 0, 0),
			ConflictReward(0, 0, 2, 0),
			ConflictReward(0, 0, 1, 0)
		]
		rewards6 = [
			ConflictReward(1, 0, 0, 0),
			ConflictReward(0, 0, 2, 0),
			ConflictReward(0, 0, 1, 0)
		]
		rewards7 = [
			ConflictReward(2, 0, 0, 0),
			ConflictReward(0, 0, 5, 0),
			ConflictReward(0, 0, 3, 0)
		]
		rewards8 = [
			ConflictReward(0, 2, 3, 0),
			ConflictReward(0, 1, 5, 0),
			ConflictReward(0, 0, 3, 0)
		]
		rewards9 = [
			ConflictReward(2, 0, 0, 0),
			ConflictReward(1, 0, 0, 0),
			ConflictReward(0, 0, 3, 0)
		]
		level1 = [
			Conflict(1, rewards1)
		]
		level2 = [
			Conflict(2, rewards2),
			Conflict(3, rewards3),
			Conflict(4, rewards4),
			Conflict(5, rewards5),
			Conflict(6, rewards6)
		]
		level3 = [
			Conflict(7, rewards7),
			Conflict(8, rewards8),
			Conflict(9, rewards9)
		]
		levels = [
			level1,
			level2,
			level3
		]
		self.conflicts = []
		for level in levels:
			random.shuffle(level)
			self.conflicts += level
		assert len(self.conflicts) == MAX_ROUNDS

	def _update_victory_points(self):
		for player in self.players:
			victory_points = player.conflict_victory_points
			if player.influence >= 2:
				victory_points += 1
			if player.influence >= 4:
				victory_points += 1
			if player.palace:
				victory_points += 1
			player.victory_points = victory_points
		if self.game_ended:
			self._add_influence_victory_points()

	def _add_influence_victory_points(self):
		players = sorted(self.players, key=lambda p: p.influence, reverse=True)
		player1 = players[0]
		player2 = players[1]
		player3 = players[2]
		min_influence = 6
		if player1.influence > player2.influence:
			if player1.influence >= min_influence:
				player1.victory_points += 2
			if player2.influence >= min_influence and player2.influence > player3.influence:
				player2.victory_points += 1
		elif player1.influence >= min_influence and player2.influence >= min_influence:
			player1.victory_points += 1
			player2.victory_points += 1