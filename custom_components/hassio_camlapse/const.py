"""Constants for the Hassio Timelapse integration."""

DOMAIN = "hassio_camlapse"
CONF_CAMERA_ENTITY_ID = "camera_entity_id"
CONF_INTERVAL_SECONDS = "interval_seconds"
CONF_SNAPSHOT_PATH = "snapshot_path"
CONF_VIDEO_PATH = "video_path"
CONF_OUTPUT_FPS = "output_fps"
CONF_IMAGE_RETENTION_DAYS = "image_retention_days"
CONF_VIDEO_RETENTION_DAYS = "video_retention_days"
CONF_VIDEOS_PER_DAY = "videos_per_day"
CONF_OUTPUT_CODEC = "output_codec"

DEFAULT_NAME = "Hassio CamLapse"
DEFAULT_INTERVAL_SECONDS = 60
DEFAULT_SNAPSHOT_PATH = "/media/timelapse"
DEFAULT_VIDEO_PATH = "/media/timelapse"
DEFAULT_OUTPUT_FPS = 10
DEFAULT_IMAGE_RETENTION_DAYS = 7
DEFAULT_VIDEO_RETENTION_DAYS = 30
DEFAULT_VIDEOS_PER_DAY = 1
DEFAULT_OUTPUT_CODEC = "libx264"
