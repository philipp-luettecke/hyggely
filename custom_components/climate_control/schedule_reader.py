"""Schedule reader: the effective level of a native schedule helper."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from homeassistant.const import STATE_ON
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import async_track_state_change_event

from .target_resolver import Level, ScheduleLevel

ATTR_NEXT_EVENT = "next_event"


class ScheduleReader:
    """Reads one schedule helper and reports changes to it.

    A block in progress means comfort, no block means eco. The next block boundary
    is the next transition of the helper.
    """

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        """Read the schedule helper `entity_id`."""
        self._hass = hass
        self._entity_id = entity_id

    @callback
    def async_track(self, on_change: Callable[[], None]) -> CALLBACK_TYPE:
        """Call `on_change` whenever the helper changes; return the unsubscriber."""

        @callback
        def _changed(event: Event[EventStateChangedData]) -> None:
            on_change()

        return async_track_state_change_event(self._hass, [self._entity_id], _changed)

    @callback
    def read(self) -> ScheduleLevel | None:
        """Return the effective level, or None while the helper has no state."""
        state = self._hass.states.get(self._entity_id)
        if state is None or state.state not in ("on", "off"):
            return None
        next_event = state.attributes.get(ATTR_NEXT_EVENT)
        return ScheduleLevel(
            level=Level.COMFORT if state.state == STATE_ON else Level.ECO,
            next_block_boundary=next_event
            if isinstance(next_event, datetime)
            else None,
        )
