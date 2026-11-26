"""Panel API, levels (ticket 19).

Level temperatures and lead time of a room, global temperatures for away,
vacation and frost protection.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
import probatio

from ..const import (
    CONF_AWAY_TEMPERATURE,
    CONF_COMFORT_TEMPERATURE,
    CONF_ECO_TEMPERATURE,
    CONF_FROST_TEMPERATURE,
    CONF_LEAD_TIME,
    CONF_NIGHT_TEMPERATURE,
    CONF_VACATION_TEMPERATURE,
    DEFAULT_LEAD_TIME,
    DEFAULT_NIGHT_TEMPERATURE,
    DOMAIN,
    TRV_MAX_TEMPERATURE,
    TRV_MIN_TEMPERATURE,
)
from .common import ERR_NOT_LOADED, loaded_runtime_data, room_controller_or_error

LEAD_TIME_MINUTES = "lead_time_minutes"
LEAD_TIME_STEP_MINUTES = 15
LEAD_TIME_MAX_MINUTES = 180


def _in_lead_time_steps(minutes: int) -> int:
    if minutes % LEAD_TIME_STEP_MINUTES:
        raise probatio.Invalid(f"not a multiple of {LEAD_TIME_STEP_MINUTES} minutes")
    return minutes


_TEMPERATURE = probatio.All(
    probatio.Coerce(float),
    probatio.Range(min=TRV_MIN_TEMPERATURE, max=TRV_MAX_TEMPERATURE),
)
_LEAD_TIME_MINUTES = probatio.All(
    int, probatio.Range(min=0, max=LEAD_TIME_MAX_MINUTES), _in_lead_time_steps
)
_GLOBAL_TEMPERATURES = (
    CONF_AWAY_TEMPERATURE,
    CONF_VACATION_TEMPERATURE,
    CONF_FROST_TEMPERATURE,
)


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the commands of the levels."""
    websocket_api.async_register_command(hass, _room_levels)
    websocket_api.async_register_command(hass, _set_room_levels)
    websocket_api.async_register_command(hass, _global_temperatures)
    websocket_api.async_register_command(hass, _set_global_temperatures)


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "hyggely/room/levels",
        probatio.Required("room_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def _room_levels(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send the level temperatures and the lead time of a room."""
    if (room := _room_or_error(hass, connection, msg)) is None:
        return
    data = room[1].data
    lead_time = timedelta(**data.get(CONF_LEAD_TIME, DEFAULT_LEAD_TIME))
    connection.send_result(
        msg["id"],
        {
            CONF_COMFORT_TEMPERATURE: data[CONF_COMFORT_TEMPERATURE],
            CONF_NIGHT_TEMPERATURE: data.get(
                CONF_NIGHT_TEMPERATURE, DEFAULT_NIGHT_TEMPERATURE
            ),
            CONF_ECO_TEMPERATURE: data[CONF_ECO_TEMPERATURE],
            LEAD_TIME_MINUTES: lead_time.total_seconds() / 60,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "hyggely/room/set_levels",
        probatio.Required("room_id"): str,
        probatio.Optional(CONF_COMFORT_TEMPERATURE): _TEMPERATURE,
        probatio.Optional(CONF_NIGHT_TEMPERATURE): _TEMPERATURE,
        probatio.Optional(CONF_ECO_TEMPERATURE): _TEMPERATURE,
        probatio.Optional(LEAD_TIME_MINUTES): _LEAD_TIME_MINUTES,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def _set_room_levels(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Change the level temperatures given; the room applies them at once."""
    if (room := _room_or_error(hass, connection, msg)) is None:
        return
    entry, subentry = room
    changes: dict[str, Any] = {
        key: msg[key]
        for key in (
            CONF_COMFORT_TEMPERATURE,
            CONF_NIGHT_TEMPERATURE,
            CONF_ECO_TEMPERATURE,
        )
        if key in msg
    }
    if LEAD_TIME_MINUTES in msg:
        hours, minutes = divmod(msg[LEAD_TIME_MINUTES], 60)
        changes[CONF_LEAD_TIME] = {"hours": hours, "minutes": minutes, "seconds": 0}
    hass.config_entries.async_update_subentry(
        entry, subentry, data={**subentry.data, **changes}
    )
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {probatio.Required("type"): "hyggely/house/temperatures"}
)
@websocket_api.require_admin
@websocket_api.async_response
async def _global_temperatures(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send the temperatures for away, vacation and frost protection."""
    if (entry := _main_entry_or_error(hass, connection, msg)) is None:
        return
    connection.send_result(
        msg["id"], {key: entry.options[key] for key in _GLOBAL_TEMPERATURES}
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "hyggely/house/set_temperatures",
        **{probatio.Optional(key): _TEMPERATURE for key in _GLOBAL_TEMPERATURES},
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def _set_global_temperatures(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Change the global temperatures given; all rooms apply them at once."""
    if (entry := _main_entry_or_error(hass, connection, msg)) is None:
        return
    changes = {key: msg[key] for key in _GLOBAL_TEMPERATURES if key in msg}
    hass.config_entries.async_update_entry(entry, options={**entry.options, **changes})
    connection.send_result(msg["id"])


@callback
def _main_entry_or_error(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> ConfigEntry | None:
    """Return the loaded main entry; answer with an error and None if not loaded."""
    if (runtime_data := loaded_runtime_data(hass)) is None:
        connection.send_error(
            msg["id"], ERR_NOT_LOADED, "The heating control is not loaded"
        )
        return None
    return next(
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if getattr(entry, "runtime_data", None) is runtime_data
    )


@callback
def _room_or_error(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> tuple[ConfigEntry, ConfigSubentry] | None:
    """Return the main entry and the settings of the room `msg["room_id"]`.

    Answers with an error and returns None if the room is unknown.
    """
    if room_controller_or_error(hass, connection, msg) is None:
        return None
    return next(
        (entry, entry.subentries[msg["room_id"]])
        for entry in hass.config_entries.async_entries(DOMAIN)
        if msg["room_id"] in entry.subentries
    )
