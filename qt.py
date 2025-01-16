from functools import partial
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QInputDialog, QMessageBox, QDialog)
from game import ThumperGame
from constants import *
from table import ExpandingTableView, PlayerTableModel
from radio import RadioButtonDialog

class ThumperQt(QWidget):
	def __init__(self):
		super().__init__()
		self.game = ThumperGame()
		self._initialize_ui()

	def _initialize_ui(self):
		self.buttons = []
		self.button_row = 2
		self.button_column = 0
		self.grid = QGridLayout()
		for i in range(3):
			self.grid.setColumnMinimumWidth(i, 140)
		self.setLayout(self.grid)
		self._add_labels_top()
		self._add_buttons()
		self._update_labels_top()
		self._update_buttons()
		self._add_table()
		self.setWindowTitle("Thumper")
		self.show()

	def _add_labels_top(self):
		self.current_player_label = QLabel("")
		self.current_round_label = QLabel("")
		self.current_round_label.setAlignment(Qt.AlignmentFlag.AlignRight)
		self.actions_label = QLabel("")
		self.actions_label.setMinimumHeight(30)
		self.actions_label.setAlignment(Qt.AlignmentFlag.AlignTop)
		self.grid.addWidget(self.current_player_label, 0, 0, 1, 2)
		self.grid.addWidget(self.current_round_label, 0, 2, 1, 1)
		self.grid.addWidget(self.actions_label, 1, 0, 1, 3)
		
	def _update_labels_top(self):
		self.current_player_label.setText(f"Current player: Player {self.game.current_player_index + 1}")
		self.current_round_label.setText(f"Round {self.game.round}")
		action_enums = map(lambda action: action.name.lower(), self.game.current_player.actions)
		action_string = ", ".join(action_enums)
		self.actions_label.setText(f"Available actions: {action_string}")

	def _add_buttons(self):
		self._add_button_label("Economy:")
		self._add_button("Construct Palace", ActionType.ECONOMIC, Action.CONSTRUCT_PALACE, self._construct_palace, solari=Cost.CONSTRUCT_PALACE, enabled=self._enable_construct_palace)
		self._add_button("Harvester", ActionType.ECONOMIC, Action.HARVESTER, self._harvester)
		self._add_button("Refinery", ActionType.ECONOMIC, Action.REFINERY, self._refinery)
		self._add_button("Spice Silo", ActionType.ECONOMIC, Action.SPICE_SILO, self._spice_silo)
		self._add_button("Sell Melange", ActionType.ECONOMIC, Action.SELL_MELANGE, self._sell_melange, spice=Cost.SELL_MELANGE)
		self._add_button("Secure Contract", ActionType.ECONOMIC, Action.SECURE_CONTRACT, self._secure_contract)
		self._new_button_column()

		self._add_button_label("Military:")
		self._add_button("Stone Burner", ActionType.MILITARY, Action.STONE_BURNER, self._stone_burner, spice=Cost.STONE_BURNER, enabled=self._stone_burner_enabled)
		self._add_button("Hire Mercenaries", ActionType.MILITARY, Action.HIRE_MERCENARIES, self._hire_mercenaries, solari=Cost.HIRE_MERCENARIES)
		self._add_button("Quick Strike", ActionType.MILITARY, Action.QUICK_STRIKE, self._quick_strike)
		self._add_button("Recruitment Center", ActionType.MILITARY, Action.RECRUITMENT_CENTER, self._recruitment_center)
		self._add_button("Troop Transports", ActionType.MILITARY, Action.TROOP_TRANSPORTS, self._troop_transports, enabled=self._has_garrison)
		self._add_button("Loot Villages", ActionType.MILITARY, Action.LOOT_VILLAGES, self._loot_villages, enabled=self._has_garrison)
		self._new_button_column()

		self._add_button_label("Politics:")
		self._add_button("Swordmaster", ActionType.POLITICAL, Action.SWORDMASTER, self._swordmaster, solari=Cost.SWORDMASTER, enabled=self._swordmaster_enabled)
		self._add_button("Sardaukar", ActionType.POLITICAL, Action.SARDAUKAR, self._sardaukar, spice=Cost.SARDAUKAR)
		self._add_button("Audience with Emperor", ActionType.POLITICAL, Action.AUDIENCE_WITH_EMPEROR, self._audience_with_emperor, spice=Cost.AUDIENCE_WITH_EMPEROR)
		self._add_button("Mobilization", ActionType.POLITICAL, Action.MOBILIZATION, self._mobilization, solari=Cost.MOBILIZATION, enabled=self._has_garrison)
		self._add_button("Seek Allies", ActionType.POLITICAL, Action.SEEK_ALLIES, self._seek_allies)
		self._add_button("Political Maneuvering", ActionType.POLITICAL, Action.POLITICAL_MANEUVERING, self._political_maneuvering)

		self.pass_button = QPushButton("Pass")
		self.pass_button.clicked.connect(self._pass_turn)
		self.grid.addWidget(self.pass_button, 9, 2, 1, 1)

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
		table_row = 4 + 6
		columns = 3
		self.grid.addWidget(self.table, table_row, 0, 1, columns)
		self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

	def _add_button_label(self, text):
		label = QLabel(text)
		self.grid.addWidget(label, self.button_row, self.button_column, alignment=Qt.AlignmentFlag.AlignCenter)
		self.button_row += 1

	def _add_button(self, text, action_type, action_enum, on_click, spice=0, solari=0, enabled=None):
		handler = partial(self._interface_update_wrapper, on_click)
		button = ActionButton(text, action_type, action_enum, handler, spice, solari, enabled)
		self.grid.addWidget(button.button, self.button_row, self.button_column)
		self.button_row += 1
		self.buttons.append(button)

	def _new_button_column(self):
		self.button_row = 2
		self.button_column += 1

	def _update_buttons(self):
		for button in self.buttons:
			button.update(self.game)
		self.pass_button.setEnabled(not self.game.game_ended)

	def _interface_update_wrapper(self, on_click):
		self.table_model.beginResetModel()
		on_click()
		self._update_labels_top()
		self._update_buttons()
		self.table_model.endResetModel()

	def _enable_construct_palace(self):
		return not self.game.current_player.palace

	def _stone_burner_enabled(self):
		return any(player is not self.game.current_player and player.troops_garrison > 0 for player in self.game.players)

	def _has_garrison(self):
		return self.game.current_player.troops_garrison > 0

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
		other_players = filter(lambda player: player is not self.game.current_player, self.game.players)
		players_by_garrison = sorted(other_players, key=lambda player: player.troops_garrison, reverse=True)
		largest_garrison_player = players_by_garrison[0]
		player_index = self.game.players.index(largest_garrison_player) + 1
		while True:
			player_index, ok = QInputDialog.getInt(None, "Stone Burner", "Which player would you like to attack?", value=player_index, min=1, max=4)
			if not ok:
				return
			targeted_player = self.game.players[player_index - 1]
			if targeted_player is self.game.current_player:
				self._show_error("You cannot target yourself.")
				continue
			if targeted_player.troops_garrison == 0:
				self._show_error("This player does not have a garrison.")
				continue
			break
		self.game.stone_burner(player_index)

	def _hire_mercenaries(self):
		troops = self._get_deployment_size(2, 3)
		if troops is None:
			return
		self.game.hire_mercenaries(troops)

	def _quick_strike(self):
		troops = self._get_deployment_size(1, 2)
		if troops is None:
			return
		self.game.quick_strike(troops)

	def _recruitment_center(self):
		self.game.recruitment_center()

	def _troop_transports(self):
		troops = self._get_deployment_size(0, 4)
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
		troops = self._get_deployment_size(0, 5)
		if troops is None:
			return
		self.game.mobilization(troops)

	def _seek_allies(self):
		self.game.seek_allies()

	def _political_maneuvering(self):
		options = {
			"Economic": ActionType.ECONOMIC,
			"Military": ActionType.MILITARY,
			"Political": ActionType.POLITICAL
		}
		dialog = RadioButtonDialog("Select an action type:", options)
		result = dialog.exec()
		if result == QDialog.DialogCode.Accepted:
			action_type = dialog.get_value()
			self.game.political_maneuvering(action_type)

	def _pass_turn(self):
		self._interface_update_wrapper(self.game.pass_turn)

	def _get_deployment_size(self, recruited, limit):
		limit = min(self.game.current_player.troops_garrison + recruited, limit)
		value, ok = QInputDialog.getInt(None, "Deploy Troops", "How many troops would you like to deploy?", value=limit, min=0, max=limit)
		if ok:
			return value
		else:
			return None

	def _show_error(self, text):
		message_box = QMessageBox()
		message_box.setIcon(QMessageBox.Icon.Critical)
		message_box.setWindowTitle("Error")
		message_box.setText(text)
		message_box.exec()

class ActionButton:
	def __init__(self, text, action_type, action_enum, on_click, spice, solari, enabled):
		self.button = QPushButton(text)
		self.button.clicked.connect(on_click)
		self.action_type = action_type
		self.action_enum = action_enum
		self.spice = spice
		self.solari = solari
		self.enabled = enabled

	def update(self, game):
		player = game.current_player
		enabled = not game.game_ended
		enabled = enabled and self.action_enum in game.available_actions
		enabled = enabled and self.action_type in player.actions
		enabled = enabled and player.spice >= self.spice
		enabled = enabled and player.solari >= self.solari
		enabled = enabled and (self.enabled is None or self.enabled())
		self.button.setEnabled(enabled)