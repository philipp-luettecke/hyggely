"""Room controller: one per room, drives the TRVs from target resolver decisions."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from datetime import datetime

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    ATTR_TEMPERATURE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DECIDED_AT,
    ATTR_REASON_CODE,
    ATTR_REASON_PARAMS,
    ATTR_TARGET_TEMPERATURE,
    CONF_COMFORT_TEMPERATURE,
    CONF_ECO_TEMPERATURE,
    CONF_FROST_TEMPERATURE,
    CONF_SCHEDULE,
    CONF_TRVS,
    DATA_TARGETS_BEFORE_RELOAD,
    DOMAIN,
    EVENT_TARGET_CHANGED,
    room_entity_unique_id,
)
from .schedule_reader import ScheduleReader
from .target_resolver import (
    Decision,
    Level,
    Reason,
    RoomMode,
    RoomSnapshot,
    TrvMode,
    resolve,
)

RECENT_DECISIONS = 20


class RoomController:
    """Subscribes the inputs of a room, resolves its target and commands its TRVs.

    Commands go out only when a TRV deviates from the decision; for `heat` the
    mode always travels with the temperature because an off tado TRV silently
    ignores a temperature alone (ticket 01).
    """

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry
    ) -> None:
        """Create the controller for the room `subentry` of the main entry."""
        self._hass = hass
        self._entry = entry
        self.room_id = subentry.subentry_id
        self.name = subentry.title
        self._trvs: list[str] = list(subentry.data[CONF_TRVS])
        self._schedule = ScheduleReader(hass, subentry.data[CONF_SCHEDULE])
        self._level_temperatures = {
            Level.COMFORT: float(subentry.data[CONF_COMFORT_TEMPERATURE]),
            Level.ECO: float(subentry.data[CONF_ECO_TEMPERATURE]),
        }
        self._frost_temperature = float(entry.options[CONF_FROST_TEMPERATURE])
        self._room_mode = RoomMode.AUTO
        self._override_temperature: float | None = None
        self._mode_expires_at: datetime | None = None
        self._decision: Decision | None = None
        self._snapshot: RoomSnapshot | None = None
        self._recent_decisions: deque[tuple[datetime, Decision]] = deque(
            maxlen=RECENT_DECISIONS
        )
        self._target_before_reload = hass.data.get(DATA_TARGETS_BEFORE_RELOAD, {}).pop(
            self.room_id, None
        )
        self._listeners: list[Callable[[], None]] = []
        self._unsubscribers: list[CALLBACK_TYPE] = []
        self._cancel_reevaluation: CALLBACK_TYPE | None = None
        self._evaluation_lock = asyncio.Lock()

    @property
    def room_mode(self) -> RoomMode:
        """Return the room mode as last decided."""
        return self._decision.room_mode if self._decision else RoomMode.AUTO

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature of the room."""
        return self._decision.target_temperature if self._decision else None

    @property
    def reason(self) -> Reason | None:
        """Return why the room has its target."""
        return self._decision.reason if self._decision else None

    @property
    def snapshot(self) -> RoomSnapshot | None:
        """Return the inputs of the latest decision."""
        return self._snapshot

    @property
    def recent_decisions(self) -> list[tuple[datetime, Decision]]:
        """Return the latest distinct decisions with their time, oldest first."""
        return list(self._recent_decisions)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature reported by the TRV."""
        for trv in self._trvs:
            state = self._hass.states.get(trv)
            if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                continue
            value = state.attributes.get(ATTR_CURRENT_TEMPERATURE)
            if isinstance(value, int | float):
                return float(value)
        return None

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Call `listener` whenever the room changes; return the unsubscriber."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    async def async_start(self) -> None:
        """Subscribe the inputs and bring the TRVs into the decided state."""
        self._unsubscribers.append(
            self._schedule.async_track(self._async_request_evaluation)
        )
        self._unsubscribers.append(
            async_track_state_change_event(self._hass, self._trvs, self._trv_changed)
        )
        await self._async_evaluate()

    async def async_set_override(self, temperature: float) -> None:
        """Heat to `temperature` until the next block boundary."""
        self._set_room_mode(RoomMode.HEAT, temperature)
        await self._async_evaluate()

    async def async_set_room_mode(self, room_mode: RoomMode) -> None:
        """Switch the room mode; heat keeps the current target."""
        if room_mode is RoomMode.HEAT:
            if self.target_temperature is None:
                return
            self._set_room_mode(RoomMode.HEAT, self.target_temperature)
        else:
            self._set_room_mode(room_mode, None)
        await self._async_evaluate()

    @callback
    def _set_room_mode(self, room_mode: RoomMode, temperature: float | None) -> None:
        self._room_mode = room_mode
        self._override_temperature = temperature
        self._mode_expires_at = None
        if room_mode is not RoomMode.AUTO and (schedule := self._schedule.read()):
            self._mode_expires_at = schedule.next_block_boundary

    @callback
    def async_stop(self) -> None:
        """Unsubscribe all inputs and timers; a reload compares against the target."""
        while self._unsubscribers:
            self._unsubscribers.pop()()
        self._cancel_pending_reevaluation()
        if self.target_temperature is not None:
            self._hass.data.setdefault(DATA_TARGETS_BEFORE_RELOAD, {})[self.room_id] = (
                self.target_temperature
            )

    @callback
    def _async_request_evaluation(self) -> None:
        self._entry.async_create_task(
            self._hass, self._async_evaluate(), f"evaluate room {self.name}"
        )

    @callback
    def _reevaluation_due(self, _now: datetime) -> None:
        self._cancel_reevaluation = None
        self._async_request_evaluation()

    @callback
    def _trv_changed(self, _event: Event[EventStateChangedData]) -> None:
        self._notify_listeners()

    @callback
    def _cancel_pending_reevaluation(self) -> None:
        if self._cancel_reevaluation is not None:
            self._cancel_reevaluation()
            self._cancel_reevaluation = None

    @callback
    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            listener()

    async def _async_evaluate(self) -> None:
        async with self._evaluation_lock:
            self._cancel_pending_reevaluation()
            schedule = self._schedule.read()
            if schedule is None:
                return
            now = dt_util.utcnow()
            snapshot = RoomSnapshot(
                now=now,
                schedule=schedule,
                level_temperatures=self._level_temperatures,
                frost_temperature=self._frost_temperature,
                room_mode=self._room_mode,
                override_temperature=self._override_temperature,
                mode_expires_at=self._mode_expires_at,
            )
            decision = resolve(snapshot)
            self._snapshot = snapshot
            if not self._recent_decisions or self._recent_decisions[-1][1] != decision:
                self._recent_decisions.append((now, decision))
            if decision.room_mode is RoomMode.AUTO:
                self._set_room_mode(RoomMode.AUTO, None)
            previous_target = (
                self._decision.target_temperature
                if self._decision
                else self._target_before_reload
            )
            if previous_target not in (None, decision.target_temperature):
                self._announce_target_change(decision, now)
            self._decision = decision
            self._notify_listeners()
            if decision.reevaluate_at is not None and decision.reevaluate_at > now:
                self._cancel_reevaluation = async_track_point_in_utc_time(
                    self._hass, self._reevaluation_due, decision.reevaluate_at
                )
            for trv in self._trvs:
                await self._async_command_if_deviating(trv, decision)

    @callback
    def _announce_target_change(self, decision: Decision, now: datetime) -> None:
        """Fire the event the logbook describes as a target change with reason."""
        entity_id = er.async_get(self._hass).async_get_entity_id(
            CLIMATE_DOMAIN, DOMAIN, room_entity_unique_id(self.room_id)
        )
        self._hass.bus.async_fire(
            EVENT_TARGET_CHANGED,
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_NAME: self.name,
                ATTR_TARGET_TEMPERATURE: decision.target_temperature,
                ATTR_REASON_CODE: decision.reason.code.value,
                ATTR_REASON_PARAMS: {
                    key: value.isoformat() if isinstance(value, datetime) else value
                    for key, value in decision.reason.params.items()
                },
                ATTR_DECIDED_AT: now.isoformat(),
            },
        )

    async def _async_command_if_deviating(self, trv: str, decision: Decision) -> None:
        state = self._hass.states.get(trv)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        if decision.trv_mode is TrvMode.OFF:
            if state.state != TrvMode.OFF:
                await self._hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_SET_HVAC_MODE,
                    {ATTR_ENTITY_ID: trv, ATTR_HVAC_MODE: TrvMode.OFF},
                    blocking=True,
                )
            return
        if (
            state.state == decision.trv_mode
            and state.attributes.get(ATTR_TEMPERATURE) == decision.target_temperature
        ):
            return
        await self._hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: trv,
                ATTR_TEMPERATURE: decision.target_temperature,
                ATTR_HVAC_MODE: decision.trv_mode,
            },
            blocking=True,
        )
