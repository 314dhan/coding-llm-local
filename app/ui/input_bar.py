from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTextEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

from app.voice import VoiceWorker

_SEND_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #a855f7,stop:1 #6366f1);
        color: white; border: none; border-radius: 8px;
        font-size: 12px; font-weight: bold;
    }
    QPushButton:hover { background: #c084fc; }
    QPushButton:disabled { background: rgba(60,60,80,150); color: #555; }
"""

_MIC_IDLE = """
    QPushButton {
        background: rgba(138, 43, 226, 30);
        color: #a855f7; border: 1px solid rgba(138, 43, 226, 60);
        border-radius: 8px; font-size: 14px;
    }
    QPushButton:hover { background: rgba(138, 43, 226, 70); }
    QPushButton:disabled { background: rgba(60,60,80,100); color: #444; }
"""

_MIC_RECORDING = """
    QPushButton {
        background: rgba(220, 38, 38, 90);
        color: #f87171; border: 1px solid rgba(220, 38, 38, 80);
        border-radius: 8px; font-size: 14px;
    }
    QPushButton:hover { background: rgba(220, 38, 38, 130); }
"""

_MIC_BUSY = """
    QPushButton {
        background: rgba(234, 179, 8, 30);
        color: #fbbf24; border: 1px solid rgba(234, 179, 8, 50);
        border-radius: 8px; font-size: 11px;
    }
"""


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
    """Auto-growing text input + Send button + mic button.

    Signals:
        message_submitted(str): emitted when user submits a non-empty message
    """

    message_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sending = False
        self._voice_worker: VoiceWorker | None = None
        self._voice_state = "idle"
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

        self._mic_btn = QPushButton("🎤")
        self._mic_btn.setFixedSize(36, 36)
        self._mic_btn.setToolTip("Voice input — EN / ID / JA auto-detected")
        self._mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mic_btn.setStyleSheet(_MIC_IDLE)
        self._mic_btn.clicked.connect(self._toggle_voice)

        self._btn = QPushButton("Send")
        self._btn.setFixedSize(60, 36)
        self._btn.setEnabled(False)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setStyleSheet(_SEND_STYLE)
        self._btn.clicked.connect(self._submit)

        layout.addWidget(self._input)
        layout.addWidget(self._mic_btn)
        layout.addWidget(self._btn)

    def _toggle_voice(self) -> None:
        if self._voice_state in ("loading", "transcribing"):
            return
        if self._voice_state == "recording":
            self._voice_worker.stop_recording()
        else:
            self._start_voice()

    def _start_voice(self) -> None:
        worker = VoiceWorker()
        worker.state_changed.connect(self._on_voice_state)
        worker.transcription_ready.connect(self._on_transcription)
        worker.error_occurred.connect(self._on_voice_error)
        worker.finished.connect(worker.deleteLater)
        self._voice_worker = worker
        worker.start_recording()

    def _on_voice_state(self, state: str) -> None:
        self._voice_state = state
        if state == "loading":
            self._mic_btn.setText("···")
            self._mic_btn.setEnabled(False)
            self._mic_btn.setStyleSheet(_MIC_BUSY)
            self._mic_btn.setToolTip("Loading Whisper model (first time only)...")
        elif state == "recording":
            self._mic_btn.setText("⏹")
            self._mic_btn.setEnabled(True)
            self._mic_btn.setStyleSheet(_MIC_RECORDING)
            self._mic_btn.setToolTip("Recording — click to stop")
        elif state == "transcribing":
            self._mic_btn.setText("···")
            self._mic_btn.setEnabled(False)
            self._mic_btn.setStyleSheet(_MIC_BUSY)
            self._mic_btn.setToolTip("Transcribing...")
        else:
            self._mic_btn.setText("🎤")
            self._mic_btn.setEnabled(True)
            self._mic_btn.setStyleSheet(_MIC_IDLE)
            self._mic_btn.setToolTip("Voice input — EN / ID / JA auto-detected")

    def _on_transcription(self, text: str) -> None:
        current = self._input.toPlainText().strip()
        self._input.setPlainText((current + " " + text).strip() if current else text)
        cursor = self._input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._input.setTextCursor(cursor)
        self._input.setFocus()

    def _on_voice_error(self, msg: str) -> None:
        self._mic_btn.setToolTip(f"Error: {msg}")

    def _on_text_changed(self) -> None:
        has_text = bool(self._input.toPlainText().strip())
        self._btn.setEnabled(has_text and not self._sending)
        doc_h = int(self._input.document().size().height())
        self._input.setFixedHeight(max(36, min(100, doc_h + 12)))

    def _submit(self) -> None:
        text = self._input.toPlainText().strip()
        if not text or self._sending:
            return
        if self._voice_state == "recording" and self._voice_worker:
            self._voice_worker.stop_recording()
        self._input.clear()
        self._input.setFixedHeight(36)
        self.message_submitted.emit(text)

    def set_sending(self, sending: bool) -> None:
        self._sending = sending
        self._input.setReadOnly(sending)
        has_text = bool(self._input.toPlainText().strip())
        self._btn.setEnabled(has_text and not sending)
