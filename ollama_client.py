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
