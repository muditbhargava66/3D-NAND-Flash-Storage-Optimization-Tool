# src/ui/main_window.py

import sys
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox, QVBoxLayout, QWidget, QTextEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from utils.config import load_config, save_config
from utils.logger import get_logger
from nand_controller import NANDController

class MainWindow(QMainWindow):
    def __init__(self, nand_controller):
        super().__init__()
        self.nand_controller = nand_controller
        self.logger = get_logger(__name__)
        self.init_ui()

    def init_ui(self):
        self.logger.info("Initializing main window UI")
        self.setWindowTitle('3D NAND Optimization Tool')
        self.setWindowIcon(QIcon('resources/icon.png'))
        self.setGeometry(100, 100, 800, 600)

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        settings_menu = menu_bar.addMenu('Settings')

        # Create file menu actions
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Create settings menu actions
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.open_settings_dialog)

        settings_menu.addAction(settings_action)

        # Create central widget and layout
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)

        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)
        layout.addWidget(self.result_text_edit)

        self.setCentralWidget(central_widget)
        self.logger.info("Main window UI initialized")

    def open_file(self):
        self.logger.info("Opening file")
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Open File', '', 'CSV Files (*.csv);;All Files (*)')
        if file_path:
            self.nand_controller.load_data(file_path)
            self.update_results()

    def save_file(self):
        self.logger.info("Saving file")
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, 'Save File', '', 'CSV Files (*.csv);;All Files (*)')
        if file_path:
            self.nand_controller.save_data(file_path)

    def open_settings_dialog(self):
        self.logger.info("Opening settings dialog")
        # Implement the settings dialog logic here
        pass

    def update_results(self):
        self.logger.info("Updating results")
        results = self.nand_controller.get_results()
        self.result_text_edit.clear()
        self.result_text_edit.append('NAND Optimization Results:\n')
        for key, value in results.items():
            self.result_text_edit.append(f'{key}: {value}')

    def closeEvent(self, event):
        self.logger.info("Closing main window")
        reply = QMessageBox.question(self, 'Quit', 'Are you sure you want to quit?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()