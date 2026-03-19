"""Per-category tab: virtual subcategory sidebar + virtual channel list.

Both the subcategory list and the channel list are backed by
QAbstractListModel, so Qt only renders visible rows regardless of
how many groups or channels exist.
"""

from __future__ import annotations

from PyQt6.QtCore import (
    QAbstractListModel,
    QItemSelectionModel,
    QModelIndex,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtWidgets import QHBoxLayout, QListView, QSplitter, QWidget

from player.channel_list import ChannelListWidget
from player.m3u_parser import Channel


class _SubcatModel(QAbstractListModel):
    """Virtual model for the group sidebar.

    Replacing QListWidget eliminates the overhead of creating one
    QListWidgetItem object per group — critical when a provider has
    hundreds or thousands of group-title values.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._groups: list[str] = ["All"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._groups)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._groups)):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._groups[index.row()]
        return None

    def set_groups(self, groups: list[str]) -> None:
        self.beginResetModel()
        self._groups = groups
        self.endResetModel()

    def group_at(self, row: int) -> str:
        return self._groups[row] if 0 <= row < len(self._groups) else "All"

    def row_of(self, group: str) -> int:
        try:
            return self._groups.index(group)
        except ValueError:
            return 0


class CategoryTab(QWidget):
    """One tab: group sidebar on the left, channel list on the right.

    set_channels() is O(n) in channels (to build buckets) but the
    UI update is O(1) because both lists are virtual models.
    """

    channel_selected = pyqtSignal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._all:           list[Channel]            = []
        self._buckets:       dict[str, list[Channel]] = {"All": []}
        self._search:        str                      = ""
        self._current_group: str                      = "All"

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self._apply_filter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Virtual subcategory list ---
        self._subcat_model = _SubcatModel()
        self.subcat_list   = QListView()
        self.subcat_list.setModel(self._subcat_model)
        self.subcat_list.setUniformItemSizes(True)
        self.subcat_list.setMaximumWidth(220)
        self.subcat_list.setMinimumWidth(140)
        self.subcat_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.subcat_list.selectionModel().currentRowChanged.connect(
            self._on_subcat_changed
        )
        splitter.addWidget(self.subcat_list)

        # --- Virtual channel list ---
        self.channel_list = ChannelListWidget()
        self.channel_list.channel_selected.connect(self.channel_selected)
        splitter.addWidget(self.channel_list)

        splitter.setSizes([200, 800])
        layout.addWidget(splitter)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_channels(self, channels: list[Channel]) -> None:
        """Load channels, pre-bucket by group, refresh both virtual lists."""
        self._all = channels

        # Build group buckets in one O(n) pass
        buckets: dict[str, list[Channel]] = {"All": channels}
        for ch in channels:
            if ch.group:
                buckets.setdefault(ch.group, []).append(ch)
        self._buckets = buckets

        # Build sorted group list, preserve current selection if possible
        groups     = ["All"] + sorted(k for k in buckets if k != "All")
        target_row = self._subcat_model.row_of(self._current_group)

        # Swap the model data (O(1) UI update via beginResetModel/endResetModel)
        self._subcat_model.set_groups(groups)

        # Re-select the previously active group (or row 0)
        target_row = min(target_row, len(groups) - 1)
        idx = self._subcat_model.index(target_row, 0)
        self.subcat_list.selectionModel().setCurrentIndex(
            idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        self._current_group = self._subcat_model.group_at(target_row)

        self._apply_filter()

    def apply_search(self, query: str) -> None:
        self._search = query.strip().lower()
        self._debounce.start()

    def channel_count(self) -> int:
        return len(self._all)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_subcat_changed(self, current: QModelIndex, _prev: QModelIndex) -> None:
        self._current_group = self._subcat_model.group_at(current.row())
        self._apply_filter()

    def _apply_filter(self) -> None:
        candidates = self._buckets.get(self._current_group, [])
        if self._search:
            q = self._search
            candidates = [c for c in candidates if q in c.name_lower]
        self.channel_list.set_channels(candidates)
