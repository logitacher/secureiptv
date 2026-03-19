"""Channel list view backed by a virtual model."""

from __future__ import annotations

from PyQt6.QtWidgets import QListView
from PyQt6.QtCore import pyqtSignal, QModelIndex, Qt
from player.channel_model import ChannelModel
from player.m3u_parser import Channel


class ChannelListWidget(QListView):
    channel_selected = pyqtSignal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._model = ChannelModel(self)
        self.setModel(self._model)
        self.setUniformItemSizes(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.activated.connect(self._on_activated)
        self.doubleClicked.connect(self._on_activated)

    def set_channels(self, channels: list[Channel]) -> None:
        self._model.set_channels(channels)

    def _on_activated(self, index: QModelIndex) -> None:
        ch = self._model.channel_at(index.row())
        if ch:
            self.channel_selected.emit(ch.url, ch.name)
