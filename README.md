# SecureIPTV

A lightweight, secure, open-source IPTV desktop player built with Python,
PyQt6, and libVLC.

![CI](https://github.com/logitacher/secureiptv/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Features

- Load M3U / M3U8 playlists from a local file or remote URL
- Auto-sorts channels into Live TV / Movies / Series tabs
- Virtual subcategory sidebar - instant even with thousands of groups
- Lazy tab loading - UI stays responsive while other tabs load in background
- Real-time debounced search using pre-computed lowercase names
- True fullscreen (F / Esc / double-click)
- SSL verification on by default; per-session opt-out
- Cross-platform: Windows / macOS / Linux

## Requirements

- Python 3.11+
- VLC installed system-wide: https://www.videolan.org/

## Install & Run

```bash
git clone https://github.com/logitacher/secureiptv.git
cd secureiptv
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
python main.py
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play / Pause |
| F | Toggle Fullscreen |
| M | Toggle Mute |
| Escape | Exit Fullscreen |
| Double-click video | Enter Fullscreen |

## Tests

```bash
pip install pytest
pytest
```

## License

[MIT](LICENSE)
