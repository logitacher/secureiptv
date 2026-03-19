"""Secure M3U/M3U8 playlist parser."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

__all__ = [
    "Channel",
    "CATEGORY_LIVE",
    "CATEGORY_MOVIES",
    "CATEGORY_SERIES",
    "parse_m3u",
]

logger = logging.getLogger(__name__)

CATEGORY_LIVE   = "Live TV"
CATEGORY_MOVIES = "Movies"
CATEGORY_SERIES = "Series"

_ALLOWED_SCHEMES: frozenset[str] = frozenset(
    {"http", "https", "rtsp", "rtmp", "rtmps", "rtp", "mms", "mmsh", "udp"}
)
_MAX_NAME:  int = 256
_MAX_GROUP: int = 128
_MAX_ATTR:  int = 512

_EXTINF_RE = re.compile(r"#EXTINF:-?\d+(?:\.\d+)?\s*(.*?)\s*,\s*(.+)")
_ATTR_RE   = re.compile(r'([\w-]+)="([^"]*)"')

_SERIES_KW: frozenset[str] = frozenset({
    "series", "serie", "serien", "show", "shows", "season", "saison",
    "episode", "episodes", "tvshow", "tv show", "staffel",
})
_MOVIE_KW: frozenset[str] = frozenset({
    "movie", "movies", "film", "films", "filme", "vod", "cinema",
    "pellicule", "peliculas", "pelicula",
})


@dataclass(frozen=True, slots=True)
class Channel:
    name:       str
    url:        str
    name_lower: str
    category:   str = CATEGORY_LIVE
    logo:       str = ""
    group:      str = ""
    tvg_id:     str = ""
    tvg_name:   str = ""


def _sanitize(value: str, max_len: int = _MAX_ATTR) -> str:
    return value.strip()[:max_len]


def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme.lower() in _ALLOWED_SCHEMES and bool(parsed.netloc)
    except Exception:
        return False


def _detect_category(name: str, group: str) -> str:
    text = (group + " " + name).lower()
    if any(kw in text for kw in _SERIES_KW):
        return CATEGORY_SERIES
    if any(kw in text for kw in _MOVIE_KW):
        return CATEGORY_MOVIES
    return CATEGORY_LIVE


def _parse_lines(lines: list[str]) -> list[Channel]:
    if not lines or not lines[0].strip().upper().startswith("#EXTM3U"):
        raise ValueError("Not a valid M3U playlist (missing #EXTM3U header).")
    channels: list[Channel] = []
    pending:  dict[str, str] = {}
    for raw in lines[1:]:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            match = _EXTINF_RE.match(line)
            if match:
                attrs_str, raw_name = match.group(1), match.group(2)
                attrs = dict(_ATTR_RE.findall(attrs_str))
                name  = _sanitize(raw_name, _MAX_NAME)
                group = _sanitize(attrs.get("group-title", ""), _MAX_GROUP)
                pending = {
                    "name":     name,
                    "group":    group,
                    "logo":     _sanitize(attrs.get("tvg-logo",  ""), _MAX_ATTR),
                    "tvg_id":   _sanitize(attrs.get("tvg-id",    ""), _MAX_GROUP),
                    "tvg_name": _sanitize(attrs.get("tvg-name",  ""), _MAX_GROUP),
                    "category": _detect_category(name, group),
                }
            continue
        if line.startswith("#"):
            continue
        if pending:
            if _is_safe_url(line):
                channels.append(Channel(
                    url=line,
                    name_lower=pending["name"].lower(),
                    **pending,
                ))
            else:
                logger.warning("Skipped channel '%s': URL scheme not allowed.",
                               pending.get("name", "<unknown>"))
            pending = {}
    return channels


def parse_m3u(filepath: str) -> list[Channel]:
    real_path = os.path.realpath(filepath)
    with open(real_path, encoding="utf-8", errors="replace") as fh:
        return _parse_lines(fh.read().splitlines())
