import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer
from pygments.formatters import HtmlFormatter


def parse_message_blocks(text: str) -> list[dict]:
    """Split a message into alternating text and fenced code blocks.

    Returns list of dicts:
        {"type": "text", "content": str}
        {"type": "code", "content": str, "lang": str}
    """
    if not text:
        return []

    blocks: list[dict] = []
    pattern = re.compile(r"```([^\n]*)\r?\n(.*?)```", re.DOTALL)
    last_end = 0

    for match in pattern.finditer(text):
        before = text[last_end:match.start()].strip()
        if before:
            blocks.append({"type": "text", "content": before})
        lang = match.group(1).strip() or "text"
        code = match.group(2).rstrip("\n")
        blocks.append({"type": "code", "content": code, "lang": lang})
        last_end = match.end()

    remaining = text[last_end:].strip()
    if remaining:
        blocks.append({"type": "text", "content": remaining})

    return blocks


def _highlight_code(code: str, lang: str) -> str:
    try:
        lexer = get_lexer_by_name(lang, stripall=True)
    except Exception:
        lexer = TextLexer()
    formatter = HtmlFormatter(style="monokai", noclasses=True)
    return highlight(code, lexer, formatter)


class CodeBlock(QWidget):
    """Dark code block with language label, Pygments highlighting, and copy button."""

    def __init__(self, code: str, lang: str, parent=None):
        super().__init__(parent)
        self._code = code
        self._build(code, lang)

    def _build(self, code: str, lang: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("codeHeader")
        header.setStyleSheet("""
            QWidget#codeHeader {
                background: rgba(138, 43, 226, 40);
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom: 1px solid rgba(138, 43, 226, 80);
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(8, 3, 8, 3)

        lang_lbl = QLabel(lang)
        lang_lbl.setStyleSheet("color: #888; font-size: 10px;")
        h_layout.addWidget(lang_lbl)
        h_layout.addStretch()

        copy_btn = QPushButton("⎘ copy")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton { color:#a855f7; background:transparent; border:none; font-size:10px; }
            QPushButton:hover { color:#c084fc; }
        """)
        copy_btn.clicked.connect(self._copy)
        h_layout.addWidget(copy_btn)
        layout.addWidget(header)

        view = QTextEdit()
        view.setReadOnly(True)
        view.setObjectName("codeView")
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        view.setStyleSheet("""
            QTextEdit#codeView {
                background: #0d0d1e;
                border: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                padding: 8px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                color: #f8f8f2;
            }
        """)
        view.setHtml(f"<div style='background:#0d0d1e'>{_highlight_code(code, lang)}</div>")
        view.document().setTextWidth(view.viewport().width())
        doc_h = int(view.document().size().height()) + 20
        view.setFixedHeight(max(doc_h, 40))
        layout.addWidget(view)

    def _copy(self) -> None:
        cb = QGuiApplication.clipboard()
        if cb:
            cb.setText(self._code)


class MessageBubble(QWidget):
    """One chat message — user (right-aligned) or assistant (left-aligned)."""

    _USER_STYLE = """
        QWidget#bubble {
            background: rgba(99, 102, 241, 50);
            border: 1px solid rgba(99, 102, 241, 80);
            border-radius: 10px; border-top-right-radius: 3px;
        }
    """
    _ASSISTANT_STYLE = """
        QWidget#bubble {
            background: rgba(138, 43, 226, 25);
            border: 1px solid rgba(138, 43, 226, 60);
            border-radius: 10px; border-top-left-radius: 3px;
        }
    """
    _ERROR_STYLE = """
        QWidget#bubble {
            background: rgba(220, 38, 38, 30);
            border: 1px solid rgba(220, 38, 38, 80);
            border-radius: 10px;
        }
    """

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._raw_text = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        role_lbl = QLabel("you" if role == "user" else "assistant")
        role_lbl.setStyleSheet("color:#555; font-size:10px; padding: 0 4px;")
        if role == "user":
            role_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        outer.addWidget(role_lbl)

        self._bubble = QWidget()
        self._bubble.setObjectName("bubble")
        self._bubble.setStyleSheet(
            self._USER_STYLE if role == "user" else self._ASSISTANT_STYLE
        )
        self._bubble_layout = QVBoxLayout(self._bubble)
        self._bubble_layout.setContentsMargins(10, 8, 10, 8)
        self._bubble_layout.setSpacing(6)

        self._stream_label = QLabel("")
        self._stream_label.setWordWrap(True)
        self._stream_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._stream_label.setStyleSheet("color:#ddd; font-size:12px;")
        self._bubble_layout.addWidget(self._stream_label)

        if role == "user":
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addStretch()
            row_layout.addWidget(self._bubble)
            outer.addWidget(row)
        else:
            outer.addWidget(self._bubble)

    def set_text(self, text: str) -> None:
        self._raw_text = text
        self._stream_label.setText(text)

    def append_token(self, token: str) -> None:
        self._raw_text += token
        self._stream_label.setText(self._raw_text)

    def finalize(self) -> None:
        """Re-render completed reply with code blocks and syntax highlighting."""
        while self._bubble_layout.count():
            item = self._bubble_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        blocks = parse_message_blocks(self._raw_text) or [
            {"type": "text", "content": self._raw_text}
        ]

        for block in blocks:
            if block["type"] == "text":
                lbl = QLabel(block["content"])
                lbl.setWordWrap(True)
                lbl.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )
                lbl.setStyleSheet("color:#ddd; font-size:12px;")
                self._bubble_layout.addWidget(lbl)
            else:
                self._bubble_layout.addWidget(
                    CodeBlock(block["content"], block["lang"])
                )

    def set_error(self, message: str) -> None:
        self._bubble.setStyleSheet(self._ERROR_STYLE)
        while self._bubble_layout.count():
            item = self._bubble_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        lbl = QLabel(f"⚠  {message}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color:#fca5a5; font-size:12px;")
        self._bubble_layout.addWidget(lbl)
