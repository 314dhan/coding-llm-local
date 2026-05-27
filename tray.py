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
    """System tray icon with Show/Hide and Quit menu. Double-click toggles visibility."""

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
