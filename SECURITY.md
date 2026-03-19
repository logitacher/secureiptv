# Security Policy

## Reporting a Vulnerability
Use GitHub Security Advisories (Security tab -> New advisory).
Do NOT open public issues for security vulnerabilities.

## Security Design

| Area | Measure |
|---|---|
| URL allow-list | Only `http`, `https`, `rtsp`, `rtmp`, `rtmps`, `rtp`, `mms`, `mmsh`, `udp` |
| Dangerous schemes | `file://`, `javascript:`, `data:` silently rejected |
| No shell execution | Pure Python parser - no subprocess, os.system, eval |
| Credential hygiene | Rejected URLs never logged (may contain auth tokens) |
| Immutable model | Channel objects are frozen dataclasses with __slots__ |
| TLS | Verified by default; per-session opt-out is user-initiated |
| Redirect limit | Capped at 10 redirects per request |
| Input caps | All M3U string attributes length-capped before storage |
| No auto-update | Only fetches user-specified URLs, never on its own |
| .gitignore | *.m3u and *.m3u8 excluded to prevent committing private playlists |
