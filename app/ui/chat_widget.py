from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

from app.ui.message_bubble import MessageBubble


class ChatWidget(QScrollArea):
    """Scrollable vertically-stacked list of MessageBubble widgets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(138, 43, 226, 120); border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(10)
        self._layout.addStretch()
        self.setWidget(self._container)

        # Welcome message
        welcome = MessageBubble("assistant")
        welcome.set_text(
            "Hi! I'm your coding assistant powered by qwen2.5-coder.\n"
            "Ask me anything — debugging, explanations, code snippets."
        )
        welcome.finalize()
        self._insert_bubble(welcome)

    def add_user_message(self, text: str) -> MessageBubble:
        bubble = MessageBubble("user")
        bubble.set_text(text)
        self._insert_bubble(bubble)
        return bubble

    def add_assistant_message(self) -> MessageBubble:
        """Add an empty assistant bubble ready for streaming. Returns the bubble."""
        bubble = MessageBubble("assistant")
        self._insert_bubble(bubble)
        return bubble

    def clear(self) -> None:
        while self._layout.count() > 1:  # keep trailing stretch
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def scroll_to_bottom(self) -> None:
        QTimer.singleShot(
            50,
            lambda: self.verticalScrollBar().setValue(
                self.verticalScrollBar().maximum()
            ),
        )

    def _insert_bubble(self, bubble: MessageBubble) -> None:
        pos = max(0, self._layout.count() - 1)
        self._layout.insertWidget(pos, bubble)
        self.scroll_to_bottom()
