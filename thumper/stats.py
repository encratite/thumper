from typing import Final
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from stable_baselines3.common.logger import Logger
from .constants import Action
from .player import ThumperPlayer
from .env import raw_env

class ThumperStats:
	PREFIX: Final[str] = "thumper"

	logger: Logger | None
	_victory_points: int
	_victory_points_swordmaster: int
	_victory_points_no_swordmaster: int
	_swordmaster_count: int
	_palace_count: int
	_holtzman_shield_count: int
	_spice_harvested: int
	_solari_earned: int
	_games_played: int
	_action_counts: dict[Action | None, int]
	_action_count: int
	_action_plot_frequency: int

	def __init__(self, action_plot_frequency=250):
		self.logger = None
		self._victory_points = 0
		self._victory_points_swordmaster = 0
		self._victory_points_no_swordmaster = 0
		self._swordmaster_count = 0
		self._palace_count = 0
		self._holtzman_shield_count = 0
		self._spice_harvested = 0
		self._solari_earned = 0
		self._games_played = 0
		self._action_counts = {}
		for action in Action:
			self._action_counts[action] = 0
		self._action_counts[None] = 0
		self._action_count = 0
		self._action_plot_frequency = action_plot_frequency

	def on_step(self, env: raw_env, index: int) -> None:
		self._action_counts[env.last_action] += 1
		self._action_count += 1
		last_game_players = env.get_last_game_players()
		if last_game_players is not None:
			player = last_game_players[index]
			self._on_game_end(player)
			if self._games_played % self._action_plot_frequency == 0:
				self._render_action_plot()

	def _on_game_end(self, player: ThumperPlayer) -> None:
		self._victory_points += player.victory_points
		if player.swordmaster:
			self._swordmaster_count += 1
			self._victory_points_swordmaster += player.victory_points
		else:
			self._victory_points_no_swordmaster += player.victory_points
		if player.palace:
			self._palace_count += 1
		if player.holtzman_shield:
			self._holtzman_shield_count += 1
		self._spice_harvested += player.spice_harvested
		self._solari_earned += player.solari_earned
		self._games_played += 1
		average_victory_points = self._victory_points / self._games_played
		average_victory_points_swordmaster = self._get_ratio(self._victory_points_swordmaster, self._swordmaster_count)
		average_victory_points_no_swordmaster = self._get_ratio(self._victory_points_no_swordmaster, self._games_played - self._swordmaster_count)
		swordmaster_percentage = self._get_percentage(self._swordmaster_count, self._games_played)
		palace_percentage = self._get_percentage(self._palace_count, self._games_played)
		holtzman_shield_percentage = self._get_percentage(self._holtzman_shield_count, self._games_played)
		spice_harvested = self._get_ratio(self._spice_harvested, self._games_played)
		solari_earned = self._get_ratio(self._solari_earned, self._games_played)
		self._record("victory_points", average_victory_points)
		self._record("victory_points_swordmaster", average_victory_points_swordmaster)
		self._record("victory_points_no_swordmaster", average_victory_points_no_swordmaster)
		self._record("swordmaster", swordmaster_percentage)
		self._record("palace", palace_percentage)
		self._record("holtzman_shield", holtzman_shield_percentage)
		self._record("spice", spice_harvested)
		self._record("solari", solari_earned)

	def _render_action_plot(self) -> None:
		assert self.logger is not None
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
			percentage = self._get_ratio(self._action_counts[action], self._action_count, 3)
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
		plt.close()

	def _record(self, key, value):
		assert self.logger is not None
		if value is None:
			return
		full_key = f"{self.PREFIX}/{key}"
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