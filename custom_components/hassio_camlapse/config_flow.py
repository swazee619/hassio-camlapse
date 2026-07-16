"""Config flow for Hassio Timelapse integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_CAMERA_ENTITY_ID,
    CONF_INTERVAL_SECONDS,
    CONF_SNAPSHOT_PATH,
    CONF_VIDEO_PATH,
    CONF_OUTPUT_FPS,
    CONF_IMAGE_RETENTION_DAYS,
    CONF_VIDEO_RETENTION_DAYS,
    CONF_VIDEOS_PER_DAY,
    DEFAULT_INTERVAL_SECONDS,
    DEFAULT_SNAPSHOT_PATH,
    DEFAULT_VIDEO_PATH,
    DEFAULT_OUTPUT_FPS,
    DEFAULT_IMAGE_RETENTION_DAYS,
    DEFAULT_VIDEO_RETENTION_DAYS,
    DEFAULT_VIDEOS_PER_DAY,
    DEFAULT_OUTPUT_CODEC,
    CONF_OUTPUT_CODEC,
    CONF_START_TIME,
    CONF_END_TIME,
    DEFAULT_START_TIME,
    DEFAULT_END_TIME,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CAMERA_ENTITY_ID): selector.EntitySelector(selector.EntitySelectorConfig(domain="camera")),
        vol.Required(CONF_INTERVAL_SECONDS, default=DEFAULT_INTERVAL_SECONDS): int,
        vol.Required(CONF_SNAPSHOT_PATH, default=DEFAULT_SNAPSHOT_PATH): cv.string,
        vol.Required(CONF_VIDEO_PATH, default=DEFAULT_VIDEO_PATH): cv.string,
        vol.Required(CONF_OUTPUT_FPS, default=DEFAULT_OUTPUT_FPS): int,
        vol.Required(CONF_IMAGE_RETENTION_DAYS, default=DEFAULT_IMAGE_RETENTION_DAYS): int,
        vol.Required(CONF_VIDEO_RETENTION_DAYS, default=DEFAULT_VIDEO_RETENTION_DAYS): int,
        vol.Required(CONF_VIDEOS_PER_DAY, default=DEFAULT_VIDEOS_PER_DAY): int,
        vol.Required(CONF_OUTPUT_CODEC, default=DEFAULT_OUTPUT_CODEC): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["libx264", "libx265"],
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="output_codec",
            )
        ),
        vol.Required(CONF_START_TIME, default=DEFAULT_START_TIME): selector.TimeSelector(),
        vol.Required(CONF_END_TIME, default=DEFAULT_END_TIME): selector.TimeSelector(),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hassio Timelapse."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_CAMERA_ENTITY_ID], data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration."""
        errors: dict[str, str] = {}

        # Get current config
        if not (config_entry := self.hass.config_entries.async_get_entry(self.context["entry_id"])):
            return self.async_abort(reason="existing_entry_not_found")

        if user_input is not None:
            # Update config entry with new data
            return self.async_update_reload_and_abort(config_entry, data={**config_entry.data, **user_input})

        # Prepare form with current values as defaults
        current_config = config_entry.data

        # Fallback to base_path or defaults if new paths are missing (migration scenario handled in init, but good for UI)
        default_snapshot = current_config.get(CONF_SNAPSHOT_PATH, DEFAULT_SNAPSHOT_PATH)

        default_video = current_config.get(CONF_VIDEO_PATH, DEFAULT_VIDEO_PATH)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_CAMERA_ENTITY_ID, default=current_config.get(CONF_CAMERA_ENTITY_ID)
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="camera")),
                vol.Required(CONF_INTERVAL_SECONDS, default=current_config.get(CONF_INTERVAL_SECONDS)): int,
                vol.Required(CONF_SNAPSHOT_PATH, default=default_snapshot): cv.string,
                vol.Required(CONF_VIDEO_PATH, default=default_video): cv.string,
                vol.Required(CONF_OUTPUT_FPS, default=current_config.get(CONF_OUTPUT_FPS)): int,
                vol.Required(
                    CONF_IMAGE_RETENTION_DAYS,
                    default=current_config.get(CONF_IMAGE_RETENTION_DAYS, DEFAULT_IMAGE_RETENTION_DAYS),
                ): int,
                vol.Required(
                    CONF_VIDEO_RETENTION_DAYS,
                    default=current_config.get(CONF_VIDEO_RETENTION_DAYS, DEFAULT_VIDEO_RETENTION_DAYS),
                ): int,
                vol.Required(
                    CONF_VIDEOS_PER_DAY,
                    default=current_config.get(CONF_VIDEOS_PER_DAY, DEFAULT_VIDEOS_PER_DAY),
                ): int,
                vol.Required(
                    CONF_OUTPUT_CODEC,
                    default=current_config.get(CONF_OUTPUT_CODEC, DEFAULT_OUTPUT_CODEC),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["libx264", "libx265"],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="output_codec",
                    )
                ),
                vol.Required(
                    CONF_START_TIME,
                    default=current_config.get(CONF_START_TIME, DEFAULT_START_TIME),
                ): selector.TimeSelector(),
                vol.Required(
                    CONF_END_TIME,
                    default=current_config.get(CONF_END_TIME, DEFAULT_END_TIME),
                ): selector.TimeSelector(),
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema,
            errors=errors,
        )
