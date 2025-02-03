class Conflict:
	def __init__(self, id, rewards):
		self.id = id
		self.rewards = rewards

class ConflictReward:
	def __init__(self, victory_points, influence, spice, solari):
		self.victory_points = victory_points
		self.influence = influence
		self.spice = spice
		self.solari = solari