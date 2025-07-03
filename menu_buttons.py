from aqt import mw
from aqt.qt import QAction

# Import the function that shows the settings window
from .settings import show_hotkey_settings

def add_popkey_menu():
    action = QAction("Popkey", mw)
    action.triggered.connect(show_hotkey_settings)
    mw.form.menuTools.addAction(action)

add_popkey_menu()