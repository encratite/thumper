import random
from constants import *

class ThumperPlayer:
	def __init__(self):
		self.spice = 0
		self.solari = 0
		self.troops_garrison = INITIAL_TROOPS
		self.troops_deployed = 0
		self.influence = 0
		self.swordmaster = False
		self.palace = False
		self.holtzman_shield = False
		self.agents_left = INITIAL_AGENTS
		self.victory_points = 0
		self.conflict_victory_points = 0
		self.previous_victory_points = 0
		self.turns = 0
		self.spice_harvested = 0
		self.solari_earned = 0
		self.reset()

	def reset(self):
		self.agents_left = 3 if self.swordmaster else 2
		self.troops_deployed = 0
		action_type_count = ACTION_TYPES
		if self.swordmaster:
			action_type_count += 1
		self.actions = random.choices(list(ActionType), k=action_type_count)

	def apply_reward(self, reward):
		self.conflict_victory_points += reward.victory_points
		self.influence += reward.influence
		self.spice = reward.spice
		self.solari = reward.solari

	def update_victory_points(self):
		self.previous_victory_points = self.victory_points

	def take_turn(self):
		self.agents_left -= 1
		self.turns += 1

	def gain_spice(self, amount):
		self.spice += amount
		self.spice_harvested += amount

	def gain_solari(self, amount):
		self.solari += amount
		self.solari_earned += amount

	def add_action_type(self):
		action_type = random.choice(list(ActionType))
		self.actions.append(action_type)