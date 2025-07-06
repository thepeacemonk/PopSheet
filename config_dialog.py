import os
import json
import shutil
import webbrowser

from aqt import mw
from aqt.qt import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QListWidget, QListWidgetItem, QDialogButtonBox, QFileDialog, 
    QFont, Qt, QColor, QPixmap
)

ALLOWED_HOTKEYS = ["W", "X", "Z"]

def get_hotkey():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            key = config.get("hotkey", "W")
            if key in ALLOWED_HOTKEYS:
                return key
    except Exception:
        pass
    return "W"

def set_hotkey(new_key: str):
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        config = {}
    config["hotkey"] = new_key
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def reload_hotkey():
    pass

def next_sheet_number(addon_folder):
    existing = []
    for fname in os.listdir(addon_folder):
        if fname.startswith("sheet-") and fname.endswith(".png"):
            try:
                num = int(fname[len("sheet-"):-len(".png")])
                existing.append(num)
            except Exception:
                continue
    n = 1
    while n in existing:
        n += 1
    return n

def list_sheet_files(addon_folder):
    files = []
    for fname in sorted(os.listdir(addon_folder)):
        if fname.startswith("sheet-") and fname.endswith(".png"):
            files.append(fname)
    return files

def get_anki_palette_colors():
    palette = mw.app.palette()
    bg = palette.window().color().name()
    fg = palette.windowText().color().name()
    btn_bg = palette.button().color().name()
    btn_fg = palette.buttonText().color().name()
    return bg, fg, btn_bg, btn_fg

class ClickableLogo(QLabel):
    def __init__(self, image_path, url, parent=None):
        super().__init__(parent)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(192, 192, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.url = url
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setToolTip("Support PopSheet on Ko-fi!")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            webbrowser.open(self.url)

class sheetListItem(QWidget):
    def __init__(self, filename, delete_callback, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.delete_callback = delete_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.label = QLabel(filename)
        font = QFont("Arial")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPixelSize(13)
        self.label.setFont(font)

        bg, fg, btn_bg, btn_fg = get_anki_palette_colors()

        # SVG icons for normal and hover states
        # Choose icon based on system theme (light/dark)
        palette = mw.app.palette()
        bg_color = palette.window().color().lightness()
        if bg_color > 128:
            icon_filename = "cross-circle.png"
        else:
            icon_filename = "cross-circle-dark.png"
        icon_path = os.path.join(os.path.dirname(__file__), icon_filename).replace("\\", "/")

        self.delete_btn = QPushButton("")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Use SVGs as background images for the button, changing on hover
        self.delete_btn.setStyleSheet(f"""
        QPushButton {{
            border-image: url("{icon_path}") 0 0 0 0 stretch stretch;
            border-radius: 8px;
            width: 14px;
            height: 14px;
            padding: 0;
        }}
        """)

        self.delete_btn.clicked.connect(self.on_delete)

        layout.addWidget(self.label)
        layout.addWidget(self.delete_btn)
        layout.addStretch()

        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(bg))
        self.setPalette(pal)

    def on_delete(self):
        self.delete_callback(self.filename)

class HotkeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PopSheet Settings")
        self.setMinimumWidth(370)
        self.setStyleSheet("""
        QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem {
            font-family: Arial;
            font-size: 13px;
        }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        # --- Logo with extra bottom margin ---
        # Choose logo based on system theme
        palette = mw.app.palette()
        bg_color = palette.window().color().lightness()
        if bg_color > 128:
            logo_filename = "PopSheet_logo_light.png"
        else:
            logo_filename = "PopSheet_logo_dark.png"
        logo_path = os.path.join(os.path.dirname(__file__), logo_filename)
        if os.path.exists(logo_path):
            logo_container = QVBoxLayout()
            logo = ClickableLogo(logo_path, "https://ko-fi.com/peacemonk")
            logo_container.addWidget(logo)
            logo_container.addSpacing(12) # More space below logo

        # --- Warning label just below the logo ---
            self.warning_label = QLabel("Add images that are max size of 700px wide.")
            self.warning_label.setStyleSheet("color: #00bf63; font-weight: bold; font-size: 13px;")
            self.warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_container.addWidget(self.warning_label)

            # --- Second label just below the first warning label ---
            self.info_label = QLabel("Changes will take effect after you restart Anki.")
            self.info_label.setStyleSheet("color: #888; font-size: 12px;")
            self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_container.addWidget(self.info_label)

            logo_container.addSpacing(12)  # Space below warning
            layout.addLayout(logo_container)

        # --- Hotkey selection ---
        hotkey_label = QLabel("Select the hotkey letter to open the cheat sheet:")
        hotkey_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(hotkey_label)

        # --- Hotkey selection buttons ---
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton

        hotkey_options = ["W", "X", "Z"]
        current_hotkey = get_hotkey()  # Your function to get the current hotkey

        hotkey_btn_layout = QHBoxLayout()
        self.hotkey_buttons = {}

        for key in hotkey_options:
            btn = QPushButton(key)
            btn.setCheckable(True)
            btn.setChecked(key == current_hotkey)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #00bf63;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 22px;
                    font-size: 16px;
                }
                QPushButton:checked {
                    background-color: #008f46;
                }
                QPushButton:hover {
                    background-color: #00a155;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: set_hotkey(k))
            self.hotkey_buttons[key] = btn
            hotkey_btn_layout.addWidget(btn)

        layout.addLayout(hotkey_btn_layout)  # <<<< Only once, after the loop!

        # --- Add sheet Image button ---
        self.add_sheet_btn = QPushButton("Add Cheat Sheet")
        self.add_sheet_btn.clicked.connect(self.add_sheet_image)
        layout.addWidget(self.add_sheet_btn)
        self.add_sheet_btn.setStyleSheet("""
            QPushButton {
                background-color: #00bf63;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 14px;
                transition: background 0.2s;
            }
            QPushButton:hover {
                background-color: #00a155;
            }
            QPushButton:pressed {
                background-color: #008f46;
            }
        """)


        # --- sheet file list ---
        self.sheet_list = QListWidget()
        self.sheet_list.setSpacing(2)
        bg, fg, btn_bg, btn_fg = get_anki_palette_colors()
        self.sheet_list.setStyleSheet(f"""
        QListWidget {{
            background: {bg};
            border: 1.5px solid {fg};
            color: {fg};
            border-radius: 8px;
            margin-bottom: 12px;
        }}
        """)
        layout.addWidget(QLabel("Existing sheets:"))
        layout.addWidget(self.sheet_list)

        self.refresh_sheet_list()

        self.status = QLabel()
        self.status.setStyleSheet("font-size:11px; color:#aaffaa; padding-top:2px;")
        layout.addWidget(self.status)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def refresh_sheet_list(self):
        self.sheet_list.clear()
        addon_folder = os.path.dirname(__file__)
        for fname in list_sheet_files(addon_folder):
            item = QListWidgetItem()
            widget = sheetListItem(fname, self.delete_sheet)
            item.setSizeHint(widget.sizeHint())
            self.sheet_list.addItem(item)
            self.sheet_list.setItemWidget(item, widget)

    def delete_sheet(self, filename):
        addon_folder = os.path.dirname(__file__)
        file_path = os.path.join(addon_folder, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                # Set color based on light/dark mode
                palette = mw.app.palette()
                bg_color = palette.window().color().lightness()
                color = "#00bf63" if bg_color > 128 else "#6fff9f"
                self.status.setStyleSheet(f"font-size:11px; color:{color}; padding-top:2px;")
                self.status.setText(f"Deleted {filename}")
                self.refresh_sheet_list()
            except Exception as e:
                self.status.setStyleSheet("font-size:11px; color:#ff3333; padding-top:2px;")
                self.status.setText(f"Error deleting {filename}: {e}")

    def add_sheet_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select sheet Image", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            try:
                addon_folder = os.path.dirname(__file__)
                n = next_sheet_number(addon_folder)
                dest_path = os.path.join(addon_folder, f"sheet-{n}.png")
                shutil.copy(file_path, dest_path)
                # Set color based on light/dark mode
                palette = mw.app.palette()
                bg_color = palette.window().color().lightness()
                color = "#00bf63" if bg_color > 128 else "#6fff9f"
                self.status.setStyleSheet(f"font-size:11px; color:{color}; padding-top:2px;")
                self.status.setText(f"Added as sheet-{n}.png!")
                self.refresh_sheet_list()
            except Exception as e:
                self.status.setStyleSheet("font-size:11px; color:#ff3333; padding-top:2px;")
                self.status.setText(f"Error copying file: {e}")

    def save(self):
        # Finds out which hotkey is selected
        selected_key = None
        for key, btn in self.hotkey_buttons.items():
            if btn.isChecked():
                selected_key = key
                break
        if selected_key is None:
            self.status.setText("Please select a hotkey.")
            return
        set_hotkey(selected_key)
        reload_hotkey()
        self.status.setText(
            f"Hotkey set to '{selected_key}'. Please close and reopen the review window for the change to take effect."
        )
        self.accept()

def open_hotkey_dialog():
    dlg = HotkeyDialog(mw)
    dlg.exec()
