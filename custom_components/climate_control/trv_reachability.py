"""TRV reachability: whether the TRVs of a room can take commands."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

from .target_resolver import TrvMode

OFFLINE_AFTER = timedelta(minutes=30)


class TrvReachability:
    """Tracks the TRVs of one room through their climate entities and sensors.

    A TRV is unreachable while its climate entity or the temperature sensor of its
    device is unavailable: on a bridge outage the climate entity of a tado TRV
    only freezes with its old values (ticket 01). A TRV takes commands while it is
    reachable and reports a valid mode. A TRV that could not take commands is
    handed to `on_back` as soon as it can again. A new state of a TRV that took
    commands before and still does goes to `on_report`, with the state before;
    frozen values and the return from an outage never do. A TRV unreachable for longer than
    `OFFLINE_AFTER` is offline; `on_offline_changed` reports changes.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        trvs: list[str],
        *,
        on_back: Callable[[str], None],
        on_report: Callable[[str, State | None], None],
        on_offline_changed: Callable[[], None],
    ) -> None:
        """Find the temperature sensor on the device of each TRV."""
        self._hass = hass
        self._sensors = {trv: _temperature_sensor(hass, trv) for trv in trvs}
        self._trv_of = {trv: trv for trv in trvs} | {
            sensor: trv for trv, sensor in self._sensors.items() if sensor is not None
        }
        self._on_back = on_back
        self._on_report = on_report
        self._on_offline_changed = on_offline_changed
        self._missed: set[str] = set()
        self._offline: frozenset[str] = frozenset()
        self._cancel_offline_check: CALLBACK_TYPE | None = None

    @property
    def entities(self) -> list[str]:
        """Return the climate entities of the TRVs and the sensors on their devices."""
        return list(self._trv_of)

    @property
    def offline(self) -> frozenset[str]:
        """Return the TRVs unreachable for longer than `OFFLINE_AFTER`."""
        return self._offline

    @callback
    def async_start(self) -> CALLBACK_TYPE:
        """Follow the TRVs; return the function that stops following them."""
        self._missed = {trv for trv in self._sensors if not self.takes_commands(trv)}
        unsubscribe = async_track_state_change_event(
            self._hass, list(self._trv_of), self._changed
        )
        self._update_offline()

        @callback
        def stop() -> None:
            unsubscribe()
            self._cancel_pending_offline_check()

        return stop

    @callback
    def takes_commands(self, trv: str) -> bool:
        """Return whether `trv` is reachable and reports a valid mode."""
        state = self._hass.states.get(trv)
        return (
            state is not None
            and state.state in (TrvMode.HEAT, TrvMode.OFF)
            and self._unreachable_since(trv) is None
        )

    @callback
    def _changed(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        trv = self._trv_of[entity_id]
        if not self.takes_commands(trv):
            self._missed.add(trv)
        elif trv in self._missed:
            self._missed.discard(trv)
            self._on_back(trv)
        elif entity_id == trv:
            self._on_report(trv, event.data["old_state"])
        self._update_offline()

    @callback
    def _unreachable_since(self, trv: str) -> datetime | None:
        entities = [trv] if (sensor := self._sensors[trv]) is None else [trv, sensor]
        return min(
            (
                state.last_changed
                for entity in entities
                if (state := self._hass.states.get(entity)) is not None
                and state.state == STATE_UNAVAILABLE
            ),
            default=None,
        )

    @callback
    def _update_offline(self, _now: datetime | None = None) -> None:
        self._cancel_pending_offline_check()
        now = dt_util.utcnow()
        offline: set[str] = set()
        next_check: datetime | None = None
        for trv in self._sensors:
            if (since := self._unreachable_since(trv)) is None:
                continue
            if (offline_at := since + OFFLINE_AFTER) <= now:
                offline.add(trv)
            elif next_check is None or offline_at < next_check:
                next_check = offline_at
        if next_check is not None:
            self._cancel_offline_check = async_track_point_in_utc_time(
                self._hass, self._update_offline, next_check
            )
        if offline != self._offline:
            self._offline = frozenset(offline)
            self._on_offline_changed()

    @callback
    def _cancel_pending_offline_check(self) -> None:
        if self._cancel_offline_check is not None:
            self._cancel_offline_check()
            self._cancel_offline_check = None


def _temperature_sensor(hass: HomeAssistant, trv: str) -> str | None:
    """Return the temperature sensor on the device of `trv`, if there is one."""
    registry = er.async_get(hass)
    entry = registry.async_get(trv)
    if entry is None or entry.device_id is None:
        return None
    return next(
        (
            sibling.entity_id
            for sibling in er.async_entries_for_device(registry, entry.device_id)
            if sibling.domain == Platform.SENSOR
            and (sibling.device_class or sibling.original_device_class)
            == SensorDeviceClass.TEMPERATURE
        ),
        None,
    )
