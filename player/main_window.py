"""Main application window."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from player.category_tab import CategoryTab
from player.fullscreen_window import FullscreenWindow
from player.m3u_parser import CATEGORY_LIVE, CATEGORY_MOVIES, CATEGORY_SERIES, Channel
from player.playlist_loader import PlaylistLoader
from player.seek_slider import SeekSlider
from player.vlc_player import VLCPlayer

logger      = logging.getLogger(__name__)
_CATEGORIES = [CATEGORY_LIVE, CATEGORY_MOVIES, CATEGORY_SERIES]
_ICONS: dict[str, str] = {
    CATEGORY_LIVE:   "📺",
    CATEGORY_MOVIES: "🎬",
    CATEGORY_SERIES: "🎞️",
}


class UrlDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Load Playlist from URL")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/playlist.m3u")
        form.addRow("Playlist URL:", self.url_input)
        layout.addLayout(form)
        self.ssl_check = QCheckBox("Skip SSL certificate verification")
        self.ssl_check.setToolTip(
            "Enable only if your provider uses an invalid or self-signed certificate. "
            "This reduces transport security - use only with sources you trust."
        )
        layout.addWidget(self.ssl_check)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_url(self)  -> str:  return self.url_input.text().strip()
    def skip_ssl(self) -> bool: return self.ssl_check.isChecked()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SecureIPTV")
        self.setMinimumSize(1024, 640)
        self.resize(1400, 800)

        self._channels:      list[Channel]             = []
        self._loader:        PlaylistLoader | None      = None
        self._last_source:   str                        = ""
        self._last_is_url:   bool                       = False
        self._last_ssl:      bool                       = True
        self._fs_active:     bool                       = False
        # Lazy distribution state
        self._dist_buckets:  dict[str, list[Channel]]  = {}
        self._loaded_tabs:   set[str]                   = set()
        self._pending_cats:  list[str]                  = []

        self._fs_win = FullscreenWindow()
        self._fs_win.exit_requested.connect(self._exit_fullscreen)

        self._setup_ui()
        self._setup_shortcuts()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        layout.addLayout(self._build_toolbar())

        self._dl_bar = QProgressBar()
        self._dl_bar.setRange(0, 100)
        self._dl_bar.setFixedHeight(6)
        self._dl_bar.setTextVisible(False)
        self._dl_bar.setStyleSheet(
            "QProgressBar { background:#313244; border-radius:3px; }"
            "QProgressBar::chunk { background:#89b4fa; border-radius:3px; }"
        )
        self._dl_bar.hide()
        layout.addWidget(self._dl_bar)

        main_split = QSplitter(Qt.Orientation.Horizontal)

        self._tabs = QTabWidget()
        self._tabs.setMinimumWidth(320)
        self._tabs.setMaximumWidth(560)
        self._cat_tabs: dict[str, CategoryTab] = {}
        for cat in _CATEGORIES:
            tab = CategoryTab()
            tab.channel_selected.connect(self._on_channel_selected)
            self._tabs.addTab(tab, f"{_ICONS[cat]} {cat}")
            self._cat_tabs[cat] = tab
        # Load a tab on demand if the user switches before lazy loading finishes
        self._tabs.currentChanged.connect(self._on_tab_switched)
        main_split.addWidget(self._tabs)

        video_pane = QWidget()
        vbox = QVBoxLayout(video_pane)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)
        self.player = VLCPlayer()
        self.player.mouseDoubleClickEvent = lambda _e: self._enter_fullscreen()
        vbox.addWidget(self.player)
        vbox.addLayout(self._build_controls())
        main_split.addWidget(video_pane)

        main_split.setSizes([380, 1020])
        layout.addWidget(main_split)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready - open a playlist file or load from URL.")

        self._poll = QTimer(self)
        self._poll.setInterval(200)
        self._poll.timeout.connect(self._refresh_controls)
        self._poll.start()

    def _build_toolbar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        b1 = QPushButton("📂  Open File")
        b1.setToolTip("Load a local M3U / M3U8 playlist file")
        b1.clicked.connect(self._open_file)
        bar.addWidget(b1)
        b2 = QPushButton("🌐  Load URL")
        b2.setToolTip("Fetch a playlist from a remote HTTP/HTTPS URL")
        b2.clicked.connect(self._open_url_dialog)
        bar.addWidget(b2)
        bar.addSpacing(12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search channels...")
        self.search.textChanged.connect(self._apply_search)
        bar.addWidget(self.search)
        return bar

    def _build_controls(self) -> QHBoxLayout:
        bar = QHBoxLayout()

        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(38)
        self.btn_play.setToolTip("Play / Pause  [Space]")
        self.btn_play.clicked.connect(self.player.toggle_play)
        bar.addWidget(self.btn_play)

        btn_stop = QPushButton("⏹")
        btn_stop.setFixedWidth(38)
        btn_stop.setToolTip("Stop")
        btn_stop.clicked.connect(self.player.stop)
        bar.addWidget(btn_stop)

        self.pos_slider = SeekSlider()
        self.pos_slider.setRange(0, 1000)
        self.pos_slider.seeked.connect(self.player.seek)
        bar.addWidget(self.pos_slider)

        self.time_label = QLabel("--:-- / --:--")
        self.time_label.setFixedWidth(100)
        bar.addWidget(self.time_label)

        bar.addWidget(QLabel("🔊"))
        self.vol_slider = SeekSlider()
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.setFixedWidth(80)
        self.vol_slider.seeked.connect(
            lambda f: self.player.set_volume(int(f * 100))
        )
        self.player.set_volume(80)
        bar.addWidget(self.vol_slider)

        self.btn_mute = QPushButton("🔇")
        self.btn_mute.setFixedWidth(36)
        self.btn_mute.setCheckable(True)
        self.btn_mute.setToolTip("Mute  [M]")
        self.btn_mute.toggled.connect(self.player.set_mute)
        bar.addWidget(self.btn_mute)

        self.btn_fs = QPushButton("⛶")
        self.btn_fs.setFixedWidth(36)
        self.btn_fs.setToolTip("Toggle Fullscreen  [F]")
        self.btn_fs.clicked.connect(self._enter_fullscreen)
        bar.addWidget(self.btn_fs)

        return bar

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Space"),  self, self.player.toggle_play)
        QShortcut(QKeySequence("F"),      self, self._toggle_fullscreen)
        QShortcut(QKeySequence("M"),      self, self.btn_mute.toggle)
        QShortcut(QKeySequence("Escape"), self, self._exit_fullscreen)

    # ------------------------------------------------------------------
    # Fullscreen
    # ------------------------------------------------------------------

    def _toggle_fullscreen(self) -> None:
        self._exit_fullscreen() if self._fs_active else self._enter_fullscreen()

    def _enter_fullscreen(self) -> None:
        if self._fs_active:
            return
        self._fs_active = True
        self._fs_win.showFullScreen()
        QTimer.singleShot(100, self._attach_vlc_to_fs)

    def _attach_vlc_to_fs(self) -> None:
        QApplication.processEvents()
        self.player.attach_to_widget(self._fs_win)
        self._fs_win.show_hint()

    def _exit_fullscreen(self) -> None:
        if not self._fs_active:
            return
        self._fs_active = False
        self._fs_win.hide()
        QTimer.singleShot(30, self.player.restore)

    # ------------------------------------------------------------------
    # Playlist loading
    # ------------------------------------------------------------------

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open M3U Playlist", "",
            "Playlist Files (*.m3u *.m3u8);;All Files (*)",
        )
        if path:
            self._start_loading(path, is_url=False)

    def _open_url_dialog(self) -> None:
        dlg = UrlDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.get_url():
            self._start_loading(
                dlg.get_url(), is_url=True, verify_ssl=not dlg.skip_ssl()
            )

    def _start_loading(self, source: str, is_url: bool,
                       verify_ssl: bool = True) -> None:
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        self._last_source = source
        self._last_is_url = is_url
        self._last_ssl    = verify_ssl
        self._dl_bar.setRange(0, 100)
        self._dl_bar.setValue(0)
        self._dl_bar.show()
        self._status.showMessage("Loading playlist...")
        self._loader = PlaylistLoader(
            source, is_url=is_url, verify_ssl=verify_ssl, parent=self
        )
        self._loader.progress.connect(self._on_progress)
        self._loader.finished.connect(self._on_load_finished)
        self._loader.error.connect(self._on_load_error)
        self._loader.start()

    def _on_progress(self, pct: int) -> None:
        if pct < 0:
            self._dl_bar.setRange(0, 0)
        else:
            self._dl_bar.setRange(0, 100)
            self._dl_bar.setValue(pct)
            self._status.showMessage(
                "Parsing..." if pct >= 90 else f"Downloading... {pct}%"
            )

    def _on_load_finished(self, channels: list[Channel]) -> None:
        self._dl_bar.setValue(100)
        QTimer.singleShot(600, self._dl_bar.hide)
        self._channels = channels
        self._distribute_channels()
        counts = {c: len(self._dist_buckets.get(c, [])) for c in _CATEGORIES}
        self._status.showMessage(
            f"Loaded {len(channels):,} channels - 📺 {counts[CATEGORY_LIVE]:,}  🎬 {counts[CATEGORY_MOVIES]:,}  🎞️ {counts[CATEGORY_SERIES]:,}"
        )

    def _on_load_error(self, message: str) -> None:
        self._dl_bar.hide()
        logger.error("Playlist load error: %s", message)
        box = QMessageBox(self)
        box.setWindowTitle("Playlist Load Error")
        box.setText(message)
        box.setIcon(QMessageBox.Icon.Warning)
        retry = box.addButton("Retry",  QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() == retry:
            self._start_loading(self._last_source, self._last_is_url, self._last_ssl)

    # ------------------------------------------------------------------
    # Lazy tab distribution
    #
    # Strategy: populate ONLY the active tab synchronously, then schedule
    # the remaining two tabs with staggered QTimer.singleShot calls.
    # This keeps the UI fully responsive between tab loads.
    # If the user clicks an unloaded tab before its timer fires,
    # _on_tab_switched() loads it immediately on demand.
    # ------------------------------------------------------------------

    def _distribute_channels(self) -> None:
        # O(n) pass to build per-category buckets
        buckets: dict[str, list[Channel]] = {c: [] for c in _CATEGORIES}
        for ch in self._channels:
            buckets.get(ch.category, buckets[CATEGORY_LIVE]).append(ch)
        self._dist_buckets = buckets
        self._loaded_tabs  = set()

        # Update tab labels immediately (no channel data needed)
        for i, cat in enumerate(_CATEGORIES):
            self._tabs.setTabText(
                i, f"{_ICONS[cat]}  {cat}  ({len(buckets[cat]):,})"
            )

        # Load the active tab now so the user sees data immediately
        active_cat = _CATEGORIES[self._tabs.currentIndex()]
        self._load_tab(active_cat)

        # Stagger the remaining two tabs: let the event loop paint the
        # active tab first, then load the others in the background.
        self._pending_cats = [c for c in _CATEGORIES if c != active_cat]
        QTimer.singleShot(0, self._load_next_pending_tab)

    def _load_next_pending_tab(self) -> None:
        """Load one pending tab per event-loop tick to avoid blocking the UI."""
        if not self._pending_cats:
            return
        cat = self._pending_cats.pop(0)
        self._load_tab(cat)
        if self._pending_cats:
            QTimer.singleShot(0, self._load_next_pending_tab)

    def _load_tab(self, cat: str) -> None:
        """Populate a single tab. No-op if already loaded."""
        if cat in self._loaded_tabs:
            return
        self._loaded_tabs.add(cat)
        self._cat_tabs[cat].set_channels(self._dist_buckets.get(cat, []))

    def _on_tab_switched(self, index: int) -> None:
        """On-demand load when the user clicks a tab before its timer fires."""
        if not self._dist_buckets:
            return
        cat = _CATEGORIES[index]
        if cat not in self._loaded_tabs:
            # Remove from pending so we don't double-load
            if cat in self._pending_cats:
                self._pending_cats.remove(cat)
            self._load_tab(cat)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _apply_search(self) -> None:
        q = self.search.text()
        for tab in self._cat_tabs.values():
            tab.apply_search(q)

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _on_channel_selected(self, url: str, name: str) -> None:
        self.player.play(url)
        self.setWindowTitle(f"SecureIPTV - {name}")
        self.btn_play.setText("⏸")

    def _refresh_controls(self) -> None:
        self.btn_play.setText("⏸" if self.player.is_playing() else "▶")
        if not self.pos_slider.is_dragging:
            self.pos_slider.blockSignals(True)
            self.pos_slider.setValue(int(self.player.get_position() * 1000))
            self.pos_slider.blockSignals(False)
        self.time_label.setText(self.player.get_time_string())

    def closeEvent(self, event) -> None:
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        self._fs_win.close()
        super().closeEvent(event)
