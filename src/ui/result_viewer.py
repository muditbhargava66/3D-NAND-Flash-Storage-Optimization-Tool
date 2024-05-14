# src/ui/result_viewer.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtGui import QFont

class ResultViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)
        self.result_text_edit.setFont(QFont('Arial', 10))  # Change the font to a widely available one
        layout.addWidget(self.result_text_edit)

        self.setLayout(layout)

    def update_results(self, results):
        self.result_text_edit.clear()
        self.result_text_edit.append('NAND Optimization Results:\n')
        for key, value in results.items():
            self.result_text_edit.append(f'{key}: {value}')