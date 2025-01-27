import sys
from PyQt6.QtWidgets import QApplication
from qt import ThumperQt

app = QApplication(sys.argv)
ThumperQt()
sys.exit(app.exec())