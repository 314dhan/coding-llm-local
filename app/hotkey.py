import sys
import threading
import ctypes
import ctypes.wintypes

from PyQt6.QtCore import QObject, pyqtSignal

_WM_HOTKEY = 0x0312
_MOD_CTRL  = 0x0002
_MOD_SHIFT = 0x0004
_VK_SPACE  = 0x20
_HOTKEY_ID = 1


class _Bridge(QObject):
    triggered = pyqtSignal()


class HotkeyListener:
    """Registers Ctrl+Shift+Space as a global hotkey using the Windows RegisterHotKey API.

    Falls back to the `keyboard` library on non-Windows platforms.
    """

    HOTKEY = "ctrl+shift+space"

    def __init__(self, window):
        self._bridge = _Bridge()
        self._bridge.triggered.connect(window.toggle_visibility)
        self._emit = self._bridge.triggered.emit

    def start(self) -> None:
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self) -> None:
        if sys.platform == "win32":
            self._run_win32()
        else:
            self._run_keyboard_lib()

    def _run_win32(self) -> None:
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, _HOTKEY_ID, _MOD_CTRL | _MOD_SHIFT, _VK_SPACE):
            print(f"Warning: Could not register hotkey '{self.HOTKEY}'")
            return
        try:
            msg = ctypes.wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == _WM_HOTKEY and msg.wParam == _HOTKEY_ID:
                    self._emit()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            user32.UnregisterHotKey(None, _HOTKEY_ID)

    def _run_keyboard_lib(self) -> None:
        try:
            import keyboard
            keyboard.add_hotkey(self.HOTKEY, self._emit)
            keyboard.wait()
        except ImportError:
            print("Warning: `keyboard` library not installed — hotkey disabled.")
        except Exception as e:
            print(f"Warning: Could not register hotkey '{self.HOTKEY}': {e}")
