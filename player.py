import random
from constants import *
from error import ThumperError

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
		self.victory_points = None
		self.roll_actions()

	def roll_actions(self):
		actions = [
			ActionType.ECONOMIC,
			ActionType.MILITARY,
			ActionType.POLITICAL
		]
		self.actions = random.choices(actions, k=4)