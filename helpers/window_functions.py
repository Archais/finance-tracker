"Generic functions for window objects."
from PyQt5.QtWidgets import QDesktopWidget, QWidget


def center_window(window: QWidget):
    "Centers given window in the screen."
    frame = window.frameGeometry()
    center_point = QDesktopWidget().availableGeometry().center()
    frame.moveCenter(center_point)
    window.move(frame.topLeft())
