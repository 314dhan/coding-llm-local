from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent


_MODE_SEQUENCE = ["normal", "terse", "ultra"]
_MODE_DISPLAY = {"normal": "N", "terse": "T", "ultra": "U"}
_MODE_STYLES = {
    "normal": (
        "QPushButton { background:rgba(100,100,100,30); color:#777; "
        "border:1px solid rgba(100,100,100,40); font-size:10px; font-weight:bold; border-radius:4px; }"
        "QPushButton:hover { background:rgba(100,100,100,60); color:#aaa; }"
    ),
    "terse": (
        "QPushButton { background:rgba(99,102,241,30); color:#818cf8; "
        "border:1px solid rgba(99,102,241,50); font-size:10px; font-weight:bold; border-radius:4px; }"
        "QPushButton:hover { background:rgba(99,102,241,60); color:#a5b4fc; }"
    ),
    "ultra": (
        "QPushButton { background:rgba(245,158,11,30); color:#fbbf24; "
        "border:1px solid rgba(245,158,11,50); font-size:10px; font-weight:bold; border-radius:4px; }"
        "QPushButton:hover { background:rgba(245,158,11,60); color:#fcd34d; }"
    ),
}
_MODE_TIPS = {
    "normal": "Mode: Normal — full explanations (click to switch)",
    "terse":  "Mode: Terse — no preamble, direct answers (click to switch)",
    "ultra":  "Mode: Ultra — fragments, minimum tokens (click to switch)",
}

_PERSONALITY_SEQUENCE = ["pro", "direct", "mentor"]
_PERSONALITY_DISPLAY = {"pro": "P", "direct": "D", "mentor": "M"}
_PERSONALITY_STYLES = {
    "pro": (
        "QPushButton { background:rgba(6,182,212,30); color:#22d3ee; "
        "border:1px solid rgba(6,182,212,50); font-size:10px; font-weight:bold; border-radius:4px; }"
        "QPushButton:hover { background:rgba(6,182,212,60); color:#67e8f9; }"
    ),
    "direct": (
        "QPushButton { background:rgba(239,68,68,30); color:#f87171; "
        "border:1px solid rgba(239,68,68,50); font-size:10px; font-weight:bold; border-radius:4px; }"
        "QPushButton:hover { background:rgba(239,68,68,60); color:#fca5a5; }"
    ),
    "mentor": (
        "QPushButton { background:rgba(34,197,94,30); color:#4ade80; "
        "border:1px solid rgba(34,197,94,50); font-size:10px; font-weight:bold; border-radius:4px; }"
        "QPushButton:hover { background:rgba(34,197,94,60); color:#86efac; }"
    ),
}
_PERSONALITY_TIPS = {
    "pro":    "Personality: Professional — formal, precise, structured (click to switch)",
    "direct": "Personality: Direct — blunt, no hand-holding, answer only (click to switch)",
    "mentor": "Personality: Mentor — explains reasoning, teaches patterns (click to switch)",
}


class TitleBar(QWidget):
    """Drag handle with model label, response-mode toggle, and window-control buttons.

    Signals:
        clear_requested: trash icon clicked
        hide_requested:  minus icon clicked (hide to tray)
        quit_requested:  X icon clicked (quit app)
        mode_changed(str): new mode name when mode button clicked
    """

    clear_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    mode_changed = pyqtSignal(str)
    personality_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setObjectName("titleBar")
        self.setStyleSheet("""
            QWidget#titleBar {
                background: rgba(138, 43, 226, 38);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid rgba(138, 43, 226, 64);
            }
        """)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self._drag_pos = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 10, 0)

        icon = QLabel("◈")
        icon.setStyleSheet("color:#a855f7; font-size:14px;")
        layout.addWidget(icon)

        title = QLabel("Code Assistant")
        title.setStyleSheet("color:#ddd; font-size:12px; font-weight:600;")
        layout.addWidget(title)

        model = QLabel("qwen2.5-coder:7b")
        model.setStyleSheet("color:#555; font-size:10px; margin-left:4px;")
        layout.addWidget(model)

        self._current_mode = "normal"
        self._mode_btn = QPushButton(_MODE_DISPLAY["normal"])
        self._mode_btn.setFixedSize(24, 20)
        self._mode_btn.setToolTip(_MODE_TIPS["normal"])
        self._mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mode_btn.setStyleSheet(_MODE_STYLES["normal"])
        self._mode_btn.clicked.connect(self._cycle_mode)
        layout.addWidget(self._mode_btn)

        self._current_personality = "pro"
        self._personality_btn = QPushButton(_PERSONALITY_DISPLAY["pro"])
        self._personality_btn.setFixedSize(24, 20)
        self._personality_btn.setToolTip(_PERSONALITY_TIPS["pro"])
        self._personality_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._personality_btn.setStyleSheet(_PERSONALITY_STYLES["pro"])
        self._personality_btn.clicked.connect(self._cycle_personality)
        layout.addWidget(self._personality_btn)

        layout.addStretch()

        for text, signal_attr, tip in (
            ("🗑", "clear_requested", "Clear chat"),
            ("—", "hide_requested", "Hide to tray"),
            ("✕", "quit_requested", "Quit"),
        ):
            btn = QPushButton(text)
            btn.setFixedSize(24, 24)
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background:transparent; border:none; color:#555;
                    font-size:12px; border-radius:4px;
                }
                QPushButton:hover { background:rgba(255,255,255,20); color:#aaa; }
            """)
            btn.clicked.connect(getattr(self, signal_attr))
            layout.addWidget(btn)

    def _cycle_mode(self) -> None:
        idx = _MODE_SEQUENCE.index(self._current_mode)
        self._current_mode = _MODE_SEQUENCE[(idx + 1) % len(_MODE_SEQUENCE)]
        self._mode_btn.setText(_MODE_DISPLAY[self._current_mode])
        self._mode_btn.setToolTip(_MODE_TIPS[self._current_mode])
        self._mode_btn.setStyleSheet(_MODE_STYLES[self._current_mode])
        self.mode_changed.emit(self._current_mode)

    def _cycle_personality(self) -> None:
        idx = _PERSONALITY_SEQUENCE.index(self._current_personality)
        self._current_personality = _PERSONALITY_SEQUENCE[(idx + 1) % len(_PERSONALITY_SEQUENCE)]
        self._personality_btn.setText(_PERSONALITY_DISPLAY[self._current_personality])
        self._personality_btn.setToolTip(_PERSONALITY_TIPS[self._current_personality])
        self._personality_btn.setStyleSheet(_PERSONALITY_STYLES[self._current_personality])
        self.personality_changed.emit(self._current_personality)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self.window().frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            event.buttons() == Qt.MouseButton.LeftButton
            and not self._drag_pos.isNull()
        ):
            self.window().move(
                event.globalPosition().toPoint() - self._drag_pos
            )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)
