# Python GUI Transparent Overlay — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Flask + browser UI with a native PyQt6 transparent floating overlay window that calls Ollama qwen2.5-coder:7b directly, with system tray, global `Ctrl+Space` hotkey, and syntax-highlighted code blocks.

**Architecture:** A frameless, always-on-top `QWidget` with `WA_TranslucentBackground` renders the Midnight Purple glass overlay. An `OllamaWorker(QThread)` streams tokens from Ollama and emits signals to update the chat live. System tray (`QSystemTrayIcon`) and a daemon thread (`keyboard` library) toggle visibility. Old Flask files are deleted.

**Tech Stack:** Python 3.10+, PyQt6 6.6+, ollama (already installed), keyboard 0.13+, Pygments 2.17+, pytest 8+

---

## File Map

| File | Responsibility |
|------|----------------|
| `gui.py` | Entry point: QApplication, window, tray, hotkey |
| `window.py` | `OverlayWindow` — frameless translucent container, drag, resize |
| `title_bar.py` | `TitleBar` — drag zone, model label, clear/hide/close buttons |
| `chat_widget.py` | `ChatWidget` — scrollable message list |
| `message_bubble.py` | `parse_message_blocks()`, `MessageBubble`, `CodeBlock` |
| `input_bar.py` | `InputBar` — auto-grow textarea, send button |
| `ollama_client.py` | `OllamaWorker(QThread)`, history management functions |
| `hotkey.py` | `HotkeyListener` — global Ctrl+Space via `keyboard` library |
| `tray.py` | `TrayIcon(QSystemTrayIcon)` — tray icon + right-click menu |
| `requirements.txt` | Updated dependencies |
| `tests/test_message_parser.py` | Tests for `parse_message_blocks()` |
| `tests/test_ollama_client.py` | Tests for history management |

**Deleted:** `app.py`, `templates/index.html`

---

## Task 1: Project Setup

**Files:**
- Modify: `requirements.txt`
- Delete: `app.py`, `templates/index.html`
- Create: `tests/__init__.py`

- [ ] **Step 1: Update `requirements.txt`**

Replace entire contents with:
```
PyQt6>=6.6.0
ollama>=0.2.0
keyboard>=0.13.5
Pygments>=2.17.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Install new dependencies**

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

Expected: PyQt6, keyboard, Pygments install without errors.

- [ ] **Step 3: Delete old files**

```powershell
Remove-Item app.py
Remove-Item -Recurse templates
```

- [ ] **Step 4: Recreate tests directory with empty init**

```powershell
New-Item -ItemType Directory -Force tests
New-Item -ItemType File -Force tests\__init__.py
```

- [ ] **Step 5: Verify PyQt6 works**

```powershell
venv\Scripts\python.exe -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
```

Expected: `PyQt6 OK`

- [ ] **Step 6: Commit**

```powershell
git rm app.py templates/index.html
git add requirements.txt tests\__init__.py
git commit -m "chore: replace Flask deps with PyQt6, keyboard, Pygments"
```

---

## Task 2: Message Parser

**Files:**
- Create: `message_bubble.py` (parser only — widgets added in Tasks 4–5)
- Create: `tests/test_message_parser.py`

The parser splits raw text into a list of `{"type": "text"|"code", "content": str, "lang": str}` dicts.

- [ ] **Step 1: Write failing tests in `tests/test_message_parser.py`**

```python
from message_bubble import parse_message_blocks


def test_plain_text_only():
    blocks = parse_message_blocks("Hello world")
    assert blocks == [{"type": "text", "content": "Hello world"}]


def test_single_code_block():
    text = "Use this:\n```python\nprint('hi')\n```\nDone."
    blocks = parse_message_blocks(text)
    assert len(blocks) == 3
    assert blocks[0] == {"type": "text", "content": "Use this:"}
    assert blocks[1] == {"type": "code", "content": "print('hi')", "lang": "python"}
    assert blocks[2] == {"type": "text", "content": "Done."}


def test_code_block_no_lang():
    blocks = parse_message_blocks("```\nx = 1\n```")
    assert blocks == [{"type": "code", "content": "x = 1", "lang": "text"}]


def test_empty_string():
    assert parse_message_blocks("") == []


def test_multiple_code_blocks():
    text = "First:\n```py\na = 1\n```\nSecond:\n```js\nconsole.log(1)\n```"
    blocks = parse_message_blocks(text)
    assert len(blocks) == 4
    assert blocks[1]["lang"] == "py"
    assert blocks[3]["lang"] == "js"


def test_ignores_empty_text_segments():
    blocks = parse_message_blocks("```python\ncode\n```")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "code"


def test_strips_surrounding_whitespace():
    blocks = parse_message_blocks("  hello  ")
    assert blocks[0]["content"] == "hello"
```

- [ ] **Step 2: Run — verify FAIL**

```powershell
venv\Scripts\python.exe -m pytest tests\test_message_parser.py -v
```

Expected: `ModuleNotFoundError: No module named 'message_bubble'`

- [ ] **Step 3: Create `message_bubble.py` with parser only**

```python
import re


def parse_message_blocks(text: str) -> list[dict]:
    """Split a message into alternating text and fenced code blocks.

    Returns list of dicts:
        {"type": "text", "content": str}
        {"type": "code", "content": str, "lang": str}
    """
    if not text:
        return []

    blocks: list[dict] = []
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
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
```

- [ ] **Step 4: Run — verify PASS**

```powershell
venv\Scripts\python.exe -m pytest tests\test_message_parser.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add message_bubble.py tests\test_message_parser.py tests\__init__.py
git commit -m "feat: add message block parser with tests"
```

---

## Task 3: OllamaWorker + History

**Files:**
- Create: `ollama_client.py`
- Create: `tests/test_ollama_client.py`

- [ ] **Step 1: Write failing tests in `tests/test_ollama_client.py`**

```python
import pytest
import ollama_client as oc


@pytest.fixture(autouse=True)
def reset():
    oc.clear_history()
    yield
    oc.clear_history()


def test_append_and_get():
    oc.append_to_history("user", "hello")
    oc.append_to_history("assistant", "hi")
    h = oc.get_history()
    assert h == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]


def test_history_capped():
    for i in range(oc.MAX_HISTORY + 5):
        oc.append_to_history("user", f"msg {i}")
    assert len(oc.get_history()) == oc.MAX_HISTORY


def test_oldest_dropped_first():
    for i in range(oc.MAX_HISTORY + 2):
        oc.append_to_history("user", f"msg {i}")
    assert oc.get_history()[0]["content"] == "msg 2"


def test_clear():
    oc.append_to_history("user", "x")
    oc.clear_history()
    assert oc.get_history() == []


def test_remove_last():
    oc.append_to_history("user", "first")
    oc.append_to_history("user", "second")
    oc.remove_last_message()
    assert len(oc.get_history()) == 1
    assert oc.get_history()[0]["content"] == "first"


def test_remove_last_empty_is_safe():
    oc.remove_last_message()  # must not raise
    assert oc.get_history() == []


def test_build_messages_has_system_prompt():
    oc.append_to_history("user", "what is python?")
    msgs = oc.build_messages()
    assert msgs[0]["role"] == "system"
    assert "coding assistant" in msgs[0]["content"].lower()
    assert msgs[1] == {"role": "user", "content": "what is python?"}


def test_build_messages_empty_history():
    msgs = oc.build_messages()
    assert len(msgs) == 1
    assert msgs[0]["role"] == "system"
```

- [ ] **Step 2: Run — verify FAIL**

```powershell
venv\Scripts\python.exe -m pytest tests\test_ollama_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'ollama_client'`

- [ ] **Step 3: Create `ollama_client.py`**

```python
from PyQt6.QtCore import QThread, pyqtSignal
import ollama

SYSTEM_PROMPT = (
    "You are an expert coding assistant. Help the user with any programming question "
    "— explain code, debug issues, write code snippets. Be concise and clear. "
    "Use code blocks for all code."
)
MODEL = "qwen2.5-coder:7b"
MAX_HISTORY = 20

_history: list[dict] = []


def get_history() -> list[dict]:
    return list(_history)


def append_to_history(role: str, content: str) -> None:
    _history.append({"role": role, "content": content})
    while len(_history) > MAX_HISTORY:
        _history.pop(0)


def clear_history() -> None:
    _history.clear()


def remove_last_message() -> None:
    if _history:
        _history.pop()


def build_messages() -> list[dict]:
    return [{"role": "system", "content": SYSTEM_PROMPT}] + list(_history)


class OllamaWorker(QThread):
    """Streams a response from Ollama in a background thread.

    Signals:
        token_received(str): one streamed token
        finished(str):       full reply text when done
        error(str):          user-friendly error message
    """

    token_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, messages: list[dict], parent=None):
        super().__init__(parent)
        self._messages = messages

    def run(self) -> None:
        full_reply = ""
        try:
            stream = ollama.chat(model=MODEL, messages=self._messages, stream=True)
            for chunk in stream:
                token = chunk["message"]["content"]
                full_reply += token
                self.token_received.emit(token)
            self.finished.emit(full_reply)
        except ollama.ResponseError as e:
            msg = str(e).lower()
            if "not found" in msg or "pull" in msg:
                self.error.emit(f"Model '{MODEL}' not found.\nRun: ollama pull {MODEL}")
            else:
                self.error.emit(f"Model error: {e}")
        except Exception as e:
            msg = str(e).lower()
            if any(w in msg for w in ("connection", "refused", "connect")):
                self.error.emit("Ollama isn't running.\nStart it with: ollama serve")
            else:
                self.error.emit(f"Unexpected error: {e}")
```

- [ ] **Step 4: Run — verify PASS**

```powershell
venv\Scripts\python.exe -m pytest tests\test_ollama_client.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add ollama_client.py tests\test_ollama_client.py
git commit -m "feat: add OllamaWorker and history management with tests"
```

---

## Task 4: CodeBlock Widget

**Files:**
- Modify: `message_bubble.py` — append `CodeBlock` class

- [ ] **Step 1: Append to `message_bubble.py`** (after the `parse_message_blocks` function)

```python
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

        # Header
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

        # Code body
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

        # Fix height to content
        view.document().setTextWidth(view.viewport().width())
        doc_h = int(view.document().size().height()) + 20
        view.setFixedHeight(max(doc_h, 40))
        layout.addWidget(view)

    def _copy(self) -> None:
        cb = QGuiApplication.clipboard()
        if cb:
            cb.setText(self._code)
```

- [ ] **Step 2: Run existing tests — verify still PASS**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add message_bubble.py
git commit -m "feat: add CodeBlock widget with syntax highlighting and copy button"
```

---

## Task 5: MessageBubble Widget

**Files:**
- Modify: `message_bubble.py` — append `MessageBubble` class

- [ ] **Step 1: Append `MessageBubble` to `message_bubble.py`**

```python
class MessageBubble(QWidget):
    """One chat message — user (right-aligned) or assistant (left-aligned).

    For assistant messages:
      - append_token(str) accumulates streaming text as plain label
      - finalize()        re-renders the complete text with code blocks
      - set_error(str)    shows a red error state
    For user messages:
      - set_text(str)     sets the display text (not streamed)
    """

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

        # Role label
        role_lbl = QLabel("you" if role == "user" else "assistant")
        role_lbl.setStyleSheet("color:#555; font-size:10px; padding: 0 4px;")
        if role == "user":
            role_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        outer.addWidget(role_lbl)

        # Bubble
        self._bubble = QWidget()
        self._bubble.setObjectName("bubble")
        self._bubble.setStyleSheet(
            self._USER_STYLE if role == "user" else self._ASSISTANT_STYLE
        )
        self._bubble_layout = QVBoxLayout(self._bubble)
        self._bubble_layout.setContentsMargins(10, 8, 10, 8)
        self._bubble_layout.setSpacing(6)

        # Streaming / plain label (replaced by finalize())
        self._stream_label = QLabel("")
        self._stream_label.setWordWrap(True)
        self._stream_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._stream_label.setStyleSheet("color:#ddd; font-size:12px;")
        self._bubble_layout.addWidget(self._stream_label)

        # Align user messages right
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
        # Clear bubble contents
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
```

- [ ] **Step 2: Run all tests**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add message_bubble.py
git commit -m "feat: add MessageBubble with streaming, finalize, and error state"
```

---

## Task 6: ChatWidget

**Files:**
- Create: `chat_widget.py`

- [ ] **Step 1: Create `chat_widget.py`**

```python
from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from message_bubble import MessageBubble


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
        """Add an empty assistant bubble ready for streaming. Returns bubble."""
        bubble = MessageBubble("assistant")
        self._insert_bubble(bubble)
        return bubble

    def clear(self) -> None:
        while self._layout.count() > 1:  # keep the stretch at index 0
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
        # Insert before the trailing stretch
        pos = max(0, self._layout.count() - 1)
        self._layout.insertWidget(pos, bubble)
        self.scroll_to_bottom()
```

- [ ] **Step 2: Run all tests**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add chat_widget.py
git commit -m "feat: add ChatWidget scrollable message list"
```

---

## Task 7: InputBar

**Files:**
- Create: `input_bar.py`

- [ ] **Step 1: Create `input_bar.py`**

```python
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
```

- [ ] **Step 2: Run all tests**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add input_bar.py
git commit -m "feat: add InputBar with auto-grow and Enter-to-send"
```

---

## Task 8: TitleBar

**Files:**
- Create: `title_bar.py`

- [ ] **Step 1: Create `title_bar.py`**

```python
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
                QPushButton { background:transparent; border:none; color:#555; font-size:12px; border-radius:4px; }
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
```

- [ ] **Step 2: Run all tests**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add title_bar.py
git commit -m "feat: add TitleBar with drag and control buttons"
```

---

## Task 9: OverlayWindow

**Files:**
- Create: `window.py`

- [ ] **Step 1: Create `window.py`**

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QPaintEvent

from title_bar import TitleBar
from chat_widget import ChatWidget
from input_bar import InputBar
import ollama_client


class _ResizeGrip(QWidget):
    """16x16 bottom-right corner widget — drag to resize the parent window."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self._active = False
        self._start_pos = QPoint()
        self._start_size = QSize()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = True
            self._start_pos = event.globalPosition().toPoint()
            self._start_size = self.window().size()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._active:
            delta = event.globalPosition().toPoint() - self._start_pos
            win = self.window()
            win.resize(
                max(win.minimumWidth(), self._start_size.width() + delta.x()),
                max(win.minimumHeight(), self._start_size.height() + delta.y()),
            )
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._active = False
        event.accept()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setPen(QPen(QColor(138, 43, 226, 110), 1))
        for offset in (4, 8, 12):
            painter.drawLine(offset, 15, 15, offset)


class OverlayWindow(QWidget):
    """Frameless, always-on-top, translucent overlay window.

    Visual structure:
        OverlayWindow (WA_TranslucentBackground — paints purple glow)
          └── QFrame#mainFrame  (dark rounded glass background + border)
               ├── TitleBar
               ├── ChatWidget   (stretches)
               └── InputBar
        _ResizeGrip (absolute, always on top)
    """

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

        self._grip = _ResizeGrip(self)
        self._grip.raise_()
        self._reposition_grip()

    # ------------------------------------------------------------------ #
    # UI setup                                                             #
    # ------------------------------------------------------------------ #

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
        self.input_bar.message_submitted.connect(self._on_message_submitted)

    # ------------------------------------------------------------------ #
    # Slots                                                                #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # Painting and resizing                                                #
    # ------------------------------------------------------------------ #

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i in range(1, 4):
            painter.setPen(QPen(QColor(138, 43, 226, 30), i * 2))
            painter.setBrush(QBrush(Qt.GlobalColor.transparent))
            painter.drawRoundedRect(self.rect().adjusted(i, i, -i, -i), 12, 12)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_grip()

    def _reposition_grip(self) -> None:
        self._grip.move(self.width() - 16, self.height() - 16)
        self._grip.raise_()

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
```

- [ ] **Step 2: Run all tests**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add window.py
git commit -m "feat: add OverlayWindow — frameless translucent overlay with drag and resize"
```

---

## Task 10: TrayIcon

**Files:**
- Create: `tray.py`

- [ ] **Step 1: Create `tray.py`**

```python
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush
from PyQt6.QtCore import Qt


def _make_icon() -> QIcon:
    px = QPixmap(32, 32)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor("#a855f7")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(4, 4, 24, 24)
    p.setBrush(QBrush(QColor("#0d0d1e")))
    p.drawEllipse(12, 12, 8, 8)
    p.end()
    return QIcon(px)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with Show/Hide and Quit menu entries.
    Double-clicking the icon also toggles visibility.
    """

    def __init__(self, window, app: QApplication):
        super().__init__(_make_icon(), app)
        self._window = window
        self.setToolTip("Code Assistant  (Ctrl+Space)")

        menu = QMenu()
        menu.addAction("Show / Hide").triggered.connect(window.toggle_visibility)
        menu.addSeparator()
        menu.addAction("Quit").triggered.connect(QApplication.quit)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._window.toggle_visibility()
```

- [ ] **Step 2: Run all tests**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add tray.py
git commit -m "feat: add TrayIcon with programmatic purple icon and Show/Quit menu"
```

---

## Task 11: HotkeyListener

**Files:**
- Create: `hotkey.py`

- [ ] **Step 1: Create `hotkey.py`**

```python
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class _Bridge(QObject):
    """Emits a Qt signal safely from a non-Qt thread."""
    triggered = pyqtSignal()


class HotkeyListener:
    """Registers Ctrl+Space as a global hotkey to toggle the overlay window.

    Runs in a daemon thread. Logs a warning and continues gracefully if the
    `keyboard` library is unavailable or hotkey registration fails.

    To change the hotkey, update HOTKEY below.
    """

    HOTKEY = "ctrl+space"

    def __init__(self, window):
        self._bridge = _Bridge()
        self._bridge.triggered.connect(window.toggle_visibility)

    def start(self) -> None:
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self) -> None:
        try:
            import keyboard
            keyboard.add_hotkey(self.HOTKEY, self._bridge.triggered.emit)
            keyboard.wait()
        except ImportError:
            print("Warning: `keyboard` library not installed — hotkey disabled.")
        except Exception as e:
            print(f"Warning: Could not register hotkey '{self.HOTKEY}': {e}")
```

- [ ] **Step 2: Run all tests**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add hotkey.py
git commit -m "feat: add HotkeyListener for global Ctrl+Space toggle"
```

---

## Task 12: Entry Point

**Files:**
- Create: `gui.py`

- [ ] **Step 1: Create `gui.py`**

```python
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from window import OverlayWindow
from tray import TrayIcon
from hotkey import HotkeyListener


def main() -> None:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # stay alive when window is hidden

    window = OverlayWindow()
    tray = TrayIcon(window, app)
    tray.show()

    HotkeyListener(window).start()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run all tests one final time**

```powershell
venv\Scripts\python.exe -m pytest tests\ -v
```

Expected: All 15 tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add gui.py
git commit -m "feat: add gui.py entry point — wires window, tray, and hotkey"
```

---

## Task 13: Manual Smoke Test

**Files:** None.

- [ ] **Step 1: Start Ollama** (separate terminal, leave running)

```powershell
ollama serve
```

- [ ] **Step 2: Launch the app**

```powershell
venv\Scripts\activate
python gui.py
```

Expected: Semi-transparent dark purple overlay window on screen. Purple circle in system tray.

- [ ] **Step 3: Drag** — click and drag the title bar.
Expected: Window moves freely.

- [ ] **Step 4: Resize** — drag the bottom-right grip.
Expected: Window resizes; minimum 280×300 enforced.

- [ ] **Step 5: Send a message** — type `how do I reverse a list in python?` + Enter.
Expected: User bubble appears; assistant tokens stream in live; finalized reply shows syntax-highlighted code block with `⎘ copy` button.

- [ ] **Step 6: Copy button** — click `⎘ copy` on a code block.
Expected: Code on clipboard (paste into Notepad to verify).

- [ ] **Step 7: Hide to tray** — click `—`.
Expected: Window hides; tray icon remains.

- [ ] **Step 8: Global hotkey** — press `Ctrl+Space`.
Expected: Window reappears.

- [ ] **Step 9: Tray right-click** — right-click the tray icon.
Expected: Menu with "Show / Hide" and "Quit".

- [ ] **Step 10: Clear chat** — click `🗑`.
Expected: All messages removed.

- [ ] **Step 11: Error state** — stop Ollama (`Ctrl+C`), then send a message.
Expected: Red error bubble: "Ollama isn't running. Start it with: ollama serve".

- [ ] **Step 12: Final commit**

```powershell
git add .
git commit -m "feat: Python GUI transparent overlay complete"
```

---

## Quick Reference

```powershell
# Activate venv
venv\Scripts\activate

# Start Ollama (keep running in its own terminal)
ollama serve

# Run the app
python gui.py

# Run tests
venv\Scripts\python.exe -m pytest tests\ -v
```
