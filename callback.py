from stable_baselines3.common.callbacks import BaseCallback

class TensorboardCallback(BaseCallback):
	PREFIX = "thumper"

	def __init__(self, environment, verbose=0):
		super().__init__(verbose)
		self.environment = environment
		self.victory_points = 0
		self.swordmaster_count = 0
		self.palace_count = 0
		self.games_played = 0

	def _on_step(self) -> bool:
		last_game_players = self.environment.get_last_game_players()
		if last_game_players is not None:
			player = last_game_players[self.environment.position_index]
			self.victory_points += player.victory_points
			if player.swordmaster:
				self.swordmaster_count += 1
			if player.palace:
				self.palace_count += 1
			self.games_played += 1
			average_victory_points = self.victory_points / self.games_played
			swordmaster_percentage = self._get_percentage(self.swordmaster_count)
			palace_percentage = self._get_percentage(self.palace_count)
			self._record("victory_points", average_victory_points)
			self._record("swordmaster", swordmaster_percentage)
			self._record("palace", palace_percentage)
		return True

	def _record(self, key, value):
		full_key = f"{TensorboardCallback.PREFIX}/{key}"
		self.logger.record(full_key, value)

	def _get_percentage(self, count):
		ratio = count / self.games_played
		percentage = round(ratio * 100, 1)
		return percentage