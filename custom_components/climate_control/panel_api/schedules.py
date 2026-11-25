"""Panel API, schedule of a room (ticket 18): assign a schedule to a room.

Schedules themselves are read, written and deleted by the panel through the
native `schedule/*` commands.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components import websocket_api
from homeassistant.components.schedule.const import DOMAIN as SCHEDULE_DOMAIN
from homeassistant.components.websocket_api import ActiveConnection
from homeassistant.core import HomeAssistant, callback, split_entity_id
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import probatio

from ..const import CONF_SCHEDULE, DOMAIN, SIGNAL_ROOMS_CHANGED, SUBENTRY_TYPE_ROOM
from .common import room_controller_or_error

ERR_SCHEDULE_NOT_FOUND = "schedule_not_found"


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the commands of the schedule of a room."""
    websocket_api.async_register_command(hass, _subscribe_schedules)
    websocket_api.async_register_command(hass, _assign_schedule)


@websocket_api.websocket_command(
    {probatio.Required("type"): "climate_control/schedules/subscribe"}
)
@websocket_api.require_admin
@callback
def _subscribe_schedules(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send the schedule of every room and all schedule helpers, now and on change.

    Changes are reassigned rooms (the main entry reloads) and created, renamed
    or deleted schedule helpers.
    """

    @callback
    def _send(*_args: Any) -> None:
        connection.send_message(
            websocket_api.event_message(msg["id"], _assignments(hass))
        )

    @callback
    def _is_schedule(event_data: er.EventEntityRegistryUpdatedData) -> bool:
        return split_entity_id(event_data["entity_id"])[0] == SCHEDULE_DOMAIN

    unsubscribers = [
        async_dispatcher_connect(hass, SIGNAL_ROOMS_CHANGED, _send),
        hass.bus.async_listen(
            er.EVENT_ENTITY_REGISTRY_UPDATED, _send, event_filter=_is_schedule
        ),
    ]

    @callback
    def _unsubscribe() -> None:
        while unsubscribers:
            unsubscribers.pop()()

    connection.subscriptions[msg["id"]] = _unsubscribe
    connection.send_result(msg["id"])
    _send()


@callback
def _assignments(hass: HomeAssistant) -> dict[str, Any]:
    registry = er.async_get(hass)
    entity_ids = {
        entity.entity_id
        for entity in registry.entities.values()
        if entity.domain == SCHEDULE_DOMAIN
    } | set(hass.states.async_entity_ids(SCHEDULE_DOMAIN))
    helpers = []
    for entity_id in entity_ids:
        entity = registry.async_get(entity_id)
        state = hass.states.get(entity_id)
        if state is not None:
            name = state.name
        elif entity is not None:
            name = entity.name or entity.original_name or entity_id
        else:
            name = entity_id
        helpers.append(
            {
                "entity_id": entity_id,
                "schedule_id": (
                    entity.unique_id
                    if entity is not None and entity.platform == SCHEDULE_DOMAIN
                    else None
                ),
                "name": name,
            }
        )
    return {
        "rooms": [
            {
                "room_id": subentry.subentry_id,
                "name": subentry.title,
                "entity_id": subentry.data.get(CONF_SCHEDULE),
            }
            for entry in hass.config_entries.async_entries(DOMAIN)
            for subentry in entry.get_subentries_of_type(SUBENTRY_TYPE_ROOM)
        ],
        "schedules": sorted(
            helpers, key=lambda helper: (helper["name"].casefold(), helper["entity_id"])
        ),
    }


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "climate_control/room/assign_schedule",
        probatio.Required("room_id"): str,
        probatio.Exclusive("entity_id", "schedule"): probatio.Any(str, None),
        probatio.Exclusive("schedule_id", "schedule"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def _assign_schedule(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Give the room a schedule helper, or none; the main entry reloads.

    The helper is given by its entity id or by the id `schedule/create`
    returned; neither means no schedule.
    """
    if room_controller_or_error(hass, connection, msg) is None:
        return
    registry = er.async_get(hass)
    entity_id: str | None = msg.get("entity_id")
    if "schedule_id" in msg:
        entity_id = registry.async_get_entity_id(
            SCHEDULE_DOMAIN, SCHEDULE_DOMAIN, msg["schedule_id"]
        )
        if entity_id is None:
            connection.send_error(msg["id"], ERR_SCHEDULE_NOT_FOUND, "Unknown schedule")
            return
    elif entity_id is not None and (
        split_entity_id(entity_id)[0] != SCHEDULE_DOMAIN
        or (hass.states.get(entity_id) is None and entity_id not in registry.entities)
    ):
        connection.send_error(msg["id"], ERR_SCHEDULE_NOT_FOUND, "Unknown schedule")
        return
    for entry in hass.config_entries.async_entries(DOMAIN):
        if (subentry := entry.subentries.get(msg["room_id"])) is None:
            continue
        data = {
            key: value for key, value in subentry.data.items() if key != CONF_SCHEDULE
        }
        if entity_id is not None:
            data[CONF_SCHEDULE] = entity_id
        hass.config_entries.async_update_subentry(entry, subentry, data=data)
    connection.send_result(msg["id"])
