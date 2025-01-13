import random
from constants import *

class ThumperPlayer:
	def __init__(self):
		self.spice = 0
		self.solari = 0
		self.troops_garrison = INITIAL_TROOPS
		self.troops_deployed = 0
		self.influence = 0
		self.third_agent = False
		self.palace = False
		self.agents_left = INITIAL_AGENTS
		self.victory_points = 0
		self.reset()

	def reset(self):
		actions = [
			ActionType.ECONOMIC,
			ActionType.MILITARY,
			ActionType.POLITICAL
		]
		self.agents_left = 3 if self.third_agent else 2
		self.troops_deployed = 0
		self.actions = random.choices(actions, k=4)

	def apply_reward(self, reward):
		self.victory_points += reward.victory_points
		self.influence += reward.influence
		self.spice = reward.spice
		self.solari = reward.solari