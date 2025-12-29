# Hassio CamLapse

**Hassio CamLapse** is a Home Assistant custom component designed to automatically generate timelapse videos from your camera entities. Ideally suited for long-term monitoring, it captures snapshots at regular intervals, compiles them into hourly videos, and optionally merges them into daily summaries.

## Features

- **Automated Snapshots**: Captures images from any `camera` entity at a configurable interval (default: 60s).
- **Hourly Timelapses**: Automatically compiles snapshots into an MP4 video at the end of every hour.
- **Daily Merging**: Optionally merges hourly videos into a single daily timelapse file to reduce clutter.
- **Gap Filling**: Checks for and generates missing hourly videos from looking back at existing snapshots (e.g., after a restart).
- **Retention Management**: Configurable retention periods for raw snapshots and video files.
- **High Efficiency**: Supports **H.264 (AVC)** and **H.265 (HEVC)** codecs for optimized file sizes.
- **Customizable**: Adjustable frame rates (FPS) and output paths.

## Installation

### Option 1: HACS (Recommended)

1.  Open HACS in Home Assistant.
2.  Go to **Integrations** > **Triple dots** > **Custom repositories**.
3.  Add the URL of this repository and select **Integration** as the category.
4.  Click **Add**.
5.  Search for **Hassio CamLapse** and click **Download**.
6.  Restart Home Assistant.

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

## How It Works

1.  **Snapshotting**: The integration triggers `camera.snapshot` for your selected entity at the defined interval. Files are saved in `Snapshot Path/{camera_name}/snapshots/YYYY-MM-DD/HH/`.
2.  **Hourly Generation**: At the start of a new hour, it checks the previous hour's folder. If snapshots exist, it uses `ffmpeg` to compile them into `timelapse_YYYY-MM-DD_HH.mp4`.
3.  **Backlog Check**: Periodically checks for past hours that have snapshots but missing videos and generates them.
4.  **Merging**: If "Videos Per Day" is set to 1, hourly videos are appended to a daily `timelapse_YYYY-MM-DD.mp4` file and the hourly file is deleted.
5.  **Cleanup**: Old snapshots and videos exceeding the retention period are automatically deleted.

## Troubleshooting

- **Videos not generating**: Ensure `ffmpeg` is installed and accessible in your Home Assistant environment (standard in HAOS/Supervised).
- **Permissions**: Ensure the `Snapshot Path` and `Video Path` are writable by Home Assistant.
- **Logs**: Check **Settings** > **System** > **Logs** for entries involved with `hassio_camlapse` for error details.
