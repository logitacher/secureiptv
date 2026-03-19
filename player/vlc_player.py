"""libVLC-backed video frame with switchable render target."""

from __future__ import annotations

import logging
import sys

import vlc
from PyQt6.QtWidgets import QFrame, QSizePolicy

logger = logging.getLogger(__name__)


class VLCPlayer(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(480, 270)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color:#000000;")
        self._instance = vlc.Instance("--no-xlib", "--quiet", "--no-video-title-show")
        self._player: vlc.MediaPlayer = self._instance.media_player_new()
        self._external_render = False
        self._attach_window()

    def _attach_to_wid(self, wid: int) -> None:
        if sys.platform.startswith("win"):
            self._player.set_hwnd(wid)
        elif sys.platform == "darwin":
            self._player.set_nsobject(wid)
        else:
            self._player.set_xwindow(wid)

    def _attach_window(self) -> None:
        if not self._external_render:
            self._attach_to_wid(int(self.winId()))

    def attach_to_widget(self, widget) -> None:
        self._external_render = True
        self._attach_to_wid(int(widget.winId()))

    def restore(self) -> None:
        self._external_render = False
        self._attach_to_wid(int(self.winId()))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._attach_window()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._attach_window()

    def play(self, url: str) -> None:
        media = self._instance.media_new(url)
        self._player.set_media(media)
        self._player.play()

    def toggle_play(self) -> None:
        self._player.pause() if self._player.is_playing() else self._player.play()

    def stop(self) -> None:              self._player.stop()
    def seek(self, pos: float) -> None:  self._player.set_position(max(0.0, min(1.0, pos)))
    def set_volume(self, v: int) -> None: self._player.audio_set_volume(max(0, min(100, v)))
    def set_mute(self, m: bool) -> None: self._player.audio_set_mute(m)
    def is_playing(self) -> bool:        return bool(self._player.is_playing())

    def get_position(self) -> float:
        pos = self._player.get_position()
        return pos if pos >= 0 else 0.0

    def get_time_string(self) -> str:
        return f"{_fmt_ms(self._player.get_time())} / {_fmt_ms(self._player.get_length())}"

    def closeEvent(self, event) -> None:
        self._player.stop()
        super().closeEvent(event)


def _fmt_ms(ms: int) -> str:
    if ms <= 0:
        return "--:--"
    s = ms // 1000
    return f"{s // 60:02d}:{s % 60:02d}"
