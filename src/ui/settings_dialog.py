# src/ui/settings_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from utils.config import load_config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle('Settings')
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        # Create input fields
        self.create_input_field(layout, 'NAND Capacity (GB):', 'nand_capacity')
        self.create_input_field(layout, 'Page Size (KB):', 'page_size')
        self.create_input_field(layout, 'Block Size (MB):', 'block_size')
        self.create_input_field(layout, 'Number of Planes:', 'num_planes')

        # Create buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def create_input_field(self, layout, label_text, field_name):
        field_layout = QHBoxLayout()
        label = QLabel(label_text)
        field = QLineEdit()
        field.setObjectName(field_name)
        field_layout.addWidget(label)
        field_layout.addWidget(field)
        layout.addLayout(field_layout)

    def load_config(self):
        config = load_config('resources/config/config.yaml').config
        self.findChild(QLineEdit, 'nand_capacity').setText(str(config['nand_capacity']))
        self.findChild(QLineEdit, 'page_size').setText(str(config['page_size']))
        self.findChild(QLineEdit, 'block_size').setText(str(config['block_size']))
        self.findChild(QLineEdit, 'num_planes').setText(str(config['num_planes']))

    def get_config(self):
        config = {
            'nand_capacity': int(self.findChild(QLineEdit, 'nand_capacity').text()),
            'page_size': int(self.findChild(QLineEdit, 'page_size').text()),
            'block_size': int(self.findChild(QLineEdit, 'block_size').text()),
            'num_planes': int(self.findChild(QLineEdit, 'num_planes').text())
        }
        return config