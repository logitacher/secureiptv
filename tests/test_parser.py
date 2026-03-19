"""Unit tests for the M3U parser (no Qt or VLC required)."""

import pytest
from player.m3u_parser import (
    _parse_lines, _is_safe_url,
    CATEGORY_LIVE, CATEGORY_MOVIES, CATEGORY_SERIES,
)


def _make_m3u(*entries):
    lines = ["#EXTM3U"]
    for extinf, url in entries:
        lines.append(extinf)
        lines.append(url)
    return lines


def test_http_allowed():        assert _is_safe_url("http://example.com/s")
def test_https_allowed():       assert _is_safe_url("https://example.com/s.m3u8")
def test_rtsp_allowed():        assert _is_safe_url("rtsp://media.example.com/live")
def test_file_blocked():        assert not _is_safe_url("file:///etc/passwd")
def test_javascript_blocked():  assert not _is_safe_url("javascript:alert(1)")
def test_data_blocked():        assert not _is_safe_url("data:text/html,<x>")
def test_ftp_blocked():         assert not _is_safe_url("ftp://example.com/f")
def test_no_netloc_blocked():   assert not _is_safe_url("http:///no-host")


def test_parse_single_channel():
    lines = _make_m3u(
        ('#EXTINF:-1 tvg-id="ch1" group-title="News",Test Channel',
         "http://example.com/stream.m3u8"),
    )
    channels = _parse_lines(lines)
    assert len(channels) == 1
    ch = channels[0]
    assert ch.name == "Test Channel"
    assert ch.url  == "http://example.com/stream.m3u8"
    assert ch.group  == "News"
    assert ch.tvg_id == "ch1"


def test_name_lower_precomputed():
    lines = _make_m3u(('#EXTINF:-1,Hello World', "http://example.com/s"))
    assert _parse_lines(lines)[0].name_lower == "hello world"


def test_invalid_header_raises():
    with pytest.raises(ValueError, match="EXTM3U"):
        _parse_lines(["not an m3u file"])


def test_empty_lines_skipped():
    lines = ["#EXTM3U", "", '#EXTINF:-1,Chan', "", "http://example.com/s", ""]
    assert len(_parse_lines(lines)) == 1


def test_unsafe_url_dropped():
    lines = _make_m3u(
        ('#EXTINF:-1,Bad',  "javascript:alert(1)"),
        ('#EXTINF:-1,Good', "http://example.com/ok"),
    )
    channels = _parse_lines(lines)
    assert len(channels) == 1
    assert channels[0].name == "Good"


def test_file_url_dropped():
    lines = _make_m3u(('#EXTINF:-1,Local', "file:///etc/passwd"))
    assert _parse_lines(lines) == []


def test_name_truncated():
    lines = _make_m3u(('#EXTINF:-1,{}'.format("A" * 1000), "http://example.com/s"))
    assert len(_parse_lines(lines)[0].name) == 256


def test_group_truncated():
    long_group = "G" * 500
    lines = _make_m3u((
        '#EXTINF:-1 group-title="{}",Chan'.format(long_group),
        "http://example.com/s",
    ))
    assert len(_parse_lines(lines)[0].group) == 128


def test_category_movies():
    lines = _make_m3u(
        ('#EXTINF:-1 group-title="VOD Movies",Action Film', "http://example.com/m")
    )
    assert _parse_lines(lines)[0].category == CATEGORY_MOVIES


def test_category_series():
    lines = _make_m3u(
        ('#EXTINF:-1 group-title="TV Series",Breaking Bad', "http://example.com/s")
    )
    assert _parse_lines(lines)[0].category == CATEGORY_SERIES


def test_category_live_default():
    lines = _make_m3u(
        ('#EXTINF:-1 group-title="Sports",Live Match', "http://example.com/l")
    )
    assert _parse_lines(lines)[0].category == CATEGORY_LIVE


def test_category_series_beats_movies():
    lines = _make_m3u(
        ('#EXTINF:-1 group-title="Movie Series",Title', "http://example.com/x")
    )
    assert _parse_lines(lines)[0].category == CATEGORY_SERIES
