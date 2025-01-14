from PyQt6.QtCore import (Qt, QSize, QModelIndex)
from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, QPushButton, QTableView, QHeaderView, QSizePolicy)
from game import ThumperGame
from constants import *
from table import PlayerTableModel

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
		self._add_button("Construct Palace", Action.CONSTRUCT_PALACE, solari=Cost.CONSTRUCT_PALACE, enabled=self._enable_construct_palace)
		self._add_button("Harvester", Action.HARVESTER)
		self._add_button("Refinery", Action.REFINERY)
		self._add_button("Spice Silo", Action.SPICE_SILO)
		self._add_button("Sell Melange", Action.SELL_MELANGE, spice=Cost.SELL_MELANGE)
		self._add_button("Secure Contract", Action.SECURE_CONTRACT)
		self._new_button_column()

		self._add_label("Military:")
		self._add_button("Stone Burner", Action.STONE_BURNER, spice=Cost.STONE_BURNER, enabled=self._stone_burner_enabled)
		self._add_button("Hire Mercenaries", Action.HIRE_MERCENARIES, solari=Cost.HIRE_MERCENARIES)
		self._add_button("Quick Strike", Action.QUICK_STRIKE)
		self._add_button("Recruitment Center", Action.RECRUITMENT_CENTER)
		self._add_button("Troop Transports", Action.TROOP_TRANSPORTS)
		self._add_button("Loot Villages", Action.LOOT_VILLAGES)
		self._new_button_column()

		self._add_label("Politics:")
		self._add_button("Swordmaster", Action.SWORDMASTER, solari=Cost.SWORDMASTER, enabled=self._swordmaster_enabled)
		self._add_button("Sardaukar", Action.SARDAUKAR, spice=Cost.SARDAUKAR)
		self._add_button("Audience with Emperor", Action.AUDIENCE_WITH_EMPEROR, spice=Cost.AUDIENCE_WITH_EMPEROR)
		self._add_button("Mobilization", Action.MOBILIZATION, solari=Cost.MOBILIZATION)
		self._add_button("Seek Allies", Action.SEEK_ALLIES)
		self._add_button("Political Maneuvering", Action.POLITICAL_MANEUVERING)

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

	def _add_button(self, text, action_enum, spice=0, solari=0, enabled=None):
		button = ActionButton(text, action_enum, spice, solari, enabled)
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

class ExpandingTableView(QTableView):
	def sizeHint(self):
		model = self.model()
		index = QModelIndex()
		column_count = model.columnCount(index)
		column_width = sum(self.columnWidth(i) for i in range(column_count))
		width = self.verticalHeader().width() + column_width
		row_count = model.rowCount(index)
		row_width = sum(self.rowHeight(i) for i in range(row_count))
		height = self.horizontalHeader().height() + row_width
		return QSize(width, height)