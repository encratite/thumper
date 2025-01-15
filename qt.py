from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QInputDialog)
from game import ThumperGame
from constants import *
from table import ExpandingTableView, PlayerTableModel

class ThumperQt(QWidget):
	def __init__(self):
		super().__init__()
		self.game = ThumperGame()
		self._initialize_ui()

	def _initialize_ui(self):
		self.buttons = []
		self.button_row = 0
		self.button_column = 0
		self.grid = QGridLayout()
		for i in range(3):
			self.grid.setColumnMinimumWidth(i, 140)
		self.setLayout(self.grid)
		self._add_buttons()
		self._update_buttons()
		self._add_table()
		self.setWindowTitle("Thumper")
		self.show()

	def _add_buttons(self):
		self._add_label("Economy:")
		self._add_button("Construct Palace", Action.CONSTRUCT_PALACE, self._construct_palace, solari=Cost.CONSTRUCT_PALACE, enabled=self._enable_construct_palace)
		self._add_button("Harvester", Action.HARVESTER, self._harvester)
		self._add_button("Refinery", Action.REFINERY, self._refinery)
		self._add_button("Spice Silo", Action.SPICE_SILO, self._spice_silo)
		self._add_button("Sell Melange", Action.SELL_MELANGE, self._sell_melange, spice=Cost.SELL_MELANGE)
		self._add_button("Secure Contract", Action.SECURE_CONTRACT, self._secure_contract)
		self._new_button_column()

		self._add_label("Military:")
		self._add_button("Stone Burner", Action.STONE_BURNER, self._stone_burner, spice=Cost.STONE_BURNER, enabled=self._stone_burner_enabled)
		self._add_button("Hire Mercenaries", Action.HIRE_MERCENARIES, self._hire_mercenaries, solari=Cost.HIRE_MERCENARIES)
		self._add_button("Quick Strike", Action.QUICK_STRIKE, self._quick_strike)
		self._add_button("Recruitment Center", Action.RECRUITMENT_CENTER, self._recruitment_center)
		self._add_button("Troop Transports", Action.TROOP_TRANSPORTS, self._troop_transports)
		self._add_button("Loot Villages", Action.LOOT_VILLAGES, self._loot_villages)
		self._new_button_column()

		self._add_label("Politics:")
		self._add_button("Swordmaster", Action.SWORDMASTER, self._swordmaster, solari=Cost.SWORDMASTER, enabled=self._swordmaster_enabled)
		self._add_button("Sardaukar", Action.SARDAUKAR, self._sardaukar, spice=Cost.SARDAUKAR)
		self._add_button("Audience with Emperor", Action.AUDIENCE_WITH_EMPEROR, self._audience_with_emperor, spice=Cost.AUDIENCE_WITH_EMPEROR)
		self._add_button("Mobilization", Action.MOBILIZATION, self._mobilization, solari=Cost.MOBILIZATION)
		self._add_button("Seek Allies", Action.SEEK_ALLIES, self._seek_allies)
		self._add_button("Political Maneuvering", Action.POLITICAL_MANEUVERING, self._political_maneuvering)

	def _add_table(self):
		self.table = ExpandingTableView()
		self.table_model = PlayerTableModel(self.game)
		self.table.setModel(self.table_model)
		self.table.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
		vertical_header = self.table.verticalHeader()
		vertical_header.hide()
		horizontal_header = self.table.horizontalHeader()
		horizontal_header.hide()
		horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
		table_row = 1 + 6
		columns = 3
		self.grid.addWidget(self.table, table_row, 0, 1, columns)
		self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

	def _add_label(self, text):
		label = QLabel(text)
		self.grid.addWidget(label, self.button_row, self.button_column, alignment=Qt.AlignmentFlag.AlignCenter)
		self.button_row += 1

	def _add_button(self, text, action_enum, on_click, spice=0, solari=0, enabled=None):
		def on_click_with_update():
			on_click()
			self._update_buttons()
		button = ActionButton(text, action_enum, on_click_with_update, spice, solari, enabled)
		self.grid.addWidget(button.button, self.button_row, self.button_column)
		self.button_row += 1
		self.buttons.append(button)

	def _new_button_column(self):
		self.button_row = 0
		self.button_column += 1

	def _update_buttons(self):
		for button in self.buttons:
			button.update(self.game)

	def _enable_construct_palace(self):
		return not self.game.current_player.palace

	def _stone_burner_enabled(self):
		return any(player is not self.game.current_player and player.troops_garrison > 0 for player in self.game.players)

	def _swordmaster_enabled(self):
		return not self.game.current_player.swordmaster

	def _construct_palace(self):
		self.game.construct_palace()

	def _harvester(self):
		self.game.harvester()

	def _refinery(self):
		self.game.refinery()

	def _spice_silo(self):
		self.game.spice_silo()

	def _sell_melange(self):
		self.game.sell_melange()

	def _secure_contract(self):
		self.game.secure_contract()

	def _stone_burner(self):
		pass

	def _hire_mercenaries(self):
		troops = self._get_deployment_size(3)
		if troops is None:
			return
		self.game.hire_mercenaries(troops)

	def _quick_strike(self):
		troops = self._get_deployment_size(2)
		if troops is None:
			return
		self.game.quick_strike(troops)

	def _recruitment_center(self):
		self.game.recruitment_center()

	def _troop_transports(self):
		troops = self._get_deployment_size(4)
		if troops is None:
			return
		self.game.troop_transports(troops)

	def _loot_villages(self):
		self.game.loot_villages()

	def _swordmaster(self):
		self.game.swordmaster()

	def _sardaukar(self):
		self.game.sardaukar()

	def _audience_with_emperor(self):
		self.game.audience_with_emperor()

	def _mobilization(self):
		troops = self._get_deployment_size(5)
		if troops is None:
			return
		self.game.mobilization(troops)

	def _seek_allies(self):
		self.game.seek_allies()

	def _political_maneuvering(self):
		pass

	def _get_deployment_size(self, limit):
		limit = min(self.game.current_player.troops_garrison, limit)
		value, ok = QInputDialog.getInt(None, "Deploy Troops", "How many troops would you like to deploy?", value=limit, min=0, max=limit)
		if ok:
			return value
		else:
			return None

class ActionButton:
	def __init__(self, text, action_enum, on_click, spice, solari, enabled):
		self.button = QPushButton(text)
		self.button.clicked.connect(on_click)
		self.action_enum = action_enum
		self.spice = spice
		self.solari = solari
		self.enabled = enabled

	def update(self, game):
		player = game.current_player
		enabled = self.action_enum in game.available_actions
		enabled = enabled and player.spice >= self.spice
		enabled = enabled and player.solari >= self.solari
		enabled = enabled and (self.enabled is None or self.enabled())
		self.button.setEnabled(enabled)