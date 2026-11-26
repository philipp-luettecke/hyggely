"""Shared by the commands of the panel API: the loaded main entry and its rooms."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback

from ..const import DOMAIN

if TYPE_CHECKING:
    from .. import RuntimeData
    from ..room_controller import RoomController

ERR_NOT_LOADED = "not_loaded"
ERR_ROOM_NOT_FOUND = "room_not_found"


@callback
def loaded_runtime_data(hass: HomeAssistant) -> RuntimeData | None:
    """Return the live objects of the main entry; None while it is not loaded.

    The entry counts from the end of its setup on, when it announces its
    rooms, though it is marked loaded only afterwards.
    """
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state in (
            ConfigEntryState.LOADED,
            ConfigEntryState.SETUP_IN_PROGRESS,
        ) and (runtime_data := getattr(entry, "runtime_data", None)):
            result: RuntimeData = runtime_data
            return result
    return None


@callback
def room_controller_or_error(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> RoomController | None:
    """Return the room `msg["room_id"]`; answer with an error and None if unknown."""
    if (runtime_data := loaded_runtime_data(hass)) is None:
        connection.send_error(
            msg["id"], ERR_NOT_LOADED, "The heating control is not loaded"
        )
        return None
    if (controller := runtime_data.rooms.get(msg["room_id"])) is None:
        connection.send_error(msg["id"], ERR_ROOM_NOT_FOUND, "Unknown room")
        return None
    return controller
