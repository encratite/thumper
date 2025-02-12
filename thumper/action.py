class EnvironmentAction:
	def __init__(self, action, action_type, action_enum, solari=0, spice=0, garrison=0, enabled=None, enabled_argument=False, argument=None, expand=None, troops_produced=None, deployment_limit=None):
		self.action = action
		self.action_type = action_type
		self.action_enum = action_enum
		self.solari = solari
		self.spice = spice
		self.garrison = garrison
		self.enabled_check = enabled
		self.enabled_argument = enabled_argument
		self.argument = argument
		self.expand = expand
		self.troops_produced = troops_produced
		self.deployment_limit = deployment_limit

	def argument_copy(self, argument):
		return EnvironmentAction(
			self.action,
			self.action_type,
			self.action_enum,
			solari=self.solari,
			spice=self.spice,
			enabled=self.enabled_check,
			enabled_argument=self.enabled_argument,
			argument=argument,
			troops_produced=self.troops_produced,
			deployment_limit=self.deployment_limit
		)

	def enabled(self, game):
		player = game.current_player
		enabled = not game.game_ended
		enabled = enabled and game.current_player.agents_left > 0
		enabled = enabled and (self.action_enum is None or self.action_enum in game.available_actions)
		enabled = enabled and (self.action_type is None or self.action_type in player.actions)
		enabled = enabled and player.spice >= self.spice
		enabled = enabled and player.solari >= self.solari
		enabled = enabled and player.troops_garrison >= self.garrison
		if self.enabled_argument:
			enabled = enabled and (self.enabled_check is None or self.enabled_check(self.argument))
		else:
			enabled = enabled and (self.enabled_check is None or self.enabled_check())
		enabled = enabled and (self.troops_produced is None or self.deployment_limit is None or self._valid_deployment(game))
		return enabled

	def perform(self, game):
		assert self.enabled(game)
		if self.argument is None:
			self.action()
		else:
			self.action(self.argument)

	def _valid_deployment(self, game):
		troops_deployed = self.argument
		if troops_deployed < 0 or troops_deployed > self.deployment_limit:
			return False
		if game.current_player.troops_garrison + self.troops_produced < troops_deployed:
			return False
		return True