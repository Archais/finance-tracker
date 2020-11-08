"Application entry point."
from PyQt5.QtWidgets import QApplication

from windows.main_window import MainWindow


def main():
    "Creates application instance."
    app = QApplication([])

    screen_res = app.desktop().screenGeometry()

    window = MainWindow(screen_res)
    window.show()

    app.exec_()


if __name__ == "__main__":
    main()
