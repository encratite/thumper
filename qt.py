from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, QPushButton)
from game import ThumperGame
from constants import Action

class ThumperQt(QWidget):
	def __init__(self):
		super().__init__()
		self.game = ThumperGame()
		self.initialize_ui()

	def initialize_ui(self):
		self.buttons = []
		self.button_row = 0
		self.button_column = 0
		self.grid = QGridLayout()
		for i in range(3):
			self.grid.setColumnMinimumWidth(i, 140)
		self.setLayout(self.grid)
		self.add_buttons()
		self.update_buttons()
		self.setWindowTitle("Thumper")
		self.show()

	def add_buttons(self):
		self.add_label("Economy:")
		self.add_button("Construct Palace", Action.CONSTRUCT_PALACE, solari=6, enabled=self.enable_construct_palace)
		self.add_button("Harvester", Action.HARVESTER)
		self.add_button("Refinery", Action.REFINERY)
		self.add_button("Spice Silo", Action.SPICE_SILO)
		self.add_button("Sell Melange", Action.SELL_MELANGE, spice=3)
		self.add_button("Secure Contract", Action.SECURE_CONTRACT)
		self.new_button_column()

		self.add_label("Military:")
		self.add_button("Stone Burner", Action.STONE_BURNER, spice=4, enabled=self.stone_burner_enabled)
		self.add_button("Hire Mercenaries", Action.HIRE_MERCENARIES, solari=2)
		self.add_button("Quick Strike", Action.QUICK_STRIKE)
		self.add_button("Recruitment Center", Action.RECRUITMENT_CENTER)
		self.add_button("Troop Transports", Action.TROOP_TRANSPORTS)
		self.add_button("Loot Villages", Action.LOOT_VILLAGES)
		self.new_button_column()

		self.add_label("Politics:")
		self.add_button("Recruit Agent", Action.RECRUIT_AGENT, solari=8, enabled=self.recruit_agent_enabled)
		self.add_button("Sardaukar", Action.SARDAUKAR, spice=4)
		self.add_button("Audience with Emperor", Action.AUDIENCE_WITH_EMPEROR, spice=3)
		self.add_button("Mobilization", Action.MOBILIZATION, solari=2)
		self.add_button("Seek Allies", Action.SEEK_ALLIES)
		self.add_button("Political Maneuvering", Action.POLITICAL_MANEUVERING)

	def add_label(self, text):
		label = QLabel(text)
		self.grid.addWidget(label, self.button_row, self.button_column, alignment=Qt.AlignmentFlag.AlignCenter)
		self.button_row += 1

	def add_button(self, text, action_enum, spice=0, solari=0, enabled=None):
		button = ActionButton(text, action_enum, spice, solari, enabled)
		self.grid.addWidget(button.button, self.button_row, self.button_column)
		self.button_row += 1
		self.buttons.append(button)

	def new_button_column(self):
		self.button_row = 0
		self.button_column += 1

	def update_buttons(self):
		for button in self.buttons:
			button.update(self.game)

	def enable_construct_palace(self):
		return not self.game.current_player.palace

	def stone_burner_enabled(self):
		return any(player is not self.game.current_player and player.troops_garrison > 0 for player in self.game.players)

	def recruit_agent_enabled(self):
		return not self.game.current_player.third_agent

class ActionButton:
	def __init__(self, text, action_enum, spice, solari, enabled):
		self.button = QPushButton(text)
		self.action_enum = action_enum
		self.spice = spice
		self.solari = solari
		self.enabled = enabled

	def update(self, game):
		player = game.current_player
		enabled_callback = self.enabled is None or self.enabled()
		enabled = player.spice >= self.spice and player.solari >= self.solari and enabled_callback
		self.button.setEnabled(enabled)