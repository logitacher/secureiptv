"""Dedicated fullscreen window used as VLC render target."""

from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeyEvent, QMouseEvent


class FullscreenWindow(QWidget):
    exit_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setStyleSheet("background:#000000;")

        self._hint = QLabel("Press  F  or  Esc  to exit fullscreen", self)
        self._hint.setStyleSheet(
            "color:rgba(255,255,255,200);"
            "background:rgba(0,0,0,150);"
            "border-radius:6px;"
            "padding:6px 16px;"
            "font-size:14px;"
        )
        self._hint.adjustSize()
        self._hint.hide()

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(2500)
        self._hide_timer.timeout.connect(self._hint.hide)

    def show_hint(self) -> None:
        self._hint.adjustSize()
        self._hint.move((self.width() - self._hint.width()) // 2, 30)
        self._hint.show()
        self._hint.raise_()
        self._hide_timer.start()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_F):
            self.exit_requested.emit()
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.exit_requested.emit()
        super().mouseDoubleClickEvent(event)
