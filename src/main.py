# src/main.py

import sys
import argparse
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import setup_logger
from utils.config import load_config
from nand_controller import NANDController

def main():
    parser = argparse.ArgumentParser(description='3D NAND Flash Storage Optimization Tool')
    parser.add_argument('--gui', action='store_true', help='Run the tool with graphical user interface')
    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config('resources/config/config.yaml')

        # Set up logger
        logger = setup_logger('main', config)
        logger.info('Application started')

        # Create NAND controller
        nand_controller = NANDController(config)
        logger.info('NAND controller created')

        if args.gui:
            # Create application and main window
            app = QApplication(sys.argv)
            main_window = MainWindow(nand_controller)
            logger.info('Main window created')

            # Show the main window
            main_window.show()
            logger.info('Main window shown')

            # Run the application event loop
            sys.exit(app.exec_())
        else:
            # Run the tool in command-line mode
            # Add your command-line interface code here
            logger.info('Running in command-line mode')
            pass

    except Exception as e:
        logger.exception('An error occurred: %s', str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()