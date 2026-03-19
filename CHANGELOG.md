# Changelog

## [1.0.0] - 2026-03-19

### Added
- Initial public release
- M3U / M3U8 playlist loading from local file or remote URL
- Auto-categorisation into Live TV, Movies, and Series tabs
- Virtual subcategory sidebar (QAbstractListModel - no QListWidgetItem overhead)
- Lazy tab distribution: active tab loads first, others staggered via QTimer
- On-demand tab loading when switching before lazy load completes
- Virtual channel list (QAbstractListModel + setUniformItemSizes)
- Pre-computed name_lower field for O(1) search on hot path
- Debounced real-time search (150 ms)
- Download progress bar with percentage and indeterminate fallback
- Click-anywhere SeekSlider with drag-lock
- True fullscreen via dedicated top-level window (reliable HWND on Windows)
- _external_render flag prevents VLC render target hijack on resize
- SSL verification on by default; per-session opt-out
- Retry dialog on playlist load failure
- Redirect loop protection (max 10 redirects)
- Dark UI (Catppuccin Mocha palette)
- Keyboard shortcuts: Space, F, M, Escape
- 18 unit tests for the M3U parser (CI-safe, no Qt/VLC required)
- GitHub Actions CI: ruff lint + pytest
- MIT licence
