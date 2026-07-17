"""Switch platform for Hassio CamLapse - pause/resume snapshot capture."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the capture switch for a config entry."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CamLapseCaptureSwitch(manager, entry)])


class CamLapseCaptureSwitch(SwitchEntity, RestoreEntity):
    """Switch to pause/resume timelapse snapshot capture for one camera."""

    _attr_has_entity_name = True
    _attr_name = "Capture Active"
    _attr_icon = "mdi:camera-timer"

    def __init__(self, manager, entry: ConfigEntry):
        self._manager = manager
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_capture_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Hassio CamLapse",
        )
        # Default to "on" until we know otherwise (e.g. first install, no prior state)
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        """Restore previous on/off state on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        # Sync the manager with the restored (or default) state
        await self._manager.async_set_capture_enabled(self._attr_is_on)

    async def async_turn_on(self, **kwargs) -> None:
        """Resume snapshot capture."""
        self._attr_is_on = True
        await self._manager.async_set_capture_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Pause snapshot capture."""
        self._attr_is_on = False
        await self._manager.async_set_capture_enabled(False)
        self.async_write_ha_state()
