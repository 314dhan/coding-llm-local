import threading
from PyQt6.QtCore import QObject, pyqtSignal


class _Bridge(QObject):
    """Emits a Qt signal safely from a non-Qt thread."""
    triggered = pyqtSignal()


class HotkeyListener:
    """Registers Ctrl+Space as a global hotkey to toggle the overlay window.

    Runs in a daemon thread. Logs a warning and continues gracefully if the
    `keyboard` library is unavailable or hotkey registration fails.
    """

    HOTKEY = "ctrl+space"

    def __init__(self, window):
        self._bridge = _Bridge()
        self._bridge.triggered.connect(window.toggle_visibility)
        # Capture emit in main thread — PyQt6 rejects signal access from other threads
        self._emit = self._bridge.triggered.emit

    def start(self) -> None:
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self) -> None:
        try:
            import keyboard
            keyboard.add_hotkey(self.HOTKEY, self._emit)
            keyboard.wait()
        except ImportError:
            print("Warning: `keyboard` library not installed — hotkey disabled.")
        except Exception as e:
            print(f"Warning: Could not register hotkey '{self.HOTKEY}': {e}")
