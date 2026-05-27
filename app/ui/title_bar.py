from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent


class TitleBar(QWidget):
    """Drag handle with model label and window-control buttons.

    Signals:
        clear_requested: trash icon clicked
        hide_requested:  minus icon clicked (hide to tray)
        quit_requested:  X icon clicked (quit app)
    """

    clear_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    quit_requested = pyqtSignal()

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
