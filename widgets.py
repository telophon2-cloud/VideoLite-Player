import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit, QFileDialog
from PySide6.QtCore import Qt


WIN95_STYLE = """
QMainWindow, QDialog {
    background-color: #c0c0c0;
}
QPushButton {
    background-color: #c0c0c0;
    border: 2px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
    padding: 4px 12px;
    color: black;
    font-family: "MS Sans Serif", "Arial";
    font-size: 12px;
}
QPushButton:pressed {
    border-color: #808080 #ffffff #ffffff #808080;
    padding: 5px 11px 3px 13px;
}
QSlider::groove:horizontal {
    border: 2px inset #808080;
    background: #ffffff;
    height: 6px;
}
QSlider::handle:horizontal {
    background: #c0c0c0;
    border: 2px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
    width: 12px;
    margin: -6px 0;
}
QLabel {
    color: black;
    font-family: "MS Sans Serif", "Arial";
    font-size: 12px;
}
QLineEdit, QTextEdit {
    background-color: #ffffff;
    border: 2px inset #808080;
    color: black;
    font-family: "MS Sans Serif", "Arial";
}
QMenuBar {
    background-color: #c0c0c0;
    border-bottom: 2px solid #808080;
}
QMenuBar::item {
    background-color: transparent;
    color: black;
    padding: 4px 8px;
}
QMenuBar::item:selected {
    background-color: #000080;
    color: white;
}
QMenu {
    background-color: #c0c0c0;
    border: 2px solid;
    border-color: #ffffff #808080 #808080 #ffffff;
}
QMenu::item:selected {
    background-color: #000080;
    color: white;
}
"""


class InfoDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Параметры видео")
        self.resize(450, 350)
        self.setStyleSheet(WIN95_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(text)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_button)
        layout.addLayout(btn_layout)


class OpenDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Открыть источник")
        self.resize(500, 120)
        self.setStyleSheet(WIN95_STYLE)
        self.result_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        layout.addWidget(QLabel("Введите путь к файлу, URL или Magnet-ссылку:"))

        input_layout = QHBoxLayout()
        self.line_edit = QLineEdit()
        input_layout.addWidget(self.line_edit)

        self.browse_button = QPushButton("Обзор...")
        self.browse_button.clicked.connect(self.browse_file)
        input_layout.addWidget(self.browse_button)
        layout.addLayout(input_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)

        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать видео", "", "Видео файлы (*.mp4 *.mkv *.avi *.mov);;Все файлы (*.*)"
        )
        if file_path:
            self.line_edit.setText(file_path)

    def validate_and_accept(self):
        self.result_path = self.line_edit.text().strip()
        if self.result_path:
            self.accept()
