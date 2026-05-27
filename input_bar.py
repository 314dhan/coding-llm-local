from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTextEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent


class _GrowingTextEdit(QTextEdit):
    """QTextEdit that emits enter_pressed on Enter (not Shift+Enter)."""

    enter_pressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        ):
            self.enter_pressed.emit()
        else:
            super().keyPressEvent(event)


class InputBar(QWidget):
    """Auto-growing text input + Send button.

    Signals:
        message_submitted(str): emitted when user submits a non-empty message
    """

    message_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sending = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet("""
            InputBar {
                background: rgba(10, 10, 25, 230);
                border-top: 1px solid rgba(138, 43, 226, 64);
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        self._input = _GrowingTextEdit(self)
        self._input.setPlaceholderText(
            "Ask a coding question... (Enter to send, Shift+Enter for newline)"
        )
        self._input.setFixedHeight(36)
        self._input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._input.setStyleSheet("""
            QTextEdit {
                background: rgba(138, 43, 226, 20);
                border: 1px solid rgba(138, 43, 226, 60);
                border-radius: 8px;
                padding: 6px 10px;
                color: #ddd;
                font-size: 12px;
            }
            QTextEdit:focus { border-color: rgba(168, 85, 247, 140); }
        """)
        self._input.textChanged.connect(self._on_text_changed)
        self._input.enter_pressed.connect(self._submit)

        self._btn = QPushButton("Send")
        self._btn.setFixedSize(60, 36)
        self._btn.setEnabled(False)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #a855f7,stop:1 #6366f1);
                color: white; border: none; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #c084fc; }
            QPushButton:disabled { background: rgba(60,60,80,150); color: #555; }
        """)
        self._btn.clicked.connect(self._submit)

        layout.addWidget(self._input)
        layout.addWidget(self._btn)

    def _on_text_changed(self) -> None:
        has_text = bool(self._input.toPlainText().strip())
        self._btn.setEnabled(has_text and not self._sending)
        doc_h = int(self._input.document().size().height())
        self._input.setFixedHeight(max(36, min(100, doc_h + 12)))

    def _submit(self) -> None:
        text = self._input.toPlainText().strip()
        if not text or self._sending:
            return
        self._input.clear()
        self._input.setFixedHeight(36)
        self.message_submitted.emit(text)

    def set_sending(self, sending: bool) -> None:
        self._sending = sending
        self._input.setReadOnly(sending)
        has_text = bool(self._input.toPlainText().strip())
        self._btn.setEnabled(has_text and not sending)
