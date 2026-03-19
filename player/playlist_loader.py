"""Background QThread for loading playlists."""

from __future__ import annotations

import ssl
import logging
import urllib.request
import urllib.error
from urllib.parse import urlparse
from PyQt6.QtCore import QThread, pyqtSignal
from player.m3u_parser import Channel, parse_m3u, _parse_lines

logger     = logging.getLogger(__name__)
_CHUNK     = 131_072
_TIMEOUT   = 60
_MAX_REDIR = 10


class _LimitedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        count = getattr(req, "_redirect_count", 0) + 1
        if count > _MAX_REDIR:
            raise urllib.error.HTTPError(
                newurl, 310, "Too many redirects", headers, fp
            )
        req._redirect_count = count  # type: ignore[attr-defined]
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PlaylistLoader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)

    def __init__(self, source: str, is_url: bool = False,
                 verify_ssl: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._source     = source
        self._is_url     = is_url
        self._verify_ssl = verify_ssl

    def run(self) -> None:
        try:
            result = self._load_url() if self._is_url else self._load_file()
            self.finished.emit(result)
        except Exception as exc:
            logger.error("PlaylistLoader failed: %s", exc)
            self.error.emit(_friendly_error(exc))

    def _load_file(self) -> list[Channel]:
        self.progress.emit(-1)
        channels = parse_m3u(self._source)
        self.progress.emit(100)
        return channels

    def _load_url(self) -> list[Channel]:
        parsed = urlparse(self._source)
        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError(
                "Only http/https is allowed for remote playlists "
                "(got '{}').".format(parsed.scheme)
            )
        ctx = ssl.create_default_context()
        if not self._verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode    = ssl.CERT_NONE
            logger.warning("SSL verification disabled for this request.")

        opener = urllib.request.build_opener(_LimitedRedirectHandler())
        req    = urllib.request.Request(
            self._source,
            headers={"User-Agent": "SecureIPTV/1.0", "Accept": "*/*"},
        )
        with opener.open(req, timeout=_TIMEOUT) as resp:
            total  = int(resp.headers.get("Content-Length") or 0)
            chunks: list[bytes] = []
            done   = 0
            while True:
                chunk = resp.read(_CHUNK)
                if not chunk:
                    break
                chunks.append(chunk)
                done += len(chunk)
                if total > 0:
                    self.progress.emit(min(int(done / total * 90), 89))
                else:
                    self.progress.emit(-1)
        self.progress.emit(90)
        channels = _parse_lines(
            b"".join(chunks).decode("utf-8", errors="replace").splitlines()
        )
        self.progress.emit(100)
        return channels


def _friendly_error(exc: Exception) -> str:
    m = str(exc).lower()
    if "too many redirects" in m:
        return "Too many redirects. The playlist URL may be misconfigured."
    if "timed out" in m or "timeout" in m:
        return "Connection timed out. Check your connection or try again later."
    if "ssl" in m or "certificate" in m:
        return "SSL error. Try enabling 'Skip SSL verification' in the URL dialog."
    if any(k in m for k in ("nodename", "getaddrinfo", "name or service")):
        return "Could not resolve hostname. Check the URL and your DNS settings."
    if "connection refused" in m:
        return "Connection refused by the server."
    if "403" in m:
        return "Access denied (HTTP 403). The server rejected the request."
    if "404" in m:
        return "Playlist not found (HTTP 404). Check the URL."
    return str(exc)
