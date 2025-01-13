from colorama import init, Fore, Style
from tabulate import tabulate
from game import ThumperGame
from constants import Action

class ThumperConsole:
	def __init__(self):
		init(autoreset=True)
		self.game = ThumperGame()

	def render_state(self):
		available_actions = self.game.available_actions
		economic_color = Fore.YELLOW
		military_color = Fore.BLUE
		political_color = Fore.GREEN
		not_available_color = Fore.BLACK

		def get_cell(name, action, color):
			if action not in available_actions:
				color = not_available_color
			formatted = color + name + Style.RESET_ALL
			return formatted

		cells = [[
			get_cell("Construct Palace", Action.CONSTRUCT_PALACE, economic_color),
			get_cell("Stone Burner", Action.STONE_BURNER, military_color),
			get_cell("Recruit Agent", Action.RECRUIT_AGENT, political_color)
		], [
			get_cell("Harvester", Action.HARVESTER, economic_color),
			get_cell("Hire Mercenaries", Action.HIRE_MERCENARIES, military_color),
			get_cell("Sardaukar", Action.SARDAUKAR, political_color)
		], [
			get_cell("Refinery", Action.REFINERY, economic_color),
			get_cell("Quick Strike", Action.QUICK_STRIKE, military_color),
			get_cell("Audience with Emperor", Action.AUDIENCE_WITH_EMPEROR, political_color)
		], [
			get_cell("Spice Silo", Action.SPICE_SILO, economic_color),
			get_cell("Recruitment Center", Action.RECRUITMENT_CENTER, military_color),
			get_cell("Mobilization", Action.MOBILIZATION, political_color)
		], [
			get_cell("Sell Melange", Action.SELL_MELANGE, economic_color),
			get_cell("Troop Transports", Action.TROOP_TRANSPORTS, military_color),
			get_cell("Seek Allies", Action.SEEK_ALLIES, political_color)
		], [
			get_cell("Secure Contract", Action.SECURE_CONTRACT, economic_color),
			get_cell("Loot Villages", Action.LOOT_VILLAGES, military_color),
			get_cell("Political Maneuvering", Action.POLITICAL_MANEUVERING, political_color)
		]]
		table = tabulate(cells, tablefmt="simple_outline")
		print(table)