"""Repair issues: one per TRV of a room that is offline."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .room_controller import RoomController

ISSUE_TRV_OFFLINE = "trv_offline"


@callback
def async_track_offline_trvs(
    hass: HomeAssistant, entry: ConfigEntry, room: RoomController
) -> CALLBACK_TYPE:
    """Keep a repair issue for each offline TRV of `room`; return the unsubscriber.

    Stopping removes the issues of the room; a restarted room raises them again.
    """
    raised: set[str] = set()

    @callback
    def sync() -> None:
        offline = room.offline_trvs
        for trv in offline - raised:
            ir.async_create_issue(
                hass,
                DOMAIN,
                _issue_id(trv),
                config_entry_id=entry.entry_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_TRV_OFFLINE,
                translation_placeholders={
                    "trv": _name(hass, trv),
                    "room": room.name,
                },
            )
        for trv in raised - offline:
            ir.async_delete_issue(hass, DOMAIN, _issue_id(trv))
        raised.clear()
        raised.update(offline)

    unsubscribe = room.async_add_listener(sync)

    @callback
    def stop() -> None:
        unsubscribe()
        for trv in raised:
            ir.async_delete_issue(hass, DOMAIN, _issue_id(trv))

    return stop


def _issue_id(trv: str) -> str:
    return f"{ISSUE_TRV_OFFLINE}_{trv}"


def _name(hass: HomeAssistant, trv: str) -> str:
    state = hass.states.get(trv)
    if state is None:
        return trv
    return str(state.attributes.get(ATTR_FRIENDLY_NAME, trv))
