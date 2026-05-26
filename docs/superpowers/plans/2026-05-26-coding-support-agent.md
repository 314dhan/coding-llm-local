# Coding Support Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web-based chat UI coding assistant using Flask + plain HTML/JS that calls the Claude API to answer any programming question.

**Architecture:** A single-file Flask backend serves the HTML page and exposes a `POST /chat` endpoint. Conversation history is stored server-side in a dict keyed by session ID. The frontend sends messages via `fetch()` and renders markdown replies using `marked.js`.

**Tech Stack:** Python 3.10+, Flask 3.x, Anthropic Python SDK, python-dotenv, pytest, marked.js (CDN)

---

## File Map

| File | Responsibility |
|------|---------------|
| `app.py` | Flask server, `/` and `/chat` routes, Claude API calls, session history |
| `templates/index.html` | Chat UI — HTML, CSS, JS all in one file |
| `requirements.txt` | Python dependencies |
| `.env` | `ANTHROPIC_API_KEY` (not committed) |
| `.env.example` | Template showing required env vars |
| `.gitignore` | Excludes `.env`, `venv/`, `__pycache__/` |
| `tests/test_app.py` | Pytest tests for all Flask routes |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Initialize git and create project files**

Run from `E:\kuzon\project\coding support agent`:
```powershell
git init
```

- [ ] **Step 2: Create `requirements.txt`**

```
flask>=3.0.0
anthropic>=0.49.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 3: Create `.env.example`**

```
ANTHROPIC_API_KEY=your_api_key_here
```

- [ ] **Step 4: Create `.gitignore`**

```
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 5: Create and activate virtual environment, install dependencies**

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 6: Create your `.env` file with your real API key**

```
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

Get your key at: https://console.anthropic.com/

- [ ] **Step 7: Commit**

```powershell
git add requirements.txt .env.example .gitignore
git commit -m "chore: project setup"
```

---

## Task 2: Flask Skeleton + GET /

**Files:**
- Create: `app.py`
- Create: `templates/index.html` (placeholder)
- Create: `tests/test_app.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `tests/__init__.py`** (empty file)

- [ ] **Step 2: Write the failing test in `tests/test_app.py`**

```python
import json
import pytest
from unittest.mock import MagicMock, patch
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    with flask_app.test_client() as client:
        yield client


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_contains_chat_ui(client):
    response = client.get("/")
    assert b"Coding Support Agent" in response.data
```

- [ ] **Step 3: Run the test — verify it FAILS**

```powershell
pytest tests/test_app.py::test_index_returns_200 -v
```

Expected: `ModuleNotFoundError: No module named 'app'` or `ImportError`.

- [ ] **Step 4: Create `templates/index.html` placeholder**

```html
<!DOCTYPE html>
<html><head><title>Coding Support Agent</title></head>
<body><h1>Coding Support Agent</h1></body>
</html>
```

- [ ] **Step 5: Create `app.py` — Flask skeleton**

```python
import os
import uuid
from flask import Flask, render_template, request, jsonify, session
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not _api_key:
    raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")

client = Anthropic(api_key=_api_key)

conversation_histories: dict[str, list] = {}

SYSTEM_PROMPT = (
    "You are an expert coding assistant. Help the user with any programming question "
    "— explain code, debug issues, write code snippets. Be concise and clear. "
    "Use code blocks for all code."
)

MAX_HISTORY = 20


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
```

- [ ] **Step 6: Run the tests — verify they PASS**

```powershell
pytest tests/test_app.py -v
```

Expected:
```
PASSED tests/test_app.py::test_index_returns_200
PASSED tests/test_app.py::test_index_contains_chat_ui
```

- [ ] **Step 7: Commit**

```powershell
git add app.py templates/index.html tests/
git commit -m "feat: flask skeleton with GET / route"
```

---

## Task 3: POST /chat Route

**Files:**
- Modify: `app.py` — add `/chat` route
- Modify: `tests/test_app.py` — add chat route tests

- [ ] **Step 1: Add tests for `/chat` to `tests/test_app.py`**

Append these test functions to the end of the existing file (imports are already at the top from Task 2):

```python
def test_chat_empty_message_returns_400(client):
    with client.session_transaction() as sess:
        sess["session_id"] = "test-session-empty"
    response = client.post(
        "/chat",
        data=json.dumps({"message": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_chat_missing_message_returns_400(client):
    with client.session_transaction() as sess:
        sess["session_id"] = "test-session-missing"
    response = client.post(
        "/chat",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_chat_returns_reply(client):
    with patch("app.client") as mock_client:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Use a for loop.")]
        mock_client.messages.create.return_value = mock_response

        with client.session_transaction() as sess:
            sess["session_id"] = "test-session-reply"

        response = client.post(
            "/chat",
            data=json.dumps({"message": "How do I loop in Python?"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["reply"] == "Use a for loop."


def test_chat_history_accumulates(client):
    with patch("app.client") as mock_client:
        mock_resp1 = MagicMock()
        mock_resp1.content = [MagicMock(text="Answer 1")]
        mock_resp2 = MagicMock()
        mock_resp2.content = [MagicMock(text="Answer 2")]
        mock_client.messages.create.side_effect = [mock_resp1, mock_resp2]

        with client.session_transaction() as sess:
            sess["session_id"] = "test-session-history"

        client.post(
            "/chat",
            data=json.dumps({"message": "First question"}),
            content_type="application/json",
        )
        client.post(
            "/chat",
            data=json.dumps({"message": "Second question"}),
            content_type="application/json",
        )

        second_call_args = mock_client.messages.create.call_args
        messages = second_call_args.kwargs["messages"]
        assert len(messages) == 3
        assert messages[0] == {"role": "user", "content": "First question"}
        assert messages[1] == {"role": "assistant", "content": "Answer 1"}
        assert messages[2] == {"role": "user", "content": "Second question"}
```

- [ ] **Step 2: Run new tests — verify they FAIL**

```powershell
pytest tests/test_app.py::test_chat_empty_message_returns_400 -v
```

Expected: `FAILED` — route doesn't exist yet (404).

- [ ] **Step 3: Add the `/chat` route to `app.py`**

Add this function after the `index()` route, before `if __name__ == "__main__":`:

```python
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    session_id = session.get("session_id")
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    history = conversation_histories[session_id]
    history.append({"role": "user", "content": user_message})

    if len(history) > MAX_HISTORY:
        conversation_histories[session_id] = history[-MAX_HISTORY:]
        history = conversation_histories[session_id]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=history,
    )

    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})
```

- [ ] **Step 4: Run all tests — verify they PASS**

```powershell
pytest tests/test_app.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add app.py tests/test_app.py
git commit -m "feat: add POST /chat route with session history"
```

---

## Task 4: Full Frontend UI

**Files:**
- Modify: `templates/index.html` — replace placeholder with full chat UI

- [ ] **Step 1: Replace `templates/index.html` with the full UI**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coding Support Agent</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: #16213e;
            padding: 16px 24px;
            border-bottom: 1px solid #0f3460;
            flex-shrink: 0;
        }
        header h1 { font-size: 1.2rem; color: #e94560; }
        header p { font-size: 0.8rem; color: #888; margin-top: 2px; }

        #chat {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.6;
            word-wrap: break-word;
        }
        .user {
            align-self: flex-end;
            background: #0f3460;
            color: #e0e0e0;
            border-bottom-right-radius: 4px;
            white-space: pre-wrap;
        }
        .assistant {
            align-self: flex-start;
            background: #16213e;
            border: 1px solid #0f3460;
            border-bottom-left-radius: 4px;
        }

        .message pre {
            background: #0d0d1a;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 8px 0;
        }
        .message code {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.88em;
        }
        .message p { margin-bottom: 8px; }
        .message p:last-child { margin-bottom: 0; }
        .message ul, .message ol { padding-left: 20px; margin-bottom: 8px; }
        .message li { margin-bottom: 4px; }

        .typing {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 14px 16px;
        }
        .typing span {
            width: 8px;
            height: 8px;
            background: #e94560;
            border-radius: 50%;
            animation: bounce 1.2s infinite;
        }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-6px); }
        }

        #input-area {
            background: #16213e;
            border-top: 1px solid #0f3460;
            padding: 16px 24px;
            display: flex;
            gap: 12px;
            align-items: flex-end;
            flex-shrink: 0;
        }
        #message-input {
            flex: 1;
            background: #0d0d1a;
            border: 1px solid #0f3460;
            color: #e0e0e0;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 1rem;
            resize: none;
            min-height: 44px;
            max-height: 140px;
            outline: none;
            font-family: inherit;
            line-height: 1.5;
        }
        #message-input:focus { border-color: #e94560; }
        #message-input::placeholder { color: #555; }
        #send-btn {
            background: #e94560;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0 20px;
            font-size: 1rem;
            cursor: pointer;
            height: 44px;
            white-space: nowrap;
            transition: background 0.15s;
        }
        #send-btn:disabled { background: #444; cursor: not-allowed; }
        #send-btn:hover:not(:disabled) { background: #c73652; }
    </style>
</head>
<body>
    <header>
        <h1>Coding Support Agent</h1>
        <p>Ask anything — debug, explain, write code, any language</p>
    </header>

    <div id="chat">
        <div class="message assistant">
            <p>Hi! I'm your coding assistant. Ask me anything — debugging, explanations, code snippets, any language.</p>
        </div>
    </div>

    <div id="input-area">
        <textarea
            id="message-input"
            placeholder="Ask a coding question... (Enter to send, Shift+Enter for newline)"
            rows="1"
        ></textarea>
        <button id="send-btn">Send</button>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');

        marked.setOptions({ breaks: true });

        function addMessage(role, content) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            if (role === 'assistant') {
                div.innerHTML = marked.parse(content);
            } else {
                div.textContent = content;
            }
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function showTyping() {
            const div = document.createElement('div');
            div.className = 'message assistant typing';
            div.id = 'typing-indicator';
            div.innerHTML = '<span></span><span></span><span></span>';
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function hideTyping() {
            const el = document.getElementById('typing-indicator');
            if (el) el.remove();
        }

        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;

            input.value = '';
            input.style.height = '44px';
            sendBtn.disabled = true;

            addMessage('user', message);
            showTyping();

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message }),
                });
                const data = await res.json();
                hideTyping();
                if (data.reply) {
                    addMessage('assistant', data.reply);
                } else {
                    addMessage('assistant', 'Sorry, something went wrong. Please try again.');
                }
            } catch {
                hideTyping();
                addMessage('assistant', 'Connection error. Is the server running?');
            } finally {
                sendBtn.disabled = false;
                input.focus();
            }
        }

        sendBtn.addEventListener('click', sendMessage);

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        input.addEventListener('input', () => {
            input.style.height = '44px';
            input.style.height = Math.min(input.scrollHeight, 140) + 'px';
        });
    </script>
</body>
</html>
```

- [ ] **Step 2: Run all tests to confirm nothing broke**

```powershell
pytest tests/test_app.py -v
```

Expected: All 6 tests PASS (the frontend change doesn't affect backend tests).

- [ ] **Step 3: Commit**

```powershell
git add templates/index.html
git commit -m "feat: add full chat UI with markdown rendering"
```

---

## Task 5: Manual End-to-End Test

**Files:** none (smoke test only)

- [ ] **Step 1: Start the server**

```powershell
python app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

- [ ] **Step 2: Open http://127.0.0.1:5000 in your browser**

Expected: Dark-themed chat UI with welcome message.

- [ ] **Step 3: Test these scenarios**

| Test | Input | Expected |
|------|-------|----------|
| Basic question | `What is a list comprehension in Python?` | Explanation with code example |
| Debug request | `Why does this crash: x = int("hello")` | Explains ValueError |
| Multi-turn | Ask a follow-up to the previous answer | Claude remembers context |
| Code generation | `Write a Python function to reverse a string` | Returns working code in a code block |
| Other language | `How do I declare a variable in Rust?` | Correct Rust syntax |

- [ ] **Step 4: Stop server with Ctrl+C**

- [ ] **Step 5: Final commit**

```powershell
git add .
git commit -m "feat: coding support agent complete"
```

---

## Running the App (Quick Reference)

```powershell
# Activate venv (do this every time you open a new terminal)
venv\Scripts\activate

# Start the server
python app.py

# Run tests
pytest tests/ -v

# Open in browser
# http://127.0.0.1:5000
```
