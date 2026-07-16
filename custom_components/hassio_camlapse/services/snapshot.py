import logging
import os

from homeassistant.core import HomeAssistant
from homeassistant.components.camera import async_get_image
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class SnapshotService:
    def __init__(
        self,
        hass: HomeAssistant,
        camera_entity_id: str,
        snapshot_path: str,
        camera_id: str,
        start_time: str = "00:00:00",
        end_time: str = "23:59:59",
    ):
        self.hass = hass
        self.camera_entity_id = camera_entity_id
        self.snapshot_path = snapshot_path
        self.camera_id = camera_id
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)

    @staticmethod
    def _parse_time(time_str: str) -> "datetime.time":
        """Parse a HH:MM:SS or HH:MM string into a time object."""
        import datetime as _dt
        parts = [int(p) for p in time_str.split(":")]
        while len(parts) < 3:
            parts.append(0)
        return _dt.time(parts[0], parts[1], parts[2])

    def _is_within_active_window(self, now) -> bool:
        """Check if the current local time falls within the configured capture window."""
        current_time = now.time()
        if self.start_time <= self.end_time:
            # Normal range, e.g. 08:00 -> 20:00
            return self.start_time <= current_time <= self.end_time
        # Overnight range, e.g. 20:00 -> 08:00 (wraps past midnight)
        return current_time >= self.start_time or current_time <= self.end_time

    def get_snapshot_path(self, date_str: str, hour_str: str) -> str:
        """Get path for snapshots of a specific hour."""
        return os.path.join(self.snapshot_path, self.camera_id, "snapshots", date_str, hour_str)

    async def async_take_snapshot(self):
        """Take a snapshot and save it, if within the configured active window."""
        now = dt_util.now()
        if not self._is_within_active_window(now):
            _LOGGER.debug(
                "Skipping snapshot for %s: outside active window (%s-%s)",
                self.camera_entity_id, self.start_time, self.end_time,
            )
            return

        try:
            image = await async_get_image(self.hass, self.camera_entity_id)
            content = image.content
        except Exception as err:
            _LOGGER.error("Error fetching image from %s: %s", self.camera_entity_id, err)
            return

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
