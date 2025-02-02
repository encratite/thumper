import os
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import Figure
from constants import Action

class TensorboardCallback(BaseCallback):
	PREFIX = "thumper"

	def __init__(self, environment, verbose=0):
		super().__init__(verbose)
		self.environment = environment
		self.victory_points = 0
		self.victory_points_swordmaster = 0
		self.victory_points_no_swordmaster = 0
		self.swordmaster_count = 0
		self.palace_count = 0
		self.holtzman_shield_count = 0
		self.spice_harvested = 0
		self.solari_earned = 0
		self.games_played = 0
		self.action_counts = {}
		for action in Action:
			self.action_counts[action] = 0
		self.action_counts[None] = 0
		self.action_count = 0

	def _on_step(self) -> bool:
		last_game_players = self.environment.get_last_game_players()
		if last_game_players is not None:
			self._on_game_end(last_game_players)
		self.action_counts[self.environment.last_action] += 1
		self.action_count += 1
		return True

	def _on_training_end(self):
		labels = [
			# Economic Actions
			"Construct Palace",
			"Harvester",
			"Refinery",
			"Spice Silo",
			"Sell Melange",
			"Secure Contract",
			# Military actions
			"Holtzman Shield",
			"Stone Burner",
			"Hire Mercenaries",
			"Quick Strike",
			"Recruitment Center",
			"Troop Transports",
			"Loot Villages",
			# Political actions
			"Swordmaster",
			"Sardaukar",
			"Audience with Emperor",
			"Mobilization",
			"Seek Allies",
			"Political Maneuvering",
			# Other
			"Pass"
		]
		values = []
		for action in list(Action) + [None]:
			percentage = self._get_ratio(self.action_counts[action], self.action_count, 3)
			values.append(percentage)
		figure, ax = plt.subplots()
		ax.bar(labels, values)
		ax.set_ylabel("Frequency")
		ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: "{:.1%}".format(y)))
		ax.set_title("Action Frequency")
		plt.xticks(rotation="vertical")
		plt.tight_layout()
		path = os.path.join(self.logger.dir, "action_frequency.png")
		plt.savefig(path, dpi=150)
		# plt.show()
		plt.close()

	def _on_game_end(self, last_game_players):
		player = last_game_players[self.environment.position_index]
		self.victory_points += player.victory_points
		if player.swordmaster:
			self.swordmaster_count += 1
			self.victory_points_swordmaster += player.victory_points
		else:
			self.victory_points_no_swordmaster += player.victory_points
		if player.palace:
			self.palace_count += 1
		if player.holtzman_shield:
			self.holtzman_shield_count += 1
		self.spice_harvested += player.spice_harvested
		self.solari_earned += player.solari_earned
		self.games_played += 1
		average_victory_points = self.victory_points / self.games_played
		average_victory_points_swordmaster = self._get_ratio(self.victory_points_swordmaster, self.swordmaster_count)
		average_victory_points_no_swordmaster = self._get_ratio(self.victory_points_no_swordmaster, self.games_played - self.swordmaster_count)
		swordmaster_percentage = self._get_percentage(self.swordmaster_count, self.games_played)
		palace_percentage = self._get_percentage(self.palace_count, self.games_played)
		holtzman_shield_percentage = self._get_percentage(self.holtzman_shield_count, self.games_played)
		spice_harvested = self._get_ratio(self.spice_harvested, self.games_played)
		solari_earned = self._get_ratio(self.solari_earned, self.games_played)
		self._record("victory_points", average_victory_points)
		self._record("victory_points_swordmaster", average_victory_points_swordmaster)
		self._record("victory_points_no_swordmaster", average_victory_points_no_swordmaster)
		self._record("swordmaster", swordmaster_percentage)
		self._record("palace", palace_percentage)
		self._record("holtzman_shield", holtzman_shield_percentage)
		self._record("spice", spice_harvested)
		self._record("solari", solari_earned)

	def _record(self, key, value):
		if value is None:
			return
		full_key = f"{TensorboardCallback.PREFIX}/{key}"
		self.logger.record(full_key, value)

	def _get_percentage(self, numerator, denominator):
		ratio = numerator / denominator
		percentage = round(ratio * 100, 1)
		return percentage

	def _get_ratio(self, numerator, denominator, precision=2):
		if denominator == 0:
			return None
		ratio = round(numerator / denominator, precision)
		return ratio