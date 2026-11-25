"""Panel API, house (ticket 20).

House mode, vacation with its end, away with the configured persons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util
import probatio

from ..const import SIGNAL_ROOMS_CHANGED
from ..target_resolver import HouseMode
from .common import ERR_NOT_LOADED, loaded_runtime_data

if TYPE_CHECKING:
    from .. import RuntimeData


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the commands of the house."""
    websocket_api.async_register_command(hass, _subscribe_house)
    websocket_api.async_register_command(hass, _set_house_mode)
    websocket_api.async_register_command(hass, _start_vacation)


@websocket_api.websocket_command(
    {probatio.Required("type"): "climate_control/house/subscribe"}
)
@websocket_api.require_admin
@websocket_api.async_response
async def _subscribe_house(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send the house now and after every change, also across reloads."""
    followed: RuntimeData | None = None
    stop_following: list[CALLBACK_TYPE] = []

    @callback
    def _send_house(*_args: Any) -> None:
        if (runtime_data := loaded_runtime_data(hass)) is None:
            return
        connection.send_message(
            websocket_api.event_message(msg["id"], _house(hass, runtime_data))
        )

    @callback
    def _unfollow() -> None:
        while stop_following:
            stop_following.pop()()

    @callback
    def _follow_main_entry() -> None:
        """Follow the live objects of the main entry; they change on a reload."""
        nonlocal followed
        runtime_data = loaded_runtime_data(hass)
        if runtime_data is followed:
            return
        _unfollow()
        followed = runtime_data
        if runtime_data is None:
            return
        presence = runtime_data.presence
        stop_following.append(runtime_data.house_mode.async_add_listener(_send_house))
        stop_following.append(presence.async_add_listener(_send_house))
        if presence.persons:
            stop_following.append(
                async_track_state_change_event(hass, presence.persons, _send_house)
            )
        _send_house()

    stop_signal = async_dispatcher_connect(
        hass, SIGNAL_ROOMS_CHANGED, _follow_main_entry
    )

    @callback
    def _unsubscribe() -> None:
        stop_signal()
        _unfollow()

    connection.subscriptions[msg["id"]] = _unsubscribe
    connection.send_result(msg["id"])
    _follow_main_entry()


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "climate_control/house/set_mode",
        probatio.Required("house_mode"): probatio.In(
            [HouseMode.AUTO.value, HouseMode.OFF.value]
        ),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def _set_house_mode(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Switch the house to auto or off; vacation starts with its end only."""
    if (runtime_data := _runtime_data_or_error(hass, connection, msg)) is None:
        return
    await runtime_data.house_mode.async_set_house_mode(HouseMode(msg["house_mode"]))
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "climate_control/house/start_vacation",
        probatio.Required("end"): cv.datetime,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def _start_vacation(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Set the vacation end and start vacation; also moves the end of a vacation.

    An end without time zone is local time.
    """
    if (runtime_data := _runtime_data_or_error(hass, connection, msg)) is None:
        return
    try:
        await runtime_data.house_mode.async_start_vacation(dt_util.as_utc(msg["end"]))
    except ServiceValidationError as error:
        connection.send_error(msg["id"], str(error.translation_key), str(error))
        return
    connection.send_result(msg["id"])


@callback
def _runtime_data_or_error(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> RuntimeData | None:
    if (runtime_data := loaded_runtime_data(hass)) is None:
        connection.send_error(
            msg["id"], ERR_NOT_LOADED, "The heating control is not loaded"
        )
    return runtime_data


@callback
def _house(hass: HomeAssistant, runtime_data: RuntimeData) -> dict[str, Any]:
    house_mode = runtime_data.house_mode
    presence = runtime_data.presence
    vacation_end = house_mode.vacation_end
    return {
        "house_mode": house_mode.house_mode.value,
        "vacation_end": (
            dt_util.as_local(vacation_end).isoformat() if vacation_end else None
        ),
        "away": presence.away,
        "persons": [
            {
                "entity_id": person,
                "name": state.name if (state := hass.states.get(person)) else person,
                "presence": presence.person_presence(person),
            }
            for person in presence.persons
        ],
    }
