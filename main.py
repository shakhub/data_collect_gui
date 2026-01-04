import sys

from PyQt5.QtWidgets import QApplication

from src.ui.main_window import DataCollectorApp


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = DataCollectorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
