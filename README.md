# ytdl — FlexGet + yt-dlp downloader

Downloads the YouTube URLs that FlexGet puts in your list files. It runs several downloads at once, and it can run on its own from the system tray.

## Files

| File | What it does |
|---|---|
| `config.yaml` | All settings: paths, number of simultaneous downloads, per-list formats |
| `ytdl.py` | Downloads every URL in the lists folder |
| `ytdl_tray.py` | Tray app that runs FlexGet and then `ytdl.py` |
| `ytdl_schedule.py` | Learns each channel's upload times, for the smart schedule |
| `channels.py` | Channel Manager window |
| `web_server.py`, `web/index.html` | Web interface |
| `flexget_channels.py` | Shared code for reading and editing the FlexGet config and looking up channels |

Keep all three files in the same folder.

## Requirements

- **Python 3.9+**
- **yt-dlp** and **ffmpeg**, both on your PATH
- **Node.js**, which yt-dlp uses to work around YouTube's JavaScript checks
- **FlexGet**, only needed for the tray app
- Python libraries:
  ```
  pip install pyyaml pystray pillow
  ```

## Quick start

1. Edit the paths in `config.yaml`.
2. Make sure FlexGet writes its `.txt` lists to the `lists_dir` folder.
3. Test a single run:
   ```
   python ytdl.py
   ```
4. Start the tray app:
   ```
   pythonw ytdl_tray.py
   ```
   To start it automatically when you log in: press Win+R, enter `shell:startup`, and put a shortcut to that command in the folder that opens.

## How it works

### Lists
- Each `.txt` file in `lists_dir` is one list. Put one URL per line. Lines starting with `#` or `;` are ignored.
- Videos are saved to `base_output\<list name>\`. For example, `lists\cooking.txt` goes to `T:\sync\Movies\cooking\`.
- A URL is removed from its list once it downloads successfully. Set `keep: true` on a list to keep its URLs, which is useful for channel or playlist URLs you want checked again on every run.
- `downloaded.txt` records every video already fetched, so nothing downloads twice. This archive is shared by all lists.

### Failures
- A URL that fails stays in its list and is retried on the next run.
- After `max_fails` failures (3 by default), it is removed from the list and recorded in `failed.txt`.

### Smart schedule
FlexGet doesn't check all channels on every run. ytdl learns when each channel usually uploads, using the publish times in its YouTube RSS feed, and asks FlexGet to check a channel only around those times, via `flexget execute --tasks ...`.

- **Every channel is checked only around its usual upload times,** whatever time of day that is. It's checked every 30 minutes, from 15 minutes before one of those times until 3 hours after. Channels that only upload on certain weekdays are checked only on those days. A channel that uploads very often has many usual times, so it's checked for most of the day.
- **Channels that don't have enough history yet,** and non-YouTube feeds, have no usual time, so they're only checked by the safety net below.
- **Every channel** is checked at least once a week (`max_gap_hours: 168`), so an off-schedule upload is never missed for long.
- **Run now** checks every channel.
- **View channel schedule** in the tray menu shows what it has learned for each channel.

Upload history is refreshed daily and builds up over time. New channels added with the Channel Manager are picked up automatically. To change the timings, edit `tray: smart_schedule:` in the config. To go back to checking every channel every `interval_minutes`, set it to `false`.

### Live streams
Live, scheduled and just-ended streams are skipped and left in their list. They download on a later run, once YouTube has turned them into normal videos. Without this, ffmpeg would record a live stream in real time until it ended. To turn it off, set `skip_live: false`, either globally or per list.

### Low disk space
Before each download, ytdl checks the free space on the drive it saves to. If it's below `download.min_free_gb` (5 GB by default), downloads stop, the rest of the run is skipped and you get a notification. Free up space and run again. URLs stay in their lists, so nothing is lost.

### Quiet hours
Set `tray: quiet_hours: '23:00-07:00'` to stop all checks and downloads during that time. The tray shows when it resumes. **Run now** still works during quiet hours.

### Expired cookies
If YouTube asks you to sign in or confirm you're not a bot:
1. Downloads stop.
2. The tray icon turns yellow, the app pauses, and you get a notification.
3. Export a fresh `cookies.txt`, then right-click the tray icon and choose **Resume**.

### The tray loop
1. Updates yt-dlp, once a day.
2. Runs FlexGet.
3. Runs `ytdl.py`.
4. Shows a notification with the results.
5. Waits until `interval_minutes` have passed since FlexGet *started*, then repeats. If downloading took longer than the interval, the next run starts immediately.

The icon is red while working, blue while idle and yellow when it needs your attention.

Right-click the icon for these options:

| Menu item | What it does |
|---|---|
| Run now | Skips the rest of the wait |
| Pause / Resume | Pausing lets the current step finish first |
| Open log | Opens `tray.log` |
| Open failed list | Opens `failed.txt` |
| Quit | Exits the tray app |

Only one copy of the tray app can run at a time.

## Web interface

The tray app also serves a web interface at **http://localhost:8765**. To open it, double-click the tray icon or choose **Open web interface** from its menu. It has the same look as the Channel Manager window, and you can bookmark it or keep it open in a tab.

| Page | What you can do |
|---|---|
| Dashboard | A dial counting down to the next check, the current status, **Run now**, a pause switch, the number of URLs waiting in each list, last-run results and recent activity, and **Test a link**: paste a YouTube link to check it can be read (cookies and all) without downloading it |
| Channels | Search, filter by list, look up and add channels (with a WAV option), edit or delete one or several, and open a channel on YouTube |
| Waiting | Every video waiting to download, shown by title, with its list and format. Tick videos and **Delete selected** to remove them from the lists so they aren't downloaded |
| Schedule | What the smart schedule learned for each channel, and which channels are in an upload window right now |
| Failed | Retry videos that kept failing, which puts them back in their list, remove them, or **Export list** to save the whole failed list as a text file (`failed-YYYY-MM-DD.txt`) |
| Settings | The main settings from `config.yaml` (downloads at once, free-space limit, H.264, quiet hours, check times). Save writes only the changed lines, so your comments stay. A backup of the old file goes in `config_backups\`, and the last 20 are kept. Restart the tray app to apply changes |
| Log | The live log, with a filter |

By default it's only reachable from this PC. To use it from your phone or another computer on your network, set `host: 0.0.0.0` in the config, then open `http://<this PC's name or IP>:8765`. No password is needed. If you want one, set `password:`; the browser will then ask for it, and any username works. Windows Firewall may ask whether to allow Python on private networks the first time. To turn the web interface off completely, set `enabled: false`.

### Screenshots

| Dashboard | Channels |
|---|---|
| ![Dashboard](screenshots/dashboard.png) | ![Channels](screenshots/channels.png) |

| Schedule | Failed | Log |
|---|---|---|
| ![Schedule](screenshots/schedule.png) | ![Failed](screenshots/failed.png) | ![Log](screenshots/log.png) |

## Channel Manager

`channels.py` opens a window for managing the channels in your FlexGet config. It does the same job as the web interface's Channels page. To open it, choose **Manage channels** from the tray menu. You can also run `pythonw channels.py` directly.

First, set `paths: flexget_config` in `config.yaml` to your FlexGet `config.yml`.

**Add channel tab**
1. Paste a channel link. A channel page, an `@handle`, a video link or a `UC...` ID all work.
2. Click **Look up**. It shows the channel's name, picture, ID and latest videos so you can check it's the right one. It also warns you if the channel is already in FlexGet.
3. Pick a list, or type a new name to create one, and adjust the task name if you like. Tick **Download as WAV** for audio only; video is the default. A WAV channel's FlexGet entry writes `URL wav` to the list, so a list can mix video and WAV channels. You can change it later with **Edit...**.
4. Click **Yes - add this channel**. The channel is added in the same format as your other entries.

**Channels tab**
- Every channel is listed in alphabetical order, with a search box and a filter by list.
- To edit a channel, double-click it or click **Edit...**. You can change its name, list or channel ID.
- To delete, select one or more channels and click **Delete** or press the Delete key.
- Channels shown in orange need attention. That covers duplicates and lists saved outside the lists folder, which ytdl won't download.

**Waiting tab**

Shows every video in your download lists that hasn't been downloaded yet, by its title, with its list and format. Titles are looked up from YouTube once and remembered in `titles.json`, so the list may show links for a moment before the titles appear.
1. Click a row (or its box) to tick it. Click again to untick.
2. **Tick all** and **Clear ticks** work on the whole list.
3. Press **Delete selected**. The ticked links are removed from their list files, so ytdl won't download them.

Deleting only removes the links from the lists. Videos already downloaded are not affected. A deleted link is also not brought back by FlexGet, because FlexGet remembers the videos it has already seen. If a download run is in progress, a link that is already being downloaded may still finish, so pause first from the tray menu if you're not sure.

The FlexGet file is edited as text, so its formatting and order are kept. A backup is saved to `config_backups\` next to it before every change, and the last 20 are kept.

## Configuration

### Per-list formats
Any list can be downloaded as audio. Use the list's filename without `.txt`:

```yaml
lists:
  music:
    format: wav                         # wav, mp3, flac, m4a, opus, or video
    output: 'T:\sync\Music\YouTube'     # optional, a different folder
    keep: false                         # optional, true keeps the URLs after downloading
    min_date: ''                        # optional, overrides the date cutoff ('' = none)
```

Lists that aren't named here use the `defaults:` section, which is MP4 video unless you change it.

### Main settings

| Setting | Meaning |
|---|---|
| `download.workers` | Number of simultaneous downloads. Keep it to about 3–5 to avoid YouTube rate limits. |
| `download.min_date` | Skip videos uploaded before this date (YYYYMMDD) |
| `download.sleep_min` / `sleep_max` | Random pause between requests, in seconds. Lower is faster but riskier. |
| `download.max_fails` | Number of failures before a URL is given up on |
| `download.min_free_gb` | Stop downloading when the output drive has less than this many GB free. `0` turns the check off |
| `download.date_in_filename` | Put the upload date first in filenames (`20260101 - Channel - Title.mp4`) |
| `download.separate_archives` | Keep audio and video "already downloaded" records apart, so a video you already have can still be downloaded as WAV |
| `download.prefer_h264` | Prefer H.264 video (plays on more devices) |
| `tray.quiet_hours` | A time range with no checks or downloads, e.g. `'23:00-07:00'` |
| `tray.interval_minutes` | Time between FlexGet runs when `smart_schedule` is off |
| `tray.update_cmd` | How yt-dlp gets updated. Use the pip line if you installed it with pip. |

In Windows paths, use **single quotes** so the backslashes are read correctly.

Changes to `config.yaml` take effect on the next download run. If you change anything under `tray:`, restart the tray app.

## Command line options

```
python ytdl.py                     # use config.yaml
python ytdl.py -j 6                # override the number of simultaneous downloads
python ytdl.py --mindate 20260101  # override the date cutoff for all lists
python ytdl.py --config other.yaml # use a different config file
python ytdl.py --update            # update yt-dlp first
```

Exit codes: `0` = all OK, `1` = some failures, `2` = config error, `3` = cookies expired.

## Files created in `state_dir`

| File | Purpose |
|---|---|
| `downloaded.txt` | Archive of downloaded videos |
| `failures.json` | Failure counts for URLs still being retried |
| `failed.txt` | URLs that were given up on |
| `last_run.json` | Results of the last run, read by the tray app |
| `tray.log` | Combined log. It rotates at 5 MB and keeps 3 old copies. |
| `tray_state.json` | Date of the last yt-dlp update |
| `schedule.json` | Upload history and last-checked time for each channel |
| `schedule_report.txt` | Readable summary of each channel's learned schedule |
| `titles.json` | Video titles cached for the Waiting page |

## Troubleshooting

- **The tray app closes immediately.** Run `python ytdl_tray.py` from a command prompt to see the error. It also shows a pop-up and saves the error to `tray_crash.txt`.
- **"Couldn't find flexget" / FlexGet errors.** FlexGet must be installed and on your PATH. Install it with `pip install flexget`, then check `flexget --version` works in a command prompt. If you installed it in a virtual environment, point `tray.flexget_cmd` in `config.yaml` at the full path to the executable. The tray app also needs `paths.flexget_config` to point at your FlexGet `config.yml` (or its folder).
- **Nothing downloads.** Check that the lists aren't empty and that the videos aren't older than `min_date`. Then look in `tray.log`.
- **WAV or MP3 conversion fails.** Install ffmpeg and make sure it's on your PATH.
- **Every download fails.** Update yt-dlp, then check your cookies.
