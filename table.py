from PyQt6.QtCore import (Qt, QSize, QModelIndex, QAbstractTableModel)
from PyQt6.QtWidgets import QTableView
from PyQt6.QtGui import QFont
from constants import *

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

class PlayerTableModel(QAbstractTableModel):
	def __init__(self, game):
		super().__init__()
		self.players = game.players
		self.game = game
		self.rows = [
			"",
			"Victory Points",
			"Influence",
			"Agents Left",
			"Spice",
			"Solari",
			"Garrison",
			"Deployed",
			"Swordmaster",
			"Palace"
		]

	def data(self, index, role):
		row = index.row()
		column = index.column()
		if role == Qt.ItemDataRole.DisplayRole:
			if column == 0:
				return self.rows[row]
			else:
				return self._get_player_column(row, column)
		elif role == Qt.ItemDataRole.TextAlignmentRole:
			if row == 0:
				return Qt.AlignmentFlag.AlignCenter
			elif column >= 1 and 1 <= row <= 7:
				return Qt.AlignmentFlag.AlignRight
			else:
				return None
		elif role == Qt.ItemDataRole.FontRole:
			if row == 0 and column - 1 == self.game.current_player_index:
				font = QFont()
				font.setBold(True)
				return font
			else:
				return None
		else:
			return None

	def rowCount(self, index):
		return len(self.rows)

	def columnCount(self, index):
		return PLAYER_COUNT + 1

	def _get_player_column(self, row, column):
		player = self.players[column - 1]
		rows = [
			f"Player {column}",
			player.victory_points,
			player.influence,
			player.agents_left,
			player.spice,
			player.solari,
			player.troops_garrison,
			player.troops_deployed,
			str(player.swordmaster),
			str(player.palace)
		]
		return rows[row]