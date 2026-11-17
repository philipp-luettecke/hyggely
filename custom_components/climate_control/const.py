"""Constants for the climate_control integration."""

from typing import Final

DOMAIN: Final = "climate_control"

CONF_PERSONS: Final = "persons"
CONF_AWAY_DELAY: Final = "away_delay"
CONF_NOTIFY_TARGETS: Final = "notify_targets"
CONF_QUIET_START: Final = "quiet_start"
CONF_QUIET_END: Final = "quiet_end"
CONF_AWAY_TEMPERATURE: Final = "away_temperature"
CONF_VACATION_TEMPERATURE: Final = "vacation_temperature"
CONF_FROST_TEMPERATURE: Final = "frost_temperature"
CONF_OVERRIDE_EXPIRY_POLICY: Final = "override_expiry_policy"
CONF_OVERRIDE_EXPIRY_DURATION: Final = "override_expiry_duration"
CONF_WINDOW_DELAY: Final = "window_delay"

OVERRIDE_EXPIRY_NEXT_BLOCK: Final = "next_block"
OVERRIDE_EXPIRY_DURATION: Final = "duration"
OVERRIDE_EXPIRY_EARLIEST: Final = "earliest"
OVERRIDE_EXPIRY_POLICIES: Final = [
    OVERRIDE_EXPIRY_NEXT_BLOCK,
    OVERRIDE_EXPIRY_DURATION,
    OVERRIDE_EXPIRY_EARLIEST,
]

DEFAULT_AWAY_DELAY: Final = {"hours": 0, "minutes": 30, "seconds": 0}
DEFAULT_QUIET_START: Final = "22:00:00"
DEFAULT_QUIET_END: Final = "07:00:00"
DEFAULT_AWAY_TEMPERATURE: Final = 17.0
DEFAULT_VACATION_TEMPERATURE: Final = 15.0
DEFAULT_FROST_TEMPERATURE: Final = 7.0
DEFAULT_OVERRIDE_EXPIRY_POLICY: Final = OVERRIDE_EXPIRY_EARLIEST
DEFAULT_OVERRIDE_EXPIRY_DURATION: Final = {"hours": 3, "minutes": 0, "seconds": 0}
DEFAULT_WINDOW_DELAY: Final = {"hours": 0, "minutes": 1, "seconds": 0}

SUBENTRY_TYPE_ROOM: Final = "room"

CONF_NAME: Final = "name"
CONF_TRVS: Final = "trvs"
CONF_SCHEDULE: Final = "schedule"
CONF_COMFORT_TEMPERATURE: Final = "comfort_temperature"
CONF_NIGHT_TEMPERATURE: Final = "night_temperature"
CONF_ECO_TEMPERATURE: Final = "eco_temperature"
CONF_LEAD_TIME: Final = "lead_time"
CONF_AREA: Final = "area"

DEFAULT_COMFORT_TEMPERATURE: Final = 21.0
DEFAULT_NIGHT_TEMPERATURE: Final = 17.0
DEFAULT_ECO_TEMPERATURE: Final = 18.0
DEFAULT_LEAD_TIME: Final = {"hours": 0, "minutes": 0, "seconds": 0}

TRV_MIN_TEMPERATURE: Final = 5.0
TRV_MAX_TEMPERATURE: Final = 25.0
TEMPERATURE_STEP: Final = 0.5
