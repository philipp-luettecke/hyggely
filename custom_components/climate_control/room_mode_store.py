"""Room modes and targets kept across restarts of Home Assistant and reloads."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .target_resolver import RoomMode

STORAGE_VERSION = 1


def _storage_key(entry_id: str) -> str:
    return f"{DOMAIN}.{entry_id}.room_modes"


@dataclass(frozen=True, kw_only=True)
class RoomModeChoice:
    """Room mode chosen for a room, with override temperature and override expiry.

    Heat carries `override_temperature`; heat and off end at `expires_at`
    (None: no expiry).
    """

    room_mode: RoomMode = RoomMode.AUTO
    override_temperature: float | None = None
    expires_at: datetime | None = None


class RoomModeStore:
    """Saves the room mode choice and the latest target of every room.

    Every change is written at once, so it survives a restart that never unloads
    the entry. The latest target lets the first decision after a restart tell
    whether the target changed meanwhile.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Use the storage file of the main entry `entry_id`."""
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, _storage_key(entry_id)
        )
        self._rooms: dict[str, dict[str, Any]] = {}
        self._targets: dict[str, float] = {}

    async def async_load(self, room_ids: Collection[str]) -> None:
        """Load what was saved; rooms that no longer exist are dropped."""
        data = await self._store.async_load() or {}
        self._rooms = {
            room_id: saved
            for room_id, saved in data.get("rooms", {}).items()
            if room_id in room_ids
        }
        self._targets = {
            room_id: target
            for room_id, target in data.get("targets", {}).items()
            if room_id in room_ids
        }

    def get(self, room_id: str) -> RoomModeChoice:
        """Return the saved choice of a room; auto if nothing is saved."""
        if (saved := self._rooms.get(room_id)) is None:
            return RoomModeChoice()
        expires_at = saved.get("expires_at")
        return RoomModeChoice(
            room_mode=RoomMode(saved["room_mode"]),
            override_temperature=saved.get("override_temperature"),
            expires_at=dt_util.parse_datetime(expires_at) if expires_at else None,
        )

    async def async_save(self, room_id: str, choice: RoomModeChoice) -> None:
        """Save the choice of a room; auto needs nothing to be restored."""
        if choice.room_mode is RoomMode.AUTO:
            self._rooms.pop(room_id, None)
        else:
            self._rooms[room_id] = {
                "room_mode": choice.room_mode.value,
                "override_temperature": choice.override_temperature,
                "expires_at": (
                    choice.expires_at.isoformat() if choice.expires_at else None
                ),
            }
        await self._async_write()

    def target(self, room_id: str) -> float | None:
        """Return the latest target of a room; None if it never had one."""
        return self._targets.get(room_id)

    async def async_save_target(self, room_id: str, target: float) -> None:
        """Save the latest target of a room."""
        self._targets[room_id] = target
        await self._async_write()

    async def _async_write(self) -> None:
        await self._store.async_save({"rooms": self._rooms, "targets": self._targets})


async def async_remove_room_modes(hass: HomeAssistant, entry_id: str) -> None:
    """Delete the saved choices and targets of a removed main entry."""
    store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, _storage_key(entry_id))
    await store.async_remove()
