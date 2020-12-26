"Application entry point."
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from windows.main_window import MainWindow


def main():
    "Creates application instance."
    app = QApplication([])
    app.setWindowIcon(QIcon("tree.png"))

    screen_res = app.desktop().screenGeometry()

    window = MainWindow(screen_res)
    window.show()

    app.exec_()


if __name__ == "__main__":
    main()
