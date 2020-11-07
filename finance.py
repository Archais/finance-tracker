"Application entry point"
from PyQt5.QtWidgets import QApplication

from windows.main_window import MainWindow

app = QApplication([])

screenRes = app.desktop().screenGeometry()

window = MainWindow(screenRes)
window.show()

app.exec_()
