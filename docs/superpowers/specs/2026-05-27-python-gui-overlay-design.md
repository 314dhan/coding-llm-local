# Python GUI Transparent Overlay — Design Spec

**Date:** 2026-05-27
**Stack:** PyQt6 + Ollama (qwen2.5-coder:7b) + Pygments + keyboard

---

## Overview

Replace the existing Flask + browser UI with a native Python GUI: a semi-transparent, always-on-top floating overlay window in a Midnight Purple style. The window is draggable, resizable, and hides to the system tray. A global hotkey (`Ctrl+Space`) toggles show/hide. The assistant calls Ollama directly — no Flask server, no browser.

---

## Architecture

```
gui.py                     ← entry point: launches QApplication + tray + window
├── window.py              ← frameless, translucent, always-on-top QWidget
│   ├── title_bar.py       ← drag handle, model label, clear/hide/close buttons
│   ├── chat_widget.py     ← QScrollArea with scrollable message list
│   │   └── message_bubble.py  ← user bubble | assistant bubble (plain text + code blocks)
│   └── input_bar.py       ← QTextEdit (auto-grow) + Send button
├── ollama_client.py       ← calls ollama.chat() in a QThread, emits tokens via signal
├── hotkey.py              ← global Ctrl+Space listener using `keyboard` library
└── tray.py                ← QSystemTrayIcon, right-click menu (Show / Quit)
```

**Removed:** `app.py`, `templates/`, Flask, anthropic SDK, pytest suite.

---

## Window Behaviour

| Property | Value |
|----------|-------|
| Default size | 380 × 520 px |
| Minimum size | 280 × 300 px |
| Window flags | `FramelessWindowHint \| WindowStaysOnTopHint` |
| Background | `WA_TranslucentBackground` — semi-transparent dark purple glass |
| Drag | Click + drag on title bar moves the window |
| Resize | Bottom-right corner grip resizes the window |
| Hide | `—` button hides to system tray (app keeps running) |
| Close | `✕` button quits the app entirely |
| Global hotkey | `Ctrl+Space` — toggles show/hide from anywhere on screen |

---

## Visual Style

- **Background:** `rgba(10, 10, 25, 0.85)` — dark near-black with purple tint
- **Accent colour:** `#a855f7` (purple) and `#6366f1` (indigo)
- **Border:** `1px solid rgba(138, 43, 226, 0.4)` — subtle purple glow border
- **Corner radius:** 12px on the window, 10px on message bubbles
- **Title bar:** `rgba(138, 43, 226, 0.15)` — slightly lighter purple strip
- **Code blocks:** dark background `#0d0d1e`, purple-tinted header bar, language label + copy button
- **Fonts:** Segoe UI for chat text; Consolas/Courier New for code

---

## Components

### `gui.py`
Entry point. Creates `QApplication`, instantiates `OverlayWindow` and `TrayIcon`, starts the global hotkey listener in a background thread, and calls `app.exec()`.

### `window.py` — `OverlayWindow(QWidget)`
The main transparent overlay widget. Sets window flags and background attribute. Lays out `TitleBar`, `ChatWidget`, and `InputBar` vertically. Implements `mousePressEvent` / `mouseMoveEvent` for drag, and a `ResizeGrip` in the bottom-right corner for resize.

### `title_bar.py` — `TitleBar(QWidget)`
Fixed-height bar at the top. Left side: icon + "Code Assistant" label + model name ("qwen2.5-coder:7b"). Right side: three icon buttons — 🗑 (clear history), — (hide to tray), ✕ (quit). Emits `clear_requested`, `hide_requested`, `quit_requested` signals.

### `chat_widget.py` — `ChatWidget(QScrollArea)`
Vertically stacked list of `MessageBubble` widgets inside a scroll area. Appends new bubbles when messages arrive. Auto-scrolls to bottom on new content. Exposes `add_user_message(text)`, `add_assistant_message() → bubble`, and `clear()` methods.

### `message_bubble.py` — `MessageBubble(QWidget)`
Renders one message. User messages: right-aligned indigo bubble, plain text. Assistant messages: left-aligned purple-tinted bubble. Parses the text for fenced code blocks (` ``` `) and renders each as a `CodeBlock` sub-widget (dark background, language label, Pygments-highlighted text, copy button). Non-code segments rendered as plain `QLabel`.

### `input_bar.py` — `InputBar(QWidget)`
Auto-growing `QTextEdit` (max 5 lines). `Enter` sends; `Shift+Enter` inserts newline. Send button disabled when input is empty or a request is in progress. Emits `message_submitted(text: str)` signal.

### `ollama_client.py` — `OllamaWorker(QThread)`
Runs `ollama.chat()` in a background thread. Emits `token_received(str)` for each streamed chunk and `finished()` on completion, or `error(str)` on failure. The main thread connects these signals to update the active assistant bubble live.

Conversation history is a module-level list of `{"role": str, "content": str}` dicts. Prepends the system prompt on each call. Capped at 20 messages (oldest dropped first).

```python
SYSTEM_PROMPT = (
    "You are an expert coding assistant. Help the user with any programming question "
    "— explain code, debug issues, write code snippets. Be concise and clear. "
    "Use code blocks for all code."
)
MODEL = "qwen2.5-coder:7b"
MAX_HISTORY = 20
```

### `hotkey.py`
Starts a daemon thread using the `keyboard` library to listen for `Ctrl+Space` globally. On trigger, emits a Qt signal (via a `QObject` bridge) to toggle the window's visibility. Catches `ImportError` / permission errors gracefully — logs a warning and continues without the hotkey if it can't register.

### `tray.py` — `TrayIcon(QSystemTrayIcon)`
System tray icon using a small purple icon (generated programmatically as a `QPixmap` — no external image file required). Right-click menu: **Show** (toggles window) and **Quit** (exits app). Double-click on tray icon also toggles window.

---

## Data Flow

```
User types message → presses Enter
  InputBar emits message_submitted(text)
  → ChatWidget.add_user_message(text)
  → history.append({"role": "user", "content": text})
  → OllamaWorker started in QThread
      → ollama.chat(model, messages, stream=True)
      → for each chunk: emit token_received(chunk)
          → ChatWidget active bubble appends token (live streaming)
      → on done: emit finished()
          → history.append({"role": "assistant", "content": full_reply})
          → InputBar re-enabled
      → on error: emit error(message)
          → ChatWidget shows red error bubble
```

---

## Error Handling

| Situation | Behaviour |
|-----------|-----------|
| Ollama not running | Red error bubble: "Ollama isn't running. Start it with `ollama serve`." |
| Model not found | Red error bubble: "Model qwen2.5-coder:7b not found. Run `ollama pull qwen2.5-coder:7b`." |
| Request in flight | Send button disabled until `finished` or `error` signal fires |
| Empty input | Send button disabled; Enter key does nothing |
| Hotkey registration fails | Warning printed to console; app continues without global hotkey |
| Clipboard copy fails | Silent fail (copy button just does nothing) |

---

## File Structure

```
coding-support-agent/
├── gui.py                  # entry point
├── window.py               # OverlayWindow
├── title_bar.py            # TitleBar
├── chat_widget.py          # ChatWidget (scroll area + message list)
├── message_bubble.py       # MessageBubble + CodeBlock widgets
├── input_bar.py            # InputBar
├── ollama_client.py        # OllamaWorker (QThread)
├── hotkey.py               # global hotkey listener
├── tray.py                 # TrayIcon
├── requirements.txt        # updated dependencies
├── .env.example            # kept (FLASK_SECRET_KEY removed)
├── .gitignore
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-27-python-gui-overlay-design.md
```

**Removed files:** `app.py`, `templates/`, `tests/`

---

## Dependencies

```
PyQt6>=6.6.0
ollama>=0.2.0
keyboard>=0.13.5
Pygments>=2.17.0
python-dotenv>=1.0.0
```

---

## Out of Scope

- Persistent chat history (database / file)
- Multiple conversation tabs
- File upload / code file analysis
- Settings UI (opacity slider, hotkey config)
- Auto-update / installer packaging
- macOS / Linux support (Windows 11 primary target)
