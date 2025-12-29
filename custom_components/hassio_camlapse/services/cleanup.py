import logging
import os
import datetime
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class CleanupService:
    def __init__(
        self, hass: HomeAssistant, snapshot_service, video_service, image_retention_days: int, video_retention_days: int
    ):
        self.hass = hass
        self.snapshot_service = snapshot_service
        self.video_service = video_service
        self.image_retention_days = image_retention_days
        self.video_retention_days = video_retention_days

    async def cleanup_old_files(self):
        """Delete old images and videos."""

        # Cleanup Images (folders are by day, so logic remains mainly the same)
        # We just delete the YYYY-MM-DD folder which contains HH subfolders.
        snapshot_base = os.path.join(self.snapshot_service.snapshot_path, self.snapshot_service.camera_id, "snapshots")

        def _cleanup_images():
            if not os.path.exists(snapshot_base):
                return

            cutoff_date = dt_util.now() - datetime.timedelta(days=self.image_retention_days)

            for folder_name in os.listdir(snapshot_base):
                try:
                    folder_date = datetime.datetime.strptime(folder_name, "%Y-%m-%d").date()
                    if folder_date < cutoff_date.date():
                        full_path = os.path.join(snapshot_base, folder_name)
                        import shutil

                        shutil.rmtree(full_path)
                        _LOGGER.info(f"Deleted old snapshots: {full_path}")
                except ValueError:
                    continue  # Not a date folder

        await self.hass.async_add_executor_job(_cleanup_images)

        # Cleanup Videos
        video_base = self.video_service.get_video_path()

        def _cleanup_videos():
            if not os.path.exists(video_base):
                return

            cutoff_date = dt_util.now() - datetime.timedelta(days=self.video_retention_days)

            for file_name in os.listdir(video_base):
                if file_name.startswith("timelapse_") and file_name.endswith(".mp4"):
                    # Format: timelapse_YYYY-MM-DD_HH.mp4
                    try:
                        # Extract date part: YYYY-MM-DD
                        parts = file_name.replace("timelapse_", "").replace(".mp4", "").split("_")
                        if len(parts) >= 1:
                            date_str = parts[0]
                            file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                            if file_date < cutoff_date.date():
                                full_path = os.path.join(video_base, file_name)
                                os.remove(full_path)
                                _LOGGER.info(f"Deleted old video: {full_path}")
                    except ValueError:
                        continue

        await self.hass.async_add_executor_job(_cleanup_videos)
