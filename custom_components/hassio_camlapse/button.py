"""Button platform for Hassio CamLapse - on-demand full timelapse compilation."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the compile button for a config entry."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CamLapseCompileButton(manager, entry)])


class CamLapseCompileButton(ButtonEntity):
    """Button to compile all daily videos into one master timelapse, on demand."""

    _attr_has_entity_name = True
    _attr_name = "Compile Full Timelapse"
    _attr_icon = "mdi:movie-filter"

    def __init__(self, manager, entry: ConfigEntry):
        self._manager = manager
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_compile_full_button"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Hassio CamLapse",
        )

    async def async_press(self) -> None:
        """Trigger compilation of all daily videos into timelapse_full.mp4."""
        result = await self._manager.async_compile_full_video()
        if result is None:
            _LOGGER.warning(
                "Full timelapse compilation produced no output "
                "(no daily videos found, or ffmpeg failed - check logs)"
            )
        else:
            _LOGGER.info("Full timelapse compilation complete: %s", result)
