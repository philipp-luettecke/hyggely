"""Diagnostics: settings, room snapshots and recent decisions, without persons."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant

from . import HyggelyConfigEntry
from .const import CONF_NOTIFY_TARGETS, CONF_PERSONS
from .room_controller import RoomController

TO_REDACT = {CONF_PERSONS, CONF_NOTIFY_TARGETS}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HyggelyConfigEntry
) -> dict[str, Any]:
    """Return the diagnostics of the main entry and its rooms."""
    return {
        "settings": async_redact_data(dict(entry.options), TO_REDACT),
        "rooms": [
            _room(entry.subentries[room_id], controller)
            for room_id, controller in entry.runtime_data.rooms.items()
        ],
    }


def _room(subentry: ConfigSubentry, controller: RoomController) -> dict[str, Any]:
    snapshot = controller.snapshot
    return {
        "room_id": subentry.subentry_id,
        "name": subentry.title,
        "settings": dict(subentry.data),
        "snapshot": _json(asdict(snapshot)) if snapshot else None,
        "decisions": [
            _json({"decided_at": decided_at, **asdict(decision)})
            for decided_at, decision in controller.recent_decisions
        ],
    }


def _json(value: Any) -> Any:
    """Turn datetimes, enums and enum keys of decisions into JSON values."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {_json(key): _json(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json(item) for item in value]
    return value
