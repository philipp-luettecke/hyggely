"""Room controller: one per room, drives the TRVs from target resolver decisions."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import partial

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
    ATTR_TEMPERATURE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    CoreState,
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

from .command_pacer import CommandPacer
from .const import (
    CONF_AWAY_TEMPERATURE,
    CONF_COMFORT_TEMPERATURE,
    CONF_ECO_TEMPERATURE,
    CONF_FROST_TEMPERATURE,
    CONF_LEAD_TIME,
    CONF_NIGHT_TEMPERATURE,
    CONF_SCHEDULE,
    CONF_TRVS,
    DEFAULT_LEAD_TIME,
    DEFAULT_NIGHT_TEMPERATURE,
)
from .presence import Presence
from .schedule_reader import ScheduleReader
from .target_resolver import (
    Decision,
    Level,
    RoomMode,
    RoomSnapshot,
    TrvMode,
    resolve,
)
from .trv_reachability import TrvReachability


class RoomController:
    """Subscribes the inputs of a room, resolves its target and commands its TRVs.

    Commands go out only when a TRV deviates from the decision; for `heat` the
    mode always travels with the temperature because an off tado TRV silently
    ignores a temperature alone (ticket 01). Unreachable TRVs and TRVs reporting
    an invalid mode get nothing; once they take commands again they get the
    current target again, deviating or not. These resends and the first commands
    while Home Assistant starts go through the command pacer, one after another.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
        presence: Presence,
        *,
        pacer: CommandPacer,
    ) -> None:
        """Create the controller for the room `subentry` of the main entry."""
        self._hass = hass
        self._entry = entry
        self._presence = presence
        self._pacer = pacer
        self.room_id = subentry.subentry_id
        self.name = subentry.title
        self._trvs: list[str] = list(subentry.data[CONF_TRVS])
        self._schedule = ScheduleReader(
            hass,
            subentry.data[CONF_SCHEDULE],
            timedelta(**subentry.data.get(CONF_LEAD_TIME, DEFAULT_LEAD_TIME)),
        )
        self._level_temperatures = {
            Level.COMFORT: float(subentry.data[CONF_COMFORT_TEMPERATURE]),
            Level.NIGHT: float(
                subentry.data.get(CONF_NIGHT_TEMPERATURE, DEFAULT_NIGHT_TEMPERATURE)
            ),
            Level.ECO: float(subentry.data[CONF_ECO_TEMPERATURE]),
        }
        self._frost_temperature = float(entry.options[CONF_FROST_TEMPERATURE])
        self._away_temperature = float(entry.options[CONF_AWAY_TEMPERATURE])
        self._room_mode = RoomMode.AUTO
        self._override_temperature: float | None = None
        self._mode_expires_at: datetime | None = None
        self._decision: Decision | None = None
        self._next_block_boundary: datetime | None = None
        self._listeners: list[Callable[[], None]] = []
        self._unsubscribers: list[CALLBACK_TYPE] = []
        self._cancel_reevaluation: CALLBACK_TYPE | None = None
        self._evaluation_lock = asyncio.Lock()
        self._reachability = TrvReachability(
            hass,
            self._trvs,
            on_back=self._trv_back,
            on_offline_changed=self._notify_listeners,
        )

    @property
    def room_mode(self) -> RoomMode:
        """Return the room mode as last decided."""
        return self._decision.room_mode if self._decision else RoomMode.AUTO

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature of the room."""
        return self._decision.target_temperature if self._decision else None

    @property
    def level(self) -> Level | None:
        """Return the level that sets the target, None for an override."""
        return self._decision.level if self._decision else None

    @property
    def next_block_boundary(self) -> datetime | None:
        """Return when the level from the schedule changes next, lead time included."""
        return self._next_block_boundary

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

    @property
    def offline_trvs(self) -> frozenset[str]:
        """Return the TRVs of the room unreachable for longer than 30 minutes."""
        return self._reachability.offline

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Call `listener` whenever the room changes; return the unsubscriber."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    async def async_start(self) -> None:
        """Subscribe the inputs and bring the TRVs into the decided state."""
        self._unsubscribers.append(
            await self._schedule.async_track(self._async_request_evaluation)
        )
        self._unsubscribers.append(
            async_track_state_change_event(self._hass, self._trvs, self._trv_changed)
        )
        self._unsubscribers.append(
            self._presence.async_add_listener(self._async_request_evaluation)
        )
        self._unsubscribers.append(self._reachability.async_start())
        await self._async_evaluate(catch_up=self._hass.state is not CoreState.running)

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
        """Unsubscribe all inputs and timers."""
        while self._unsubscribers:
            self._unsubscribers.pop()()
        self._cancel_pending_reevaluation()

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
    def _trv_back(self, trv: str) -> None:
        self._pacer.async_enqueue(
            f"resend to {trv}", partial(self._async_catch_up, trv, resend=True)
        )

    async def _async_catch_up(self, trv: str, *, resend: bool) -> None:
        """Bring `trv` to the current decision; `resend` even if it matches."""
        async with self._evaluation_lock:
            decision = self._decision
            if decision is not None and (
                self._deviates(trv, decision)
                or (resend and self._reachability.takes_commands(trv))
            ):
                await self._async_command(trv, decision)

    @callback
    def _cancel_pending_reevaluation(self) -> None:
        if self._cancel_reevaluation is not None:
            self._cancel_reevaluation()
            self._cancel_reevaluation = None

    @callback
    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            listener()

    async def _async_evaluate(self, *, catch_up: bool = False) -> None:
        """Decide and command deviating TRVs; with `catch_up` paced, not at once."""
        async with self._evaluation_lock:
            self._cancel_pending_reevaluation()
            schedule = self._schedule.read()
            if schedule is None:
                return
            self._next_block_boundary = schedule.next_block_boundary
            now = dt_util.utcnow()
            decision = resolve(
                RoomSnapshot(
                    now=now,
                    schedule=schedule,
                    level_temperatures=self._level_temperatures,
                    frost_temperature=self._frost_temperature,
                    away_temperature=self._away_temperature,
                    room_mode=self._room_mode,
                    override_temperature=self._override_temperature,
                    mode_expires_at=self._mode_expires_at,
                    away=self._presence.away,
                )
            )
            if decision.room_mode is RoomMode.AUTO:
                self._set_room_mode(RoomMode.AUTO, None)
            self._decision = decision
            self._notify_listeners()
            if decision.reevaluate_at is not None and decision.reevaluate_at > now:
                self._cancel_reevaluation = async_track_point_in_utc_time(
                    self._hass, self._reevaluation_due, decision.reevaluate_at
                )
            for trv in self._trvs:
                if not self._deviates(trv, decision):
                    continue
                if catch_up:
                    self._pacer.async_enqueue(
                        f"bring {trv} up to date",
                        partial(self._async_catch_up, trv, resend=False),
                    )
                else:
                    await self._async_command(trv, decision)

    @callback
    def _deviates(self, trv: str, decision: Decision) -> bool:
        """Return whether `trv` takes commands and differs from `decision`."""
        if not self._reachability.takes_commands(trv):
            return False
        state = self._hass.states.get(trv)
        assert state is not None
        return state.state != decision.trv_mode or (
            decision.trv_mode is TrvMode.HEAT
            and state.attributes.get(ATTR_TEMPERATURE) != decision.target_temperature
        )

    async def _async_command(self, trv: str, decision: Decision) -> None:
        if decision.trv_mode is TrvMode.OFF:
            await self._hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {ATTR_ENTITY_ID: trv, ATTR_HVAC_MODE: TrvMode.OFF},
                blocking=True,
            )
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
