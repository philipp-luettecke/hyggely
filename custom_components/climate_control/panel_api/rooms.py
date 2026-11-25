"""Panel API, room overview: subscribe to all rooms, return a room to auto."""

from __future__ import annotations

from typing import Any

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util
import probatio

from ..const import SIGNAL_ROOMS_CHANGED
from ..reason_text import async_load_reason_texts, reason_text
from ..room_controller import RoomController
from ..target_resolver import RoomMode
from .common import loaded_runtime_data, room_controller_or_error


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the commands of the room overview."""
    websocket_api.async_register_command(hass, _subscribe_rooms)
    websocket_api.async_register_command(hass, _return_to_auto)


@websocket_api.websocket_command(
    {probatio.Required("type"): "climate_control/rooms/subscribe"}
)
@websocket_api.require_admin
@websocket_api.async_response
async def _subscribe_rooms(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send all rooms now and after every change, also across reloads."""
    await async_load_reason_texts(hass)

    @callback
    def _send_rooms() -> None:
        if (runtime_data := loaded_runtime_data(hass)) is None:
            return
        rooms = [_room(hass, controller) for controller in runtime_data.rooms.values()]
        connection.send_message(
            websocket_api.event_message(msg["id"], {"rooms": rooms})
        )

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_ROOMS_CHANGED, _send_rooms
    )
    connection.send_result(msg["id"])
    _send_rooms()


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "climate_control/room/return_to_auto",
        probatio.Required("room_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def _return_to_auto(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """End the override or off of a room: it follows its schedule again."""
    if (controller := room_controller_or_error(hass, connection, msg)) is None:
        return
    await controller.async_set_room_mode(RoomMode.AUTO)
    connection.send_result(msg["id"])


@callback
def _room(hass: HomeAssistant, controller: RoomController) -> dict[str, Any]:
    reason = controller.reason
    return {
        "room_id": controller.room_id,
        "name": controller.name,
        "current_temperature": controller.current_temperature,
        "target_temperature": controller.target_temperature,
        "room_mode": controller.room_mode,
        "reason": (
            reason_text(hass, reason.code, reason.params, dt_util.utcnow())
            if reason
            else None
        ),
        "reason_code": reason.code if reason else None,
    }
