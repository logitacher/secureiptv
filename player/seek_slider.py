"""Click-anywhere seek slider with drag-lock."""

from __future__ import annotations

from PyQt6.QtWidgets import QSlider, QStyle
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent


class SeekSlider(QSlider):
    seeked = pyqtSignal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._dragging = False
        self.sliderPressed.connect(lambda: setattr(self, "_dragging", True))
        self.sliderReleased.connect(self._on_released)
        self.sliderMoved.connect(
            lambda v: self.seeked.emit(v / max(self.maximum(), 1))
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            value = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(),
                int(event.position().x()), self.width(),
            )
            self.setValue(value)
            self.seeked.emit(value / max(self.maximum(), 1))
        super().mousePressEvent(event)

    def _on_released(self) -> None:
        self._dragging = False
        self.seeked.emit(self.value() / max(self.maximum(), 1))

    @property
    def is_dragging(self) -> bool:
        return self._dragging
