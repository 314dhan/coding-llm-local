import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from app.ui.window import OverlayWindow
from app.tray import TrayIcon
from app.hotkey import HotkeyListener


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
