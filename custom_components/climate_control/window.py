"""Window input: tells since when a room's window is open."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from homeassistant.const import STATE_ON
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


class WindowContacts:
    """Tells whether a room's window is open: any contact open for the window delay.

    A contact is open while its state is `on`; unknown, unavailable or missing
    contacts count as closed, so an empty battery never keeps a room cold. The
    window is open since the earliest moment a still open contact opened, and
    closed as soon as the last contact closes.
    """

    def __init__(
        self, hass: HomeAssistant, contacts: Sequence[str], window_delay: timedelta
    ) -> None:
        """Follow `contacts` (binary sensor entity ids)."""
        self._hass = hass
        self._contacts = list(contacts)
        self._window_delay = window_delay
        self._open_since: datetime | None = None
        self._on_change: Callable[[], None] | None = None
        self._cancel_timer: CALLBACK_TYPE | None = None

    @property
    def open_since(self) -> datetime | None:
        """Return since when the window is open; None while it counts as closed."""
        return self._open_since

    @callback
    def async_track(self, on_change: Callable[[], None]) -> CALLBACK_TYPE:
        """Derive the window from the contacts and call `on_change` when it changes.

        Contacts already open count from their last change, so reloading the
        entry keeps an open window open. Returns the unsubscriber.
        """
        self._update()
        self._on_change = on_change
        unsubscribe = (
            async_track_state_change_event(
                self._hass, self._contacts, self._contact_changed
            )
            if self._contacts
            else None
        )

        @callback
        def stop() -> None:
            self._on_change = None
            if unsubscribe is not None:
                unsubscribe()
            self._cancel_pending_timer()

        return stop

    @callback
    def _contact_changed(self, _event: Event[EventStateChangedData]) -> None:
        self._update()

    @callback
    def _window_delay_passed(self, _now: datetime) -> None:
        self._cancel_timer = None
        self._update()

    @callback
    def _update(self) -> None:
        self._cancel_pending_timer()
        opened = [
            state.last_changed
            for contact in self._contacts
            if (state := self._hass.states.get(contact)) is not None
            and state.state == STATE_ON
        ]
        open_since = None
        if opened:
            first_opened = min(opened)
            open_from = first_opened + self._window_delay
            if dt_util.utcnow() >= open_from:
                open_since = first_opened
            else:
                self._cancel_timer = async_track_point_in_utc_time(
                    self._hass, self._window_delay_passed, open_from
                )
        if open_since != self._open_since:
            self._open_since = open_since
            if self._on_change is not None:
                self._on_change()

    @callback
    def _cancel_pending_timer(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None
