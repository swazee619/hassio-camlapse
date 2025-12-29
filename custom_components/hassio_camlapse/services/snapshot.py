import logging
import os

from homeassistant.core import HomeAssistant
from homeassistant.components.camera import async_get_image
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class SnapshotService:
    def __init__(self, hass: HomeAssistant, camera_entity_id: str, snapshot_path: str, camera_id: str):
        self.hass = hass
        self.camera_entity_id = camera_entity_id
        self.snapshot_path = snapshot_path
        self.camera_id = camera_id

    def get_snapshot_path(self, date_str: str, hour_str: str) -> str:
        """Get path for snapshots of a specific hour."""
        return os.path.join(self.snapshot_path, self.camera_id, "snapshots", date_str, hour_str)

    async def async_take_snapshot(self):
        """Take a snapshot and save it."""
        try:
            image = await async_get_image(self.hass, self.camera_entity_id)
            content = image.content
        except Exception as err:
            _LOGGER.error("Error fetching image from %s: %s", self.camera_entity_id, err)
            return

        now = dt_util.now()
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        file_time_str = now.strftime("%Y-%m-%d_%H-%M-%S")

        folder_path = self.get_snapshot_path(date_str, hour_str)
        file_path = os.path.join(folder_path, f"{file_time_str}.jpg")

        def _write_file():
            os.makedirs(folder_path, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(content)

        await self.hass.async_add_executor_job(_write_file)
        _LOGGER.debug(f"Saved snapshot to {file_path}")
