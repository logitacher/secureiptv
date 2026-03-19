"""Virtual list model for channels."""

from __future__ import annotations

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt

from player.m3u_parser import Channel


class ChannelModel(QAbstractListModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._channels: list[Channel] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._channels)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._channels)):
            return None
        ch = self._channels[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return f"[{ch.group}]  {ch.name}" if ch.group else ch.name
        if role == Qt.ItemDataRole.UserRole:
            return ch
        return None

    def set_channels(self, channels: list[Channel]) -> None:
        self.beginResetModel()
        self._channels = channels
        self.endResetModel()

    def channel_at(self, row: int) -> Channel | None:
        return self._channels[row] if 0 <= row < len(self._channels) else None
