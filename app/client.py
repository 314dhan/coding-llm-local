from PyQt6.QtCore import QThread, pyqtSignal
import ollama

try:
    import httpx as _httpx
except ImportError:
    _httpx = None

_SYSTEM_PROMPTS = {
    "normal": (
        "You are an expert coding assistant. Help the user with any programming question "
        "— explain code, debug issues, write code snippets. Be concise and clear. "
        "Use code blocks for all code."
    ),
    "terse": (
        "Expert coding assistant. No preamble, no filler, no summaries. "
        "Direct answers only. Code blocks for all code. Skip explanation unless asked."
    ),
    "ultra": (
        "Coding assistant. Ultra-terse mode. Fragments OK. Code only. "
        "Drop all filler, intros, summaries. Answer in minimum tokens possible."
    ),
}

_PERSONALITY_PROMPTS = {
    "pro": (
        "Tone: professional and formal. Use precise technical terminology. "
        "Structure responses clearly with consistent formatting."
    ),
    "direct": (
        "Tone: blunt and direct. Assume the user is competent. "
        "Give the answer only — no hand-holding, no filler, no encouragement."
    ),
    "mentor": (
        "Tone: mentoring. Explain reasoning and patterns, not just the answer. "
        "Help the user understand the why, not just the what."
    ),
}

MODEL = "qwen2.5-coder:7b"
MAX_HISTORY = 20

_mode: str = "normal"
_personality: str = "pro"

_history: list[dict] = []


def set_mode(mode: str) -> None:
    global _mode
    if mode in _SYSTEM_PROMPTS:
        _mode = mode


def get_mode() -> str:
    return _mode


def set_personality(personality: str) -> None:
    global _personality
    if personality in _PERSONALITY_PROMPTS:
        _personality = personality


def get_personality() -> str:
    return _personality


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
    system = _SYSTEM_PROMPTS[_mode] + "\n\n" + _PERSONALITY_PROMPTS[_personality]
    return [{"role": "system", "content": system}] + list(_history)


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
            is_conn = isinstance(e, ConnectionError)
            if _httpx and isinstance(e, _httpx.ConnectError):
                is_conn = True
            if not is_conn:
                msg = str(e).lower()
                is_conn = any(w in msg for w in ("connection", "refused", "connect"))
            if is_conn:
                self.error.emit("Ollama isn't running.\nStart it with: ollama serve")
            else:
                self.error.emit(f"Unexpected error: {e}")
