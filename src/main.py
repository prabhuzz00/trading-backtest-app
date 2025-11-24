from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Trading Backtest Platform")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()