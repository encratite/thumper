from typing import Final
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from stable_baselines3.common.logger import Logger
from .constants import Action
from .player import ThumperPlayer
from .env import raw_env

class ThumperGameOutcome:
	victory_points: int
	swordmaster: bool
	palace: bool
	holtzman_shield: bool
	spice_harvested: int
	solari_earned: int
	win: bool
	action_counts: dict[Action | None, int]

	def __init__(self):
		self.victory_points = 0
		self.swordmaster = False
		self.palace = False
		self.holtzman_shield = False
		self.spice_harvested = 0
		self.solari_earned = 0
		self.win = False
		self.action_counts = {}
		for action in ThumperStats.ACTION_RANGE:
			self.action_counts[action] = 0

class ThumperStats:
	PREFIX: Final[str] = "thumper"
	GAME_LIMIT: Final[int] = 200
	ACTION_RANGE: Final[list[Action | None]] = list(Action) + [None]

	logger: Logger | None
	_game: ThumperGameOutcome
	_games: list[ThumperGameOutcome]
	_games_played: int
	_action_plot_frequency: int

	def __init__(self, action_plot_frequency=250):
		self.logger = None
		self._game = ThumperGameOutcome()
		self._games = []
		self._games_played = 0
		self._action_plot_frequency = action_plot_frequency

	def on_step(self, env: raw_env, index: int) -> None:
		self._game.action_counts[env.last_action] += 1
		last_game_players = env.get_last_game_players()
		if last_game_players is not None:
			player = last_game_players[index]
			self._on_game_end(player, last_game_players)
			if self._games_played % self._action_plot_frequency == 0:
				self._render_action_plot()

	def _on_game_end(self, player: ThumperPlayer, last_game_players: list[ThumperPlayer]) -> None:
		self._game.victory_points = player.victory_points
		self._game.swordmaster = player.swordmaster
		self._game.palace = player.palace
		self._game.holtzman_shield = player.holtzman_shield
		self._game.spice_harvested = player.spice_harvested
		self._game.solari_earned = player.solari_earned
		self._games_played += 1
		self._game.win = player is last_game_players[0]
		self._games.append(self._game)
		while len(self._games) > self.GAME_LIMIT:
			self._games.pop(0)
		self._game = ThumperGameOutcome()
		self._record_stats()

	def _record_stats(self):
		wins = 0
		victory_points = 0
		victory_points_swordmaster = 0
		victory_points_no_swordmaster = 0
		swordmaster_count = 0
		palace_count = 0
		holtzman_shield_count = 0
		spice_harvested = 0
		solari_earned = 0
		games_played = len(self._games)
		for game in self._games:
			if game.win:
				wins += 1
			victory_points += game.victory_points
			if game.swordmaster:
				swordmaster_count += 1
				victory_points_swordmaster += game.victory_points
			else:
				victory_points_no_swordmaster += game.victory_points
			if game.palace:
				palace_count += 1
			if game.holtzman_shield:
				holtzman_shield_count += 1
			spice_harvested += game.spice_harvested
			solari_earned += game.solari_earned
		win_ratio_percentage = self._get_percentage(wins, games_played)
		average_victory_points = victory_points / games_played
		average_victory_points_swordmaster = self._get_ratio(victory_points_swordmaster, swordmaster_count)
		average_victory_points_no_swordmaster = self._get_ratio(victory_points_no_swordmaster, games_played - swordmaster_count)
		swordmaster_percentage = self._get_percentage(swordmaster_count, games_played)
		palace_percentage = self._get_percentage(palace_count, games_played)
		holtzman_shield_percentage = self._get_percentage(holtzman_shield_count, games_played)
		spice_harvested = self._get_ratio(spice_harvested, games_played)
		solari_earned = self._get_ratio(solari_earned, games_played)
		self._record("win_ratio", win_ratio_percentage)
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
		action_counts = {}
		for action in self.ACTION_RANGE:
			action_counts[action] = 0
		action_count = 0
		for game in self._games:
			for action in game.action_counts:
				value = game.action_counts[action]
				action_counts[action] += value
				action_count += value
		for action in self.ACTION_RANGE:
			percentage = self._get_ratio(action_counts[action], action_count, 3)
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