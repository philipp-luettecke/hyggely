"""House mode and vacation end of the main entry, kept across restarts."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .target_resolver import HouseMode

STORAGE_VERSION = 1


def _storage_key(entry_id: str) -> str:
    return f"{DOMAIN}.{entry_id}.house_mode"


def house_device_info(entry_id: str) -> DeviceInfo:
    """Return the device of the house; the global entities belong to it."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        translation_key="house",
        manufacturer="Climate Control",
        model="House",
        entry_type=DeviceEntryType.SERVICE,
    )


class HouseModeController:
    """Holds the house mode and the vacation end; the one place that changes them.

    Vacation needs a vacation end in the future and returns to auto once it is
    reached, also when that happened while Home Assistant was down. Every change
    is written at once, so it survives a restart that never unloads the entry.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Use the storage file of the main entry `entry`."""
        self._hass = hass
        self._entry = entry
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, _storage_key(entry.entry_id)
        )
        self._house_mode = HouseMode.AUTO
        self._vacation_end: datetime | None = None
        self._listeners: list[Callable[[], None]] = []
        self._cancel_vacation_end: CALLBACK_TYPE | None = None

    @property
    def house_mode(self) -> HouseMode:
        """Return the house mode."""
        return self._house_mode

    @property
    def vacation_end(self) -> datetime | None:
        """Return when the vacation ends (None: never set)."""
        return self._vacation_end

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Call `listener` whenever house mode or vacation end change."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    async def async_start(self) -> None:
        """Load the saved state; a vacation that ended meanwhile is auto."""
        data = await self._store.async_load() or {}
        self._house_mode = HouseMode(data.get("house_mode", HouseMode.AUTO))
        if (vacation_end := data.get("vacation_end")) is not None:
            self._vacation_end = dt_util.parse_datetime(vacation_end)
        await self._async_follow_vacation_end()

    @callback
    def async_stop(self) -> None:
        """Stop waiting for the vacation end."""
        self._cancel_pending_vacation_end()

    async def async_set_house_mode(self, house_mode: HouseMode) -> None:
        """Switch the house mode; vacation needs a vacation end in the future."""
        if house_mode is HouseMode.VACATION and not self._vacation_end_ahead():
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="vacation_end_not_ahead"
            )
        self._house_mode = house_mode
        await self._async_follow_vacation_end()

    async def async_set_vacation_end(self, vacation_end: datetime) -> None:
        """Set the vacation end; one already passed ends a vacation at once."""
        self._vacation_end = vacation_end
        await self._async_follow_vacation_end()

    def _vacation_end_ahead(self) -> bool:
        return self._vacation_end is not None and self._vacation_end > dt_util.utcnow()

    async def _async_follow_vacation_end(self) -> None:
        """End a vacation whose end passed, wait for a future one, save, notify."""
        self._cancel_pending_vacation_end()
        if self._house_mode is HouseMode.VACATION:
            if self._vacation_end_ahead():
                assert self._vacation_end is not None
                self._cancel_vacation_end = async_track_point_in_utc_time(
                    self._hass, self._vacation_end_reached, self._vacation_end
                )
            else:
                self._house_mode = HouseMode.AUTO
        await self._store.async_save(
            {
                "house_mode": self._house_mode.value,
                "vacation_end": (
                    self._vacation_end.isoformat() if self._vacation_end else None
                ),
            }
        )
        for listener in list(self._listeners):
            listener()

    @callback
    def _vacation_end_reached(self, _now: datetime) -> None:
        self._cancel_vacation_end = None
        self._entry.async_create_task(
            self._hass, self._async_follow_vacation_end(), "end vacation"
        )

    @callback
    def _cancel_pending_vacation_end(self) -> None:
        if self._cancel_vacation_end is not None:
            self._cancel_vacation_end()
            self._cancel_vacation_end = None


async def async_remove_house_mode(hass: HomeAssistant, entry_id: str) -> None:
    """Delete the saved house mode of a removed main entry."""
    store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, _storage_key(entry_id))
    await store.async_remove()
