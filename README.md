# coding-llm-local

A lightweight, always-on-top coding assistant overlay powered by a local LLM via [Ollama](https://ollama.com). Works with any model available in your Ollama installation — `qwen2.5-coder`, `codellama`, `llama3`, `deepseek-coder`, and more.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![Ollama](https://img.shields.io/badge/Backend-Ollama-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Features

- **Transparent overlay** — frameless, always-on-top window that sits above any application
- **Global hotkey** — `Ctrl+Space` to show/hide from anywhere on your screen
- **System tray** — minimize to tray, double-click or right-click to restore
- **Streaming responses** — tokens appear in real time as the model generates them
- **Syntax-highlighted code blocks** — powered by Pygments
- **Conversation history** — keeps the last 20 messages for context
- **Resizable window** — drag the bottom-right corner to resize
- **Works with any local LLM** — swap models by changing one line in the config

---

## Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com)** installed and running (`ollama serve`)
- At least one model pulled, e.g.:

```bash
ollama pull qwen2.5-coder:7b
```

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/314dhan/coding-llm-local.git
cd coding-llm-local

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running

Make sure Ollama is running first:

```bash
ollama serve
```

Then launch the overlay:

```bash
python gui.py
```

The overlay window appears. Press `Ctrl+Space` at any time to show or hide it.

---

## Configuration

### Changing the model

Open `app/client.py` and edit the `MODEL` constant on line 14:

```python
MODEL = "qwen2.5-coder:7b"   # change to any model you have pulled
```

Examples:

| Model | Pull command |
|-------|-------------|
| `qwen2.5-coder:7b` | `ollama pull qwen2.5-coder:7b` |
| `codellama:7b` | `ollama pull codellama:7b` |
| `deepseek-coder:6.7b` | `ollama pull deepseek-coder:6.7b` |
| `llama3.2:3b` | `ollama pull llama3.2:3b` |
| `mistral:7b` | `ollama pull mistral:7b` |

Any model listed by `ollama list` will work.

### System prompt

The assistant's persona is defined in `app/client.py`:

```python
SYSTEM_PROMPT = (
    "You are an expert coding assistant. Help the user with any programming question "
    "— explain code, debug issues, write code snippets. Be concise and clear. "
    "Use code blocks for all code."
)
```

Edit this string to change the assistant's behavior.

---

## Hotkeys & Controls

| Action | How |
|--------|-----|
| Show / Hide overlay | `Ctrl+Space` |
| Send message | `Enter` |
| New line in input | `Shift+Enter` |
| Clear chat history | Click **Clear** in the title bar |
| Hide to tray | Click **−** in the title bar |
| Quit | Click **×** in the title bar, or right-click tray → Quit |
| Resize window | Drag the bottom-right grip |

---

## Project Structure

```
coding-llm-local/
├── gui.py                  # Entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── app/
│   ├── client.py           # Ollama client + streaming worker (QThread)
│   ├── hotkey.py           # Global hotkey listener (Ctrl+Space)
│   ├── tray.py             # System tray icon
│   └── ui/
│       ├── window.py       # Main overlay window
│       ├── chat_widget.py  # Scrollable message list
│       ├── input_bar.py    # Text input with send button
│       ├── message_bubble.py # Individual message with syntax highlighting
│       └── title_bar.py    # Draggable title bar with controls
└── tests/
    ├── test_ollama_client.py   # Unit tests for client logic
    └── test_message_parser.py  # Unit tests for message parsing
```

---

## Running Tests

```bash
pytest tests/
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `PyQt6` | GUI framework |
| `ollama` | Ollama Python client |
| `keyboard` | Global hotkey registration |
| `Pygments` | Syntax highlighting in code blocks |
| `python-dotenv` | `.env` file loading |
| `pytest` | Test runner |

---

## License

MIT — do whatever you want with it.
