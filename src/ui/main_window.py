# src/ui/main_window.py

import sys
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from .settings_dialog import SettingsDialog
from .result_viewer import ResultViewer
from utils.config import load_config, save_config
from nand_controller import NANDController

class MainWindow(QMainWindow):
    def __init__(self, nand_controller):
        super().__init__()
        self.nand_controller = nand_controller
        self.init_ui()

    def init_ui(self):
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

        # Create central widget
        self.result_viewer = ResultViewer()
        self.setCentralWidget(self.result_viewer)

    def open_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Open File', '', 'CSV Files (*.csv);;All Files (*)')
        if file_path:
            self.nand_controller.load_data(file_path)
            self.result_viewer.update_results(self.nand_controller.get_results())

    def save_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, 'Save File', '', 'CSV Files (*.csv);;All Files (*)')
        if file_path:
            self.nand_controller.save_data(file_path)

    def open_settings_dialog(self):
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec_() == SettingsDialog.Accepted:
            config = settings_dialog.get_config()
            save_config('resources/config/config.yaml', config)
            self.nand_controller.update_config(config)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Quit', 'Are you sure you want to quit?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())