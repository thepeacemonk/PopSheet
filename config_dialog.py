import os
import json
import shutil
import webbrowser
from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip

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

def next_chart_number(addon_folder):
    existing = []
    for fname in os.listdir(addon_folder):
        if fname.startswith("chart-") and fname.endswith(".png"):
            try:
                num = int(fname[len("chart-"):-len(".png")])
                existing.append(num)
            except Exception:
                continue
    n = 1
    while n in existing:
        n += 1
    return n

def list_chart_files(addon_folder):
    files = []
    for fname in sorted(os.listdir(addon_folder)):
        if fname.startswith("chart-") and fname.endswith(".png"):
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

class ChartListItem(QWidget):
    def __init__(self, filename, delete_callback, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.delete_callback = delete_callback
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self.label = QLabel(filename)

        font = QFont("Courier New, monospace")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPixelSize(13)
        self.label.setFont(font)

        bg, fg, btn_bg, btn_fg = get_anki_palette_colors()

        self.delete_btn = QPushButton("x")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setFont(font)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg};
                color: {btn_fg};
                border-radius: 14px;
                font-weight: bold;
                font-size: 18pt;
                border: 1px solid {fg};
                padding-bottom: 2px;
            }}
            QPushButton:hover {{
                background: {fg};
                color: {bg};
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
        logo_path = os.path.join(os.path.dirname(__file__), "PopSheet_logo.png")
        if os.path.exists(logo_path):
            logo_container = QVBoxLayout()
            logo = ClickableLogo(logo_path, "https://ko-fi.com/peacemonk")
            logo_container.addWidget(logo)
            logo_container.addSpacing(32)  # More space below logo
            layout.addLayout(logo_container)

        # --- Hotkey selection ---
        hotkey_label = QLabel("Select the hotkey letter to open the cheat sheet:")
        hotkey_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(hotkey_label)

        self.combo = QComboBox()
        self.combo.addItems(ALLOWED_HOTKEYS)
        current = get_hotkey()
        idx = ALLOWED_HOTKEYS.index(current) if current in ALLOWED_HOTKEYS else 0
        self.combo.setCurrentIndex(idx)
        layout.addWidget(self.combo)

        # --- Add Chart Image button ---
        self.add_chart_btn = QPushButton("Add Chart Image...")
        self.add_chart_btn.clicked.connect(self.add_chart_image)
        layout.addWidget(self.add_chart_btn)

        # --- Chart file list ---
        self.chart_list = QListWidget()
        self.chart_list.setSpacing(2)
        bg, fg, btn_bg, btn_fg = get_anki_palette_colors()
        self.chart_list.setStyleSheet(f"""
            QListWidget {{
                background: {bg};
                border: 1.5px solid {fg};
                color: {fg};
                border-radius: 8px;
                margin-bottom: 12px;
            }}
        """)
        layout.addWidget(QLabel("Existing charts:"))
        layout.addWidget(self.chart_list)
        self.refresh_chart_list()

        self.status = QLabel()
        self.status.setStyleSheet("font-size:11px; color:#aaffaa; padding-top:2px;")
        layout.addWidget(self.status)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def refresh_chart_list(self):
        self.chart_list.clear()
        addon_folder = os.path.dirname(__file__)
        for fname in list_chart_files(addon_folder):
            item = QListWidgetItem()
            widget = ChartListItem(fname, self.delete_chart)
            item.setSizeHint(widget.sizeHint())
            self.chart_list.addItem(item)
            self.chart_list.setItemWidget(item, widget)

    def delete_chart(self, filename):
        addon_folder = os.path.dirname(__file__)
        file_path = os.path.join(addon_folder, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.status.setText(f"Deleted {filename}")
                self.refresh_chart_list()
            except Exception as e:
                self.status.setText(f"Error deleting {filename}: {e}")

    def add_chart_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Chart Image", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            try:
                addon_folder = os.path.dirname(__file__)
                n = next_chart_number(addon_folder)
                dest_path = os.path.join(addon_folder, f"chart-{n}.png")
                shutil.copy(file_path, dest_path)
                self.status.setText(f"Added as chart-{n}.png!")
                self.refresh_chart_list()
            except Exception as e:
                self.status.setText(f"Error copying file: {e}")

    def save(self):
        key = self.combo.currentText()
        set_hotkey(key)
        reload_hotkey()
        self.status.setText(
            f"Hotkey set to '{key}'. Please close and reopen the review window for the change to take effect."
        )
        self.accept()

def open_hotkey_dialog():
    dlg = HotkeyDialog(mw)
    dlg.exec()
