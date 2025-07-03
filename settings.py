import os
import json
from aqt import mw
from aqt.qt import *
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton

from . import set_hotkey, reload_hotkey

class HotkeySettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cheat Sheet Hotkey Settings")
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.info_label = QLabel("Enter a single letter to use as the hotkey for the cheat sheet popup:")
        self.layout.addWidget(self.info_label)

        self.input = QLineEdit()
        self.input.setMaxLength(1)
        self.layout.addWidget(self.input)

        self.save_btn = QPushButton("Save Hotkey")
        self.save_btn.clicked.connect(self.save_hotkey)
        self.layout.addWidget(self.save_btn)

        self.status = QLabel("")
        self.layout.addWidget(self.status)

        self.load_current_hotkey()

    def load_current_hotkey(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        hotkey = "C"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                key = config.get("hotkey", "C")
                if isinstance(key, str) and len(key) == 1:
                    hotkey = key.upper()
        except Exception:
            pass
        self.input.setText(hotkey)

    def save_hotkey(self):
        new_key = self.input.text().strip().upper()
        if len(new_key) != 1 or not new_key.isalpha():
            self.status.setText("Please enter a single letter (A-Z).")
            return
        set_hotkey(new_key)
        reload_hotkey()
        self.status.setText(f"Hotkey set to '{new_key}'. Please restart review for changes to take effect.")

def show_hotkey_settings():
    win = HotkeySettingsWindow(mw)
    win.show()

