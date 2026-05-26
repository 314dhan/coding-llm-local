# Coding Support Agent — Design Spec

**Date:** 2026-05-26
**Stack:** Flask + plain HTML/JS + Claude API (claude-haiku-4-5)

## Overview

A web-based chat UI for a general AI coding assistant. Users can ask any coding question (explain code, debug, write code) in any language. The app runs locally and communicates with the Claude API.

## Architecture

```
Browser (HTML/JS)
    │  POST /chat  {"message": "..."}
    ▼
Flask server (app.py)
    │  anthropic SDK
    ▼
Claude API (claude-haiku-4-5)
    │  response
    ▼
Browser — renders reply in chat UI
```

## File Structure

```
coding-support-agent/
├── app.py              # Flask server + Claude API integration
├── templates/
│   └── index.html      # Chat UI (HTML + CSS + JS in one file)
├── .env                # ANTHROPIC_API_KEY (not committed to git)
├── .gitignore          # Excludes .env and __pycache__
└── requirements.txt    # flask, anthropic, python-dotenv
```

## Components

### Backend (app.py)

- Flask app with two routes:
  - `GET /` — serves the chat UI
  - `POST /chat` — receives `{"message": "..."}`, calls Claude API, returns `{"reply": "..."}`
- Conversation history stored in a server-side in-memory dict keyed by a session ID (UUID stored in Flask's session cookie)
- System prompt: "You are an expert coding assistant. Help the user with any programming question — explain code, debug issues, write code snippets. Be concise and clear. Use code blocks for all code."
- Model: `claude-haiku-4-5` (fast, cheap, capable)

### Frontend (templates/index.html)

- Single HTML file with embedded CSS and JS
- Chat layout: scrollable message list + input box + send button
- JS sends `POST /chat` with the user message, appends both user message and assistant reply to the chat
- Renders markdown using `marked.js` (CDN) so code blocks display with formatting
- Keyboard shortcut: Enter to send, Shift+Enter for newline

### Configuration (.env)

```
ANTHROPIC_API_KEY=your_key_here
```

Loaded via `python-dotenv` at startup. App exits with a clear error if the key is missing.

## Data Flow

1. User types a message and presses Enter
2. JS appends user message to the chat and sends `POST /chat {"message": "..."}`
3. Flask appends message to conversation history, calls `anthropic.messages.create()`
4. Claude response is appended to history and returned as `{"reply": "..."}`
5. JS renders the reply with markdown formatting

## Conversation History

- Stored in a server-side in-memory dict: `{ session_id: [ {"role": ..., "content": ...} ] }`
- Session ID is a UUID generated on first visit, stored in Flask's session cookie
- History is cleared on page refresh (no persistence — keeps it simple)
- Max history: last 20 messages to avoid exceeding context limits

## Error Handling

- Missing API key → server logs clear error and returns 500 with message
- Claude API error → returns 500 with user-friendly message ("Something went wrong, please try again")
- Empty user message → ignored on the frontend (send button disabled)

## Dependencies

```
flask
anthropic
python-dotenv
```

Frontend uses `marked.js` via CDN (no build step needed).

## Out of Scope

- User authentication
- Persistent chat history (database)
- File upload / code file analysis
- Streaming responses
- Multiple chat sessions/tabs
