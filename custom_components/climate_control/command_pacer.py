"""Command pacer: catch-up commands to the TRVs go out one after another."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

CATCH_UP_SPACING = timedelta(seconds=2)


class CommandPacer:
    """Runs catch-up jobs of all rooms `CATCH_UP_SPACING` apart.

    Catch-up jobs bring TRVs up to date in bulk: on the start of Home Assistant
    and when TRVs return, e.g. together after a bridge outage. Spacing them keeps
    the bridge from a flood of commands. The first job runs at once.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Pace the jobs of the main entry `entry`."""
        self._hass = hass
        self._entry = entry
        self._next_slot: datetime | None = None
        self._pending: set[CALLBACK_TYPE] = set()

    @callback
    def async_enqueue(
        self, name: str, job: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        """Run `job` in the next free slot."""
        now = dt_util.utcnow()
        slot = now if self._next_slot is None else max(now, self._next_slot)
        self._next_slot = slot + CATCH_UP_SPACING
        if slot <= now:
            self._entry.async_create_task(self._hass, job(), name)
            return

        @callback
        def run(_now: datetime) -> None:
            self._pending.discard(cancel)
            self._entry.async_create_task(self._hass, job(), name)

        cancel = async_track_point_in_utc_time(self._hass, run, slot)
        self._pending.add(cancel)

    @callback
    def async_stop(self) -> None:
        """Drop the jobs still waiting for their slot."""
        while self._pending:
            self._pending.pop()()
