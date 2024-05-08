# src/main.py

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import setup_logger
from utils.config import load_config
from nand_controller import NANDController

def main():
    # Set up logger
    setup_logger()

    # Load configuration
    config = load_config('resources/config/config.yaml')

    # Create NAND controller
    nand_controller = NANDController(config)

    # Create application and main window
    app = QApplication(sys.argv)
    main_window = MainWindow(nand_controller)
    main_window.show()

    # Run the application event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()