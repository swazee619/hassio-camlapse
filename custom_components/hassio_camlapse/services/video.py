import logging
import os
import datetime
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class VideoService:
    def __init__(
        self,
        hass: HomeAssistant,
        video_path: str,
        camera_id: str,
        output_fps: int,
        output_codec: str,
        videos_per_day: int,
        snapshot_service,
    ):
        self.hass = hass
        self.video_path = video_path
        self.camera_id = camera_id
        self.output_fps = output_fps
        self.output_codec = output_codec
        self.videos_per_day = videos_per_day
        self.snapshot_service = snapshot_service

    def get_video_path(self) -> str:
        """Get path for output videos."""
        return os.path.join(self.video_path, self.camera_id, "videos")

    async def async_generate_timelapse(self, date_str: str, hour_str: str):
        """Generate timelapse for a specific date and hour."""
        folder_path = self.snapshot_service.get_snapshot_path(date_str, hour_str)
        output_folder = self.get_video_path()
        output_file = os.path.join(output_folder, f"timelapse_{date_str}_{hour_str}.mp4")

        def _ensure_folder():
            if not os.path.exists(folder_path):
                return False
            os.makedirs(output_folder, exist_ok=True)
            return True

        if not await self.hass.async_add_executor_job(_ensure_folder):
            _LOGGER.error(f"Snapshot folder {folder_path} does not exist")
            return

        async def _create_list_file_and_run_ffmpeg():
            list_file_path = os.path.join(folder_path, "file_list.txt")

            def _prepare_list():
                files = sorted([f for f in os.listdir(folder_path) if f.endswith(".jpg")])
                if not files:
                    return None

                frame_duration = 1.0 / self.output_fps
                with open(list_file_path, "w") as f:
                    for filename in files:
                        f.write(f"file '{filename}'\n")
                        f.write(f"duration {frame_duration}\n")
                    if files:
                        f.write(f"file '{files[-1]}'\n")
                return True

            if not await self.hass.async_add_executor_job(_prepare_list):
                _LOGGER.warning("No files found to generate timelapse for %s %s", date_str, hour_str)
                return

            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_file_path,
                "-r",
                str(self.output_fps),
                "-c:v",
                self.output_codec,
                "-pix_fmt",
                "yuv420p",
                output_file,
            ]

            _LOGGER.info(f"Running ffmpeg: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                _LOGGER.error(f"FFmpeg failed: {stderr.decode()}")
            else:
                _LOGGER.info(f"Timelapse created at {output_file}")

            try:
                await self.hass.async_add_executor_job(os.remove, list_file_path)
            except OSError:
                pass

        await _create_list_file_and_run_ffmpeg()

        # After successful generation, attempt to merge if configured
        await self.merge_timelapses(date_str, hour_str)

    async def merge_timelapses(self, date_str: str, hour_str: str):
        """Merge hourly timelapse into daily video if configured."""
        if self.videos_per_day != 1:
            return

        video_folder = self.get_video_path()
        source_video = os.path.join(video_folder, f"timelapse_{date_str}_{hour_str}.mp4")
        target_video = os.path.join(video_folder, f"timelapse_{date_str}.mp4")
        snapshot_folder = self.snapshot_service.get_snapshot_path(date_str, hour_str)
        merged_marker = os.path.join(snapshot_folder, ".merged")

        async def _do_merge():
            if not await self.hass.async_add_executor_job(os.path.exists, source_video):
                return

            if not await self.hass.async_add_executor_job(os.path.exists, target_video):
                # First video of the day, just rename
                await self.hass.async_add_executor_job(os.rename, source_video, target_video)
                _LOGGER.info(f"Initialized daily video {target_video} from {source_video}")
            else:
                # Append to existing
                list_file_path = os.path.join(video_folder, f"merge_list_{date_str}_{hour_str}.txt")

                def _write_list():
                    with open(list_file_path, "w") as f:
                        f.write(f"file '{target_video}'\n")
                        f.write(f"file '{source_video}'\n")

                await self.hass.async_add_executor_job(_write_list)

                temp_output = os.path.join(video_folder, f"timelapse_{date_str}_temp.mp4")

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_file_path,
                    "-c",
                    "copy",
                    temp_output,
                ]

                _LOGGER.info(f"Merging video: {' '.join(cmd)}")
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0:

                    def _finalize():
                        os.rename(temp_output, target_video)
                        os.remove(source_video)
                        if os.path.exists(list_file_path):
                            os.remove(list_file_path)

                    await self.hass.async_add_executor_job(_finalize)
                    _LOGGER.info(f"Merged {source_video} into {target_video}")
                else:
                    _LOGGER.error(f"Failed to merge videos: {stderr.decode()}")

                    def _cleanup_fail():
                        if os.path.exists(temp_output):
                            os.remove(temp_output)
                        if os.path.exists(list_file_path):
                            os.remove(list_file_path)

                    await self.hass.async_add_executor_job(_cleanup_fail)
                    # Don't create marker if failed
                    return

            # Create marker file to prevent regeneration loop
            # Ensure snapshot folder exists (it should)
            def _create_marker():
                if os.path.exists(snapshot_folder):
                    with open(merged_marker, "w") as f:
                        f.write("merged")

            await self.hass.async_add_executor_job(_create_marker)

        await _do_merge()

    async def check_and_generate_backlog(self, video_retention_days: int):
        """Check for missing hourly timelapses and generate them."""
        # Check from now backwards by hour
        now = dt_util.now()
        video_folder = self.get_video_path()

        await self.hass.async_add_executor_job(lambda: os.makedirs(video_folder, exist_ok=True))

        # Check back X days worth of hours
        # We start from previous hour to avoid generating current incomplete hour
        start_check = now - datetime.timedelta(hours=1)
        hours_to_check = video_retention_days * 24

        # Batch check for existence of videos and merged markers
        def _get_backlog_status(start, count):
            status = {}
            for i in reversed(range(count)):
                check_time = start - datetime.timedelta(hours=i)
                d_str = check_time.strftime("%Y-%m-%d")
                h_str = check_time.strftime("%H")
                key = (d_str, h_str)

                v_file = os.path.join(video_folder, f"timelapse_{d_str}_{h_str}.mp4")
                v_exists = os.path.exists(v_file)

                s_folder = self.snapshot_service.get_snapshot_path(d_str, h_str)
                m_marker = os.path.join(s_folder, ".merged")
                is_merged = os.path.exists(m_marker)

                has_snaps = os.path.exists(s_folder) and any(f.endswith(".jpg") for f in os.listdir(s_folder))

                status[key] = {"video_exists": v_exists, "is_merged": is_merged, "has_snapshots": has_snaps}
            return status

        backlog_status = await self.hass.async_add_executor_job(_get_backlog_status, start_check, hours_to_check)

        for (date_str, hour_str), status in backlog_status.items():
            if status["video_exists"]:
                _LOGGER.debug(f"Video for {date_str} {hour_str} exists.")
                continue

            if status["is_merged"]:
                _LOGGER.debug(f"Video for {date_str} {hour_str} was already merged.")
                continue

            if status["has_snapshots"]:
                _LOGGER.info(f"Generating missing timelapse for {date_str} {hour_str}")
                await self.async_generate_timelapse(date_str, hour_str)
