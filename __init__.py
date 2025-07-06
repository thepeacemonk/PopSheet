"""PopSheet add-on init"""

import os
import re
import json
from typing import Optional, List

from aqt import gui_hooks, mw
from aqt.qt import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QCursor,
    QPixmap,
    QPainter,
    QPainterPath,
    Qt,
    QKeySequence,
    QShortcut,
    QAction,
)

from .config_dialog import open_hotkey_dialog  # <-- NEW

ALLOWED_HOTKEYS = ["W", "X", "Z"]

_dlg: Optional[QDialog] = None
_chart_files: List[str] = []
_current_index: int = 0

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
    global HOTKEY_LETTER
    HOTKEY_LETTER = get_hotkey()

HOTKEY_LETTER = get_hotkey()

def _find_chart_files() -> List[str]:
    folder = os.path.dirname(__file__)
    files = []
    for fname in os.listdir(folder):
        m = re.match(r"chart-(\d+)\.png$", fname)
        if m:
            files.append((int(m.group(1)), os.path.join(folder, fname)))
    files.sort()
    return [f[1] for f in files]

def _image_path(idx: int = 0) -> Optional[str]:
    if not _chart_files:
        return None
    if 0 <= idx < len(_chart_files):
        return _chart_files[idx]
    return None

def _anki_palette():
    palette = mw.app.palette()
    bg = palette.window().color().name()
    fg = palette.windowText().color().name()
    return bg, fg

class RoundedImageLabel(QLabel):
    def __init__(self, radius=24, parent=None):
        super().__init__(parent)
        self._radius = radius
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("margin:0px; padding:0px; background: transparent;")

    def setPixmap(self, pixmap: QPixmap):
        if pixmap.isNull():
            super().setPixmap(pixmap)
            return
        size = pixmap.size()
        mask = QPixmap(size)
        mask.fill(Qt.GlobalColor.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, size.width(), size.height(), self._radius, self._radius)
        painter.fillPath(path, Qt.GlobalColor.white)
        painter.end()
        rounded = QPixmap(size)
        rounded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        super().setPixmap(rounded)

class ChartDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sheet Notebook")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)

        self.nav_bar = QHBoxLayout()
        self.nav_bar.setSpacing(6)
        self.nav_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.left_btn = QPushButton("←")
        self.right_btn = QPushButton("→")
        self.count_label = QLabel()

        for btn in (self.left_btn, self.right_btn):
            btn.setFixedSize(28, 28)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 14px;
                    background: transparent;
                    border: 2px solid #888;
                    font-size: 15pt;
                    font-weight: bold;
                    padding: 0px;
                    min-width: 28px;
                    min-height: 28px;
                    max-width: 28px;
                    max-height: 28px;
                }
                QPushButton:hover {
                    background: #888;
                }
            """)

        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setMinimumWidth(44)
        self.count_label.setStyleSheet("font-weight: bold; font-size: 10pt; border-radius: 8px; padding: 3px 7px;")

        self.nav_bar.addWidget(self.left_btn)
        self.nav_bar.addWidget(self.count_label)
        self.nav_bar.addWidget(self.right_btn)
        self.layout.addLayout(self.nav_bar)

        self.label = RoundedImageLabel(radius=15)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.label)
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumHeight(300)
        self.scroll.setContentsMargins(0, 0, 0, 0)
        self.scroll.setStyleSheet("QScrollArea { margin:0px; padding:0px; background: transparent; border: none; }")
        self.layout.addWidget(self.scroll, stretch=1)

        self.warning = QLabel("⚠️ Put chart-1.png, chart-2.png, ... in this add‑on folder.")
        self.warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.warning)
        self.warning.hide()

        self.setMinimumWidth(750)
        self.setMinimumHeight(550)
        self.setStyleSheet(self._make_stylesheet())

        self.left_btn.clicked.connect(self.prev_chart)
        self.right_btn.clicked.connect(self.next_chart)

        self.update_image(_current_index)

    def _make_stylesheet(self):
        bg, fg = _anki_palette()
        return f"""
        QDialog {{
            background: {bg};
            color: {fg};
            border-radius: 14px;
        }}
        QLabel {{
            background: transparent;
            color: {fg};
        }}
        QScrollArea {{
            background: transparent;
            border-radius: 10px;
        }}
        """

    def update_image(self, idx: int):
        img = _image_path(idx)
        total = len(_chart_files)
        if not img:
            self.label.hide()
            self.scroll.hide()
            self.warning.show()
            self.count_label.setText("0 / 0")
            self.left_btn.setEnabled(False)
            self.right_btn.setEnabled(False)
            self.resize(300, 350)
        else:
            self.label.setPixmap(QPixmap(img))
            self.label.show()
            self.scroll.show()
            self.warning.hide()
            self.count_label.setText(f"{idx + 1} / {total}")
            self.left_btn.setEnabled(total > 1)
            self.right_btn.setEnabled(total > 1)
            # Optional: Resize dialog to fit image, but NOT the image itself
            # Remove or comment out this line if you want the dialog to stay fixed:
            # self.resize(self.label.pixmap().width() + 32, min(self.label.pixmap().height() + 70, 800))
            self.setStyleSheet(self._make_stylesheet())
            self.count_label.setStyleSheet(
                f"font-weight: bold; font-size: 10pt; border-radius: 8px; padding: 3px 7px; background: {_anki_palette()[0]}; color: {_anki_palette()[1]};"
            )

    def prev_chart(self):
        global _current_index
        if len(_chart_files) > 1:
            _current_index = (_current_index - 1) % len(_chart_files)
            self.update_image(_current_index)

    def next_chart(self):
        global _current_index
        if len(_chart_files) > 1:
            _current_index = (_current_index + 1) % len(_chart_files)
            self.update_image(_current_index)

    def keyPressEvent(self, event):
        try:
            esc = Qt.Key.Key_Escape
        except AttributeError:
            esc = Qt.Key_Escape
        num_text = event.text()
        if num_text.isdigit():
            num = int(num_text)
            idx = num - 1 if num != 0 else 9
            if 0 <= idx < len(_chart_files):
                global _current_index
                _current_index = idx
                self.update_image(_current_index)
                return
        if event.text().lower() == HOTKEY_LETTER.lower() or event.key() == esc:
            self.close()
            return
        if event.key() in [Qt.Key.Key_Left, Qt.Key.Key_A]:
            self.prev_chart()
            return
        if event.key() in [Qt.Key.Key_Right, Qt.Key.Key_D]:
            self.next_chart()
            return
        super().keyPressEvent(event)

def _build_dialog() -> QDialog:
    dlg = ChartDialog(mw.app.activeWindow() or mw)
    return dlg

def _toggle() -> None:
    global _dlg
    try:
        if _dlg and _dlg.isVisible():
            _dlg.hide()
        else:
            if _dlg is None:
                _dlg = _build_dialog()
            _dlg.update_image(_current_index)
            _dlg.show()
    except RuntimeError:
        _dlg = _build_dialog()
        _dlg.update_image(_current_index)
        _dlg.show()

def _add_shortcut(reviewer) -> None:
    key_seq = QKeySequence(f"{HOTKEY_LETTER}")
    sc = QShortcut(key_seq, reviewer.web)
    ctx = getattr(Qt, "ShortcutContext", Qt).WidgetWithChildrenShortcut
    sc.setContext(ctx)
    sc.activated.connect(_toggle)
    reviewer._cheatsheet_shortcut = sc

gui_hooks.reviewer_did_init.append(_add_shortcut)

_chart_files = _find_chart_files()
if not _chart_files:
    fallback = os.path.join(os.path.dirname(__file__), "chart.png")
    if os.path.exists(fallback):
        _chart_files = [fallback]

# --------- MENU ENTRY FOR HOTKEY SETTINGS ---------
def add_popsheet_menu():
    action = QAction("PopSheets", mw)
    action.triggered.connect(open_hotkey_dialog)
    mw.form.menuTools.addAction(action)

add_popsheet_menu()
# --------- END OF MENU ENTRY FOR HOTKEY SETTINGS ---------
