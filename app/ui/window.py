import ctypes
import sys

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QPaintEvent

from app.ui.title_bar import TitleBar
from app.ui.chat_widget import ChatWidget
from app.ui.input_bar import InputBar
import app.client as ollama_client

_WDA_EXCLUDEFROMCAPTURE = 0x00000011
_RESIZE_MARGIN = 8


class _EdgeGrip(QWidget):
    """Invisible resize handle along one or two edges of the parent window."""

    _CURSORS = {
        'l':  Qt.CursorShape.SizeHorCursor,
        'r':  Qt.CursorShape.SizeHorCursor,
        't':  Qt.CursorShape.SizeVerCursor,
        'b':  Qt.CursorShape.SizeVerCursor,
        'tl': Qt.CursorShape.SizeFDiagCursor,
        'br': Qt.CursorShape.SizeFDiagCursor,
        'tr': Qt.CursorShape.SizeBDiagCursor,
        'bl': Qt.CursorShape.SizeBDiagCursor,
    }

    def __init__(self, parent: QWidget, dirs: str):
        super().__init__(parent)
        self._dirs = dirs
        self._active = False
        self._start_pos = QPoint()
        self._start_geom: QRect = QRect()
        self.setCursor(self._CURSORS.get(dirs, Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = True
            self._start_pos = event.globalPosition().toPoint()
            self._start_geom = self.window().geometry()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._active:
            return
        delta = event.globalPosition().toPoint() - self._start_pos
        win = self.window()
        g = self._start_geom
        min_w, min_h = win.minimumWidth(), win.minimumHeight()

        x, y, w, h = g.x(), g.y(), g.width(), g.height()

        if 'l' in self._dirs:
            new_w = max(min_w, w - delta.x())
            x = x + w - new_w
            w = new_w
        elif 'r' in self._dirs:
            w = max(min_w, w + delta.x())

        if 't' in self._dirs:
            new_h = max(min_h, h - delta.y())
            y = y + h - new_h
            h = new_h
        elif 'b' in self._dirs:
            h = max(min_h, h + delta.y())

        win.setGeometry(x, y, w, h)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._active = False
        event.accept()


class OverlayWindow(QWidget):
    """Frameless, always-on-top, translucent overlay window."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(380, 520)
        self.setMinimumSize(280, 300)

        self._setup_ui()
        self._setup_connections()
        self._setup_grips()

        if sys.platform == "win32":
            ctypes.windll.user32.SetWindowDisplayAffinity(
                int(self.winId()), _WDA_EXCLUDEFROMCAPTURE
            )

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._frame = QFrame(self)
        self._frame.setObjectName("mainFrame")
        self._frame.setStyleSheet("""
            QFrame#mainFrame {
                background: rgba(10, 10, 25, 217);
                border: 1px solid rgba(138, 43, 226, 100);
                border-radius: 12px;
            }
        """)

        frame_layout = QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        self.title_bar = TitleBar(self._frame)
        self.chat_widget = ChatWidget(self._frame)
        self.input_bar = InputBar(self._frame)

        frame_layout.addWidget(self.title_bar)
        frame_layout.addWidget(self.chat_widget, 1)
        frame_layout.addWidget(self.input_bar)

        outer.addWidget(self._frame)

    def _setup_connections(self) -> None:
        self.title_bar.clear_requested.connect(self._on_clear)
        self.title_bar.hide_requested.connect(self.hide)
        self.title_bar.quit_requested.connect(self._quit)
        self.title_bar.mode_changed.connect(ollama_client.set_mode)
        self.title_bar.personality_changed.connect(ollama_client.set_personality)
        self.input_bar.message_submitted.connect(self._on_message_submitted)

    def _setup_grips(self) -> None:
        self._grips = {d: _EdgeGrip(self, d) for d in ('l', 'r', 't', 'b', 'tl', 'tr', 'bl', 'br')}
        self._reposition_grips()

    def _reposition_grips(self) -> None:
        w, h = self.width(), self.height()
        m = _RESIZE_MARGIN
        self._grips['l'].setGeometry(0, m, m, h - 2 * m)
        self._grips['r'].setGeometry(w - m, m, m, h - 2 * m)
        self._grips['t'].setGeometry(m, 0, w - 2 * m, m)
        self._grips['b'].setGeometry(m, h - m, w - 2 * m, m)
        self._grips['tl'].setGeometry(0, 0, m, m)
        self._grips['tr'].setGeometry(w - m, 0, m, m)
        self._grips['bl'].setGeometry(0, h - m, m, m)
        self._grips['br'].setGeometry(w - m, h - m, m, m)
        for grip in self._grips.values():
            grip.raise_()

    def _on_clear(self) -> None:
        self.chat_widget.clear()
        ollama_client.clear_history()

    def _quit(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def _on_message_submitted(self, text: str) -> None:
        self.chat_widget.add_user_message(text)
        ollama_client.append_to_history("user", text)
        self.input_bar.set_sending(True)

        bubble = self.chat_widget.add_assistant_message()
        messages = ollama_client.build_messages()

        self._worker = ollama_client.OllamaWorker(messages)
        self._worker.token_received.connect(bubble.append_token)
        self._worker.token_received.connect(
            lambda _: self.chat_widget.scroll_to_bottom()
        )
        self._worker.finished.connect(
            lambda reply: self._on_finished(bubble, reply)
        )
        self._worker.error.connect(
            lambda msg: self._on_error(bubble, msg)
        )
        self._worker.start()

    def _on_finished(self, bubble, reply: str) -> None:
        ollama_client.append_to_history("assistant", reply)
        bubble.finalize()
        self.input_bar.set_sending(False)
        self.chat_widget.scroll_to_bottom()

    def _on_error(self, bubble, message: str) -> None:
        ollama_client.remove_last_message()
        bubble.set_error(message)
        self.input_bar.set_sending(False)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i in range(1, 4):
            painter.setPen(QPen(QColor(138, 43, 226, 30), i * 2))
            painter.setBrush(QBrush(Qt.GlobalColor.transparent))
            painter.drawRoundedRect(self.rect().adjusted(i, i, -i, -i), 12, 12)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_grips()

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
