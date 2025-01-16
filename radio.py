from PyQt6.QtWidgets import (QDialog, QRadioButton, QVBoxLayout, QDialogButtonBox)

class RadioButtonDialog(QDialog):
	def __init__(self, title, options):
		super().__init__()
		self.options = options
		self.setWindowTitle(title)
		self.radio_buttons = list(map(lambda description: QRadioButton(description), options.keys()))
		self.radio_buttons[0].setChecked(True)
		layout = QVBoxLayout()
		for radio_button in self.radio_buttons:
			layout.addWidget(radio_button)
		button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
		layout.addWidget(button_box)
		button_box.accepted.connect(self.accept)
		button_box.rejected.connect(self.reject)
		self.setLayout(layout)

	def get_value(self):
		for radio_button in self.radio_buttons:
			if radio_button.isChecked():
				value = self.options[radio_button.text()]
				return value
		raise ValueError("Unable to find a corresponding value for this option")