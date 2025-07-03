import os
import json
from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip

def get_hotkey():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            key = config.get("hotkey", "C")
            if isinstance(key, str) and len(key) == 1:
                return key.upper()
    except Exception:
        pass
    return "C"

def set_hotkey(new_key: str):
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        config = {}
    config["hotkey"] = new_key.upper()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def reload_hotkey():
    # This function is only needed if you want to update a global variable in __init__.py
    # If you use a global HOTKEY_LETTER in __init__.py, you should call this after changing the hotkey.
    pass

class HotkeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Popkey Hotkey")
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter a single letter to use as the hotkey for the cheat sheet:"))
        self.input = QLineEdit()
        self.input.setMaxLength(1)
        self.input.setText(get_hotkey())
        layout.addWidget(self.input)
        self.status = QLabel()
        layout.addWidget(self.status)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def save(self):
        key = self.input.text().strip().upper()
        if len(key) != 1 or not key.isalpha():
            self.status.setText("Please enter a single letter (A-Z).")
            return
        set_hotkey(key)
        # Optionally, call reload_hotkey() here if you use a global in __init__.py
        tooltip(f"Hotkey set to '{key}'.")
        self.accept()

def open_hotkey_dialog():
    dlg = HotkeyDialog(mw)
    dlg.exec()
