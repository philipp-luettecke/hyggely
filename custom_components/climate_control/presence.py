"""Presence input: derives away from the configured persons and the presence delay."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from homeassistant.const import STATE_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

_COUNTS_AS_HOME = (STATE_HOME, STATE_UNKNOWN, STATE_UNAVAILABLE)


class Presence:
    """Tells whether the house is away: all persons not home for the presence delay.

    A person whose presence is missing, unknown or unavailable counts as home,
    so a lost phone never lowers the house. Without persons it is never away.
    """

    def __init__(
        self, hass: HomeAssistant, persons: Sequence[str], presence_delay: timedelta
    ) -> None:
        """Follow `persons` (person entity ids)."""
        self._hass = hass
        self._persons = list(persons)
        self._presence_delay = presence_delay
        self._all_gone_since: datetime | None = None
        self._away = False
        self._listeners: list[Callable[[], None]] = []
        self._unsubscribe: CALLBACK_TYPE | None = None
        self._cancel_timer: CALLBACK_TYPE | None = None

    @property
    def away(self) -> bool:
        """Return whether the house is away."""
        return self._away

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Call `listener` whenever away changes; return the unsubscriber."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    @callback
    def async_start(self) -> None:
        """Derive away from the current presences and follow their changes.

        Persons already gone count from their last change, so reloading the
        entry keeps an away house away.
        """
        if self._all_gone():
            self._all_gone_since = max(
                state.last_changed
                for person in self._persons
                if (state := self._hass.states.get(person)) is not None
            )
        if self._persons:
            self._unsubscribe = async_track_state_change_event(
                self._hass, self._persons, self._presence_changed
            )
        self._update()

    @callback
    def async_stop(self) -> None:
        """Stop following the persons."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        self._cancel_pending_timer()

    @callback
    def _presence_changed(self, _event: Event[EventStateChangedData]) -> None:
        if not self._all_gone():
            self._all_gone_since = None
        elif self._all_gone_since is None:
            self._all_gone_since = dt_util.utcnow()
        self._update()

    @callback
    def _presence_delay_passed(self, _now: datetime) -> None:
        self._cancel_timer = None
        self._update()

    @callback
    def _update(self) -> None:
        self._cancel_pending_timer()
        away = False
        if self._all_gone_since is not None:
            away_from = self._all_gone_since + self._presence_delay
            away = dt_util.utcnow() >= away_from
            if not away:
                self._cancel_timer = async_track_point_in_utc_time(
                    self._hass, self._presence_delay_passed, away_from
                )
        if away != self._away:
            self._away = away
            for listener in list(self._listeners):
                listener()

    def _all_gone(self) -> bool:
        return bool(self._persons) and all(
            (state := self._hass.states.get(person)) is not None
            and state.state not in _COUNTS_AS_HOME
            for person in self._persons
        )

    @callback
    def _cancel_pending_timer(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None
