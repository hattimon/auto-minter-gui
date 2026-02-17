import sys
from PyQt6.QtWidgets import QApplication

from mbc20_inscription_gui import Mbc20InscriptionGUI


def main():
    app = QApplication(sys.argv)
    win = Mbc20InscriptionGUI()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
