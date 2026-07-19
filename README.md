# Hassio CamLapse

**Hassio CamLapse** is a Home Assistant custom component designed to automatically generate timelapse videos from your camera entities. Ideally suited for long-term monitoring, it captures snapshots at regular intervals, compiles them into hourly videos, and optionally merges them into daily summaries.

## Features

- **Automated Snapshots**: Captures images from any `camera` entity at a configurable interval (default: 60s).
- **Active Time Window**: Restrict snapshot capture to a specific time range (e.g., daylight hours only, or overnight only). Supports ranges that cross midnight.
- **Pause/Resume Switch**: A `switch` entity per camera to pause and resume snapshot capture on demand (e.g. via automation or dashboard), without disabling the whole integration. State survives restarts.
- **On-Demand Full Compilation**: A `button` entity per camera to concatenate every daily video generated so far into a single `timelapse_full.mp4` master file.
- **Hourly Timelapses**: Automatically compiles snapshots into an MP4 video at the end of every hour.
- **Daily Merging**: Optionally merges hourly videos into a single daily timelapse file to reduce clutter.
- **Gap Filling**: Checks for and generates missing hourly videos from looking back at existing snapshots (e.g., after a restart).
- **Retention Management**: Configurable retention periods for raw snapshots and video files.
- **High Efficiency**: Supports **H.264 (AVC)** and **H.265 (HEVC)** codecs for optimized file sizes.
- **Customizable**: Adjustable frame rates (FPS) and output paths.

## Installation

### Option 1: HACS (Recommended)

1.  Open HACS in Home Assistant.
2.  Go to **Integrations** > **Triple dots** (top right) > **Custom repositories**.
3.  Paste the repository URL: `https://github.com/swazee619/hassio-camlapse` into the **Repository** field.
4.  Select **Integration** as the **Category**.
5.  Click **Add**.
6.  Close the custom repositories dialog.
7.  Search for **Hassio CamLapse** and click **Download**.
8.  Restart Home Assistant.

### Option 2: Manual Installation

1.  Download the `custom_components/hassio_camlapse` folder from this repository.
2.  Copy the folder into your Home Assistant's `config/custom_components/` directory.
3.  Restart Home Assistant.

## Configuration

**Hassio CamLapse** is configured entirely via the Home Assistant UI.

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for **Hassio CamLapse**.
4.  Follow the setup wizard.

### Configuration Options

| Option                 | Description                                               | Default            |
| :--------------------- | :-------------------------------------------------------- | :----------------- |
| **Camera Entity**      | The camera entity id to capture snapshots from.           | Required           |
| **Interval**           | Time in seconds between snapshots.                        | `60`               |
| **Snapshot Path**      | Base path. Files saved in `<path>/<camera_id>/snapshots`. | `/media/timelapse` |
| **Video Path**         | Base path. Files saved in `<path>/<camera_id>/videos`.    | `/media/timelapse` |
| **Output FPS**         | Frames per second for the output video.                   | `10`               |
| **Codec**              | Video codec to use (`libx264` or `libx265`).              | `H.264 (AVC)`      |
| **Snapshot Retention** | Number of days to keep raw images.                        | `7`                |
| **Video Retention**    | Number of days to keep video files.                       | `30`               |
| **Videos Per Day**     | Set to `1` to merge hourly videos into a daily file.      | `1`                |
| **Start Time**         | Time of day snapshots start being captured (HH:MM:SS).    | `00:00:00`         |
| **End Time**           | Time of day snapshots stop being captured (HH:MM:SS). If earlier than Start Time, the window is treated as overnight (e.g. `20:00` → `08:00`). | `23:59:59` |

## How It Works

1.  **Snapshotting**: The integration triggers `camera.snapshot` for your selected entity at the defined interval. Files are saved in `Snapshot Path/{camera_name}/snapshots/YYYY-MM-DD/HH/`.
    - Before saving, the current time is checked against **Start Time** / **End Time**. If it falls outside this window, the snapshot is skipped (no file written, no error).
    - Hours with no snapshots simply produce no video for that hour — nothing else is affected.
2.  **Hourly Generation**: At the start of a new hour, it checks the previous hour's folder. If snapshots exist, it uses `ffmpeg` to compile them into `timelapse_YYYY-MM-DD_HH.mp4`, encoded with `preset medium` (ffmpeg's own default) and a codec-appropriate CRF (`23` for H.264, `30` for H.265 - bumped from the default `28` after a visual check showed no perceptible difference on real footage, for ~20% smaller files).
    - Unlike regular high-framerate video, timelapse frames are captured minutes apart and share almost no inter-frame redundancy. Slower presets (`slow`/`veryslow`) exist to exploit that redundancy more thoroughly, but empirically produced **larger** files here, not smaller - stick with `medium` unless you've verified otherwise on your own footage.
3.  **Backlog Check**: Periodically checks for past hours that have snapshots but missing videos and generates them.
    - To avoid re-processing already-merged hours on every check, a hidden `.merged` marker file is written inside each hour's **snapshot** folder once that hour has been folded into its daily video. If a video exists but its `.merged` marker is present, the backlog check considers it already handled and skips it — see [Troubleshooting](#troubleshooting) if you ever need to force a full regeneration.
4.  **Merging**: If "Videos Per Day" is set to 1, hourly videos are appended to a daily `timelapse_YYYY-MM-DD.mp4` file and the hourly file is deleted.
5.  **Cleanup**: Old snapshots and videos exceeding the retention period are automatically deleted.

## Active Time Window Examples

| Goal                                | Start Time | End Time   |
| :----------------------------------- | :--------- | :--------- |
| Capture all day (default)            | `00:00:00` | `23:59:59` |
| Daylight only                        | `08:00:00` | `20:00:00` |
| Overnight only (wraps past midnight) | `20:00:00` | `08:00:00` |
| Business hours                       | `09:00:00` | `18:00:00` |

## Entities Created

Each configured camera exposes two extra entities alongside its config entry:

| Entity                     | Type     | Purpose                                                                                   |
| :-------------------------- | :------- | :------------------------------------------------------------------------------------------ |
| **Capture Active**          | `switch` | Pause/resume snapshot capture on demand. Off = no new snapshots (existing videos untouched). Automatable, e.g. `switch.turn_off` before doing gardening work in frame. State is restored after a Home Assistant restart. |
| **Compile Full Timelapse**  | `button` | Concatenates every existing `timelapse_YYYY-MM-DD.mp4` daily video into one `timelapse_full.mp4` in the video folder. Re-run any time to rebuild it with newly generated days included. |

> **Note on Compile Full Timelapse**: it uses a lossless stream copy (no re-encoding), so all daily videos must share the same codec/FPS/resolution. This holds true unless those settings were changed mid-project via **Reconfigure**. If compilation fails, check the logs — mismatched encoding parameters is the most likely cause.

## Troubleshooting

- **Videos not generating**: Ensure `ffmpeg` is installed and accessible in your Home Assistant environment (standard in HAOS/Supervised).
- **Permissions**: Ensure the `Snapshot Path` and `Video Path` are writable by Home Assistant.
- **Logs**: Check **Settings** > **System** > **Logs** for entries involved with `hassio_camlapse` for error details.
- **No snapshots during a certain time range**: This is expected if that range falls outside your configured **Start Time** / **End Time** window. Check **Reconfigure** on the integration entry to verify the window, and enable debug logging to see `Skipping snapshot ... outside active window` entries confirming the behavior.
- **Forcing a full video regeneration**: Deleting `.mp4` files from the video folder is not enough on its own. Each hour that was already merged into a daily video has a hidden `.merged` marker file left behind inside its **snapshot** folder (`<snapshot_path>/<camera_id>/snapshots/<date>/<hour>/.merged`), and the backlog check skips any hour with that marker — even if the corresponding video no longer exists. To force regeneration:
  1. Delete the `.mp4` files you want rebuilt from the video folder.
  2. Also delete the matching `.merged` markers, e.g. from a shell with access to the snapshot path:
     ```bash
     find <snapshot_path>/<camera_id>/snapshots -name ".merged" -delete
     ```
  3. Restart Home Assistant (or wait for the next hourly backlog check) to trigger regeneration, then re-press **Compile Full Timelapse** if needed.
- **Smaller file sizes without losing quality**: For timelapse content (low inter-frame redundancy), the preset has little effect on size - `medium` (the default) already performs as well as or better than slower presets here. The real lever is CRF: raising it (e.g. `28` → `30` for H.265) trades a small amount of quality for a meaningfully smaller file - test on your own footage with `ffprobe`/visual comparison before committing to a value, since "acceptable quality" is subjective. Switching from H.264 to H.265 (via **Reconfigure**) cuts file size further (~40-50%) at equivalent quality, but note that **Compile Full Timelapse** stream-copies (no re-encode), so all daily videos must share the same codec — regenerate older days (see above) after switching codecs to keep compilation working.
