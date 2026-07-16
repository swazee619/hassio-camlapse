# Hassio CamLapse

**Hassio CamLapse** is a Home Assistant custom component designed to automatically generate timelapse videos from your camera entities. Ideally suited for long-term monitoring, it captures snapshots at regular intervals, compiles them into hourly videos, and optionally merges them into daily summaries.

## Features

- **Automated Snapshots**: Captures images from any `camera` entity at a configurable interval (default: 60s).
- **Active Time Window**: Restrict snapshot capture to a specific time range (e.g., daylight hours only, or overnight only). Supports ranges that cross midnight.
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
3.  Paste the repository URL: `https://github.com/tolwi/hassio-camlapse` into the **Repository** field.
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
2.  **Hourly Generation**: At the start of a new hour, it checks the previous hour's folder. If snapshots exist, it uses `ffmpeg` to compile them into `timelapse_YYYY-MM-DD_HH.mp4`.
3.  **Backlog Check**: Periodically checks for past hours that have snapshots but missing videos and generates them.
4.  **Merging**: If "Videos Per Day" is set to 1, hourly videos are appended to a daily `timelapse_YYYY-MM-DD.mp4` file and the hourly file is deleted.
5.  **Cleanup**: Old snapshots and videos exceeding the retention period are automatically deleted.

## Active Time Window Examples

| Goal                                | Start Time | End Time   |
| :----------------------------------- | :--------- | :--------- |
| Capture all day (default)            | `00:00:00` | `23:59:59` |
| Daylight only                        | `08:00:00` | `20:00:00` |
| Overnight only (wraps past midnight) | `20:00:00` | `08:00:00` |
| Business hours                       | `09:00:00` | `18:00:00` |

## Troubleshooting

- **Videos not generating**: Ensure `ffmpeg` is installed and accessible in your Home Assistant environment (standard in HAOS/Supervised).
- **Permissions**: Ensure the `Snapshot Path` and `Video Path` are writable by Home Assistant.
- **Logs**: Check **Settings** > **System** > **Logs** for entries involved with `hassio_camlapse` for error details.
- **No snapshots during a certain time range**: This is expected if that range falls outside your configured **Start Time** / **End Time** window. Check **Reconfigure** on the integration entry to verify the window, and enable debug logging to see `Skipping snapshot ... outside active window` entries confirming the behavior.
