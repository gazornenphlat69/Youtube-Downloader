# CLAUDE.md

Guidance for Claude when working on this repository. If `memory.md` exists, read it too. It's
the owner's private notes: setup, paths, history and open issues. It's git-ignored, so never
copy its contents into tracked files.

## Project
A Windows system-tray app. **FlexGet** watches YouTube channel RSS feeds and appends new video
URLs to `lists/*.txt`. **ytdl** downloads them with **yt-dlp**, several at once, as MP4 video or
audio (WAV and others). It includes a smart scheduler, a web UI (`localhost:8765`) and a Tk
"Channel Manager". It's pure Python with no build step. The user runs it on Windows under
`pythonw` (no console).

## Layout
| File | Role |
|---|---|
| `ytdl.py` | Downloader CLI. Thread pool of yt-dlp subprocesses, one job per URL |
| `ytdl_tray.py` | Entry point. pystray icon and main loop: daily yt-dlp update, then FlexGet (due tasks only), then ytdl if any list has URLs, then notify and sleep until the next due time. Starts the web server |
| `ytdl_schedule.py` | Learns per-channel upload times from RSS `<published>` and decides which FlexGet tasks are due |
| `web_server.py` | Stdlib `ThreadingHTTPServer` with a JSON API (`/api/...`), served on a daemon thread inside the tray process |
| `web/index.html` | Single-page UI: inline CSS and vanilla JS, no framework, no external requests except channel avatars |
| `flexget_channels.py` | Shared core: `FlexgetConfig` (text-based task edits), `lookup_channel`, `validate`, `load_settings` |
| `channels.py` | Tk Channel Manager window. GUI only; the logic lives in `flexget_channels.py` |
| `config.example.yaml` | Settings template. The first run copies it to `config.yaml`, which is git-ignored |

## Running and testing
```
pip install -r requirements.txt          # pyyaml, pystray, pillow
python ytdl.py                           # one download pass (creates config.yaml on first run)
python ytdl_tray.py                      # tray app + web UI; use pythonw to hide the console
python channels.py                       # Tk window
python -m py_compile *.py                # quick syntax check before handing anything over
```
- **Tests** live in `tests/` (standard-library `unittest`, no extra packages). Run them all from
  the project folder:
  ```
  python -m unittest discover -s tests -t .
  ```
  They use temp folders, never the user's real files. `tests/test_export_ui.py` is a browser
  test (Playwright). It needs `pip install playwright`, and it uses Playwright's own Chromium
  (`playwright install chromium`) or the one in `YTDL_CHROME`. It skips itself when neither is
  available. Run it alone with `YTDL_CHROME=/path/to/chrome python -m unittest tests.test_export_ui`.
- Test with throwaway copies under a temp or scratch folder, never the user's real files.
- **FlexGet edits:** copy a real `config.yml`, then add, edit and delete through
  `FlexgetConfig`, undo the changes, and assert the file is **byte-identical** to the original.
- **Web UI:** run `web_server.start(FakeRunner(), ...)` with a stub runner that has
  `status`, `icon_state`, `paused` (Event), `next_run`, `next_count`, `last_flexget`, `sched`,
  `api_run_now()`, `api_pause()` and `api_resume()`. Exercise it with curl, and take
  screenshots with Playwright (Chromium is preinstalled in Claude's workspace).
- YouTube may be unreachable from sandboxes. If so, stub `flexget_channels.lookup_channel`
  and feed `Scheduler` synthetic upload timestamps.

## Rules
- **Never rewrite the FlexGet config with `yaml.dump`.** Edit it as text (see `FlexgetConfig`)
  so the user's order, comments, CRLF line endings and missing final newline survive. Always
  validate with `yaml.safe_load`, back up to `config_backups/` and replace atomically.
- **List line format is `URL [format]`,** e.g. `https://... wav`. FlexGet writes it via
  `echo {{url}} wav >> "<list>.txt"`. Windows `echo` adds a trailing space. Compare URLs by
  their first token, never by the whole line.
- **Keep pythonw failures visible.** Fatal errors must show a Windows MessageBox and/or write
  `*_crash.txt` / `tray.log`; a silent exit looks to the user like "nothing happens".
- **UTF-8 everywhere.** Pass `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` to subprocesses and use
  `encoding="utf-8", errors="replace"`. Titles with emoji crashed cp1252 before.
- **Web security:** keep the Host-header check (DNS rebinding) and require the `X-YTDL: 1`
  header plus same-origin on every POST or PUT (CSRF). A password stays **optional**. The owner
  explicitly wants LAN access without one, so don't reintroduce a requirement.
- **No new dependencies** without good reason. Stdlib first; the runtime deps are pyyaml,
  pystray and pillow. Tkinter ships with Python.
- **Don't name modules after PyPI packages** (that's why the scheduler is `ytdl_schedule.py`).
- **Settings go in `config.yaml`, never hard-coded.** Every new setting needs a sensible default
  in code, a commented entry in `config.example.yaml` and a line in `README.md`. Path
  defaults are relative to the script folder (`data/`, `downloads/`).
- **Never overwrite the user's `config.yaml`** when delivering changes. Tell them which new
  block to paste in.
- **Never commit or print secrets or personal data:** `cookies.txt`, `config.yaml`, lists,
  logs, state files, `memory.md`. Check `.gitignore` covers anything new that holds personal
  data.

## Design system (web UI and Tk)
"AER — climate dial" neumorphism, light only:
- Colors: `--bg #E8EEF2`, `--shade #c3ccd4`, `--light #ffffff`, `--accent #4db8e8`, `--ink #4a5a66`
  (plus `--ink-soft #7d8b96`, `--warn #e0a24d`, `--bad #e06d6d`, `--ok #5cc28f`).
- Raised surfaces use `8px 8px 16px var(--shade), -8px -8px 16px var(--light)`. Pressed and
  inputs use the inset equivalent.
- Type and shape: system-ui; h1 2.5rem/700; radii 4/8/16px; spacing 1/2/4rem; subtle motion
  (≈0.2s); respect `prefers-reduced-motion`.
- Tk can't draw soft shadows. It uses the same palette on the `clam` theme (`apply_theme()` in
  `channels.py`).
- New UI must match: reuse the existing CSS classes (`.card`, `.well`, `.btn`, `.input`,
  `.toggle`, `.pill`, `.item`) rather than inventing new styles.

## Style
- Plain, readable Python 3.9+. Small functions, comments where behaviour isn't obvious.
- User-facing text is plain language with no jargon (the owner isn't a developer).
- Keep `README.md` in sync with any behaviour or settings change.
