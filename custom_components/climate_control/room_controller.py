"""Room controller: one per room, drives the TRVs from target resolver decisions."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta

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

from .const import (
    CONF_COMFORT_TEMPERATURE,
    CONF_ECO_TEMPERATURE,
    CONF_FROST_TEMPERATURE,
    CONF_OVERRIDE_EXPIRY_DURATION,
    CONF_OVERRIDE_EXPIRY_POLICY,
    CONF_SCHEDULE,
    CONF_TRVS,
    OVERRIDE_EXPIRY_GLOBAL,
)
from .room_mode_store import RoomModeChoice, RoomModeStore
from .schedule_reader import ScheduleReader
from .target_resolver import (
    Decision,
    Level,
    OverrideExpiry,
    OverrideExpiryPolicy,
    RoomMode,
    RoomSnapshot,
    TrvMode,
    mode_expires_at,
    resolve,
)


def _override_expiry(entry: ConfigEntry, subentry: ConfigSubentry) -> OverrideExpiry:
    """Return the override expiry rule of a room; room settings beat global ones."""
    policy = subentry.data.get(CONF_OVERRIDE_EXPIRY_POLICY, OVERRIDE_EXPIRY_GLOBAL)
    if policy == OVERRIDE_EXPIRY_GLOBAL:
        policy = entry.options[CONF_OVERRIDE_EXPIRY_POLICY]
    duration = subentry.data.get(
        CONF_OVERRIDE_EXPIRY_DURATION, entry.options[CONF_OVERRIDE_EXPIRY_DURATION]
    )
    return OverrideExpiry(
        policy=OverrideExpiryPolicy(policy), duration=timedelta(**duration)
    )


class RoomController:
    """Subscribes the inputs of a room, resolves its target and commands its TRVs.

    Commands go out only when a TRV deviates from the decision; for `heat` the
    mode always travels with the temperature because an off tado TRV silently
    ignores a temperature alone (ticket 01).
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
        room_modes: RoomModeStore,
    ) -> None:
        """Create the controller for the room `subentry` of the main entry.

        The room continues with the room mode saved in `room_modes`.
        """
        self._hass = hass
        self._entry = entry
        self._room_modes = room_modes
        self.room_id = subentry.subentry_id
        self.name = subentry.title
        self._trvs: list[str] = list(subentry.data[CONF_TRVS])
        self._schedule = ScheduleReader(hass, subentry.data[CONF_SCHEDULE])
        self._level_temperatures = {
            Level.COMFORT: float(subentry.data[CONF_COMFORT_TEMPERATURE]),
            Level.ECO: float(subentry.data[CONF_ECO_TEMPERATURE]),
        }
        self._frost_temperature = float(entry.options[CONF_FROST_TEMPERATURE])
        self._override_expiry = _override_expiry(entry, subentry)
        self._choice = room_modes.get(self.room_id)
        self._decision: Decision | None = None
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
    def mode_expires_at(self) -> datetime | None:
        """Return when the room returns to auto (override expiry)."""
        return self._decision.mode_expires_at if self._decision else None

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
        """Heat to `temperature` until the override expiry."""
        await self._async_choose(RoomMode.HEAT, temperature)
        await self._async_evaluate()

    async def async_set_room_mode(self, room_mode: RoomMode) -> None:
        """Switch the room mode; heat keeps the current target."""
        if room_mode is RoomMode.HEAT:
            if self.target_temperature is None:
                return
            await self._async_choose(RoomMode.HEAT, self.target_temperature)
        else:
            await self._async_choose(room_mode, None)
        await self._async_evaluate()

    async def _async_choose(
        self, room_mode: RoomMode, temperature: float | None
    ) -> None:
        schedule = self._schedule.read()
        self._choice = RoomModeChoice(
            room_mode=room_mode,
            override_temperature=temperature,
            expires_at=mode_expires_at(
                room_mode,
                now=dt_util.utcnow(),
                next_block_boundary=schedule.next_block_boundary if schedule else None,
                override_expiry=self._override_expiry,
            ),
        )
        await self._room_modes.async_save(self.room_id, self._choice)

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
            decision = resolve(
                RoomSnapshot(
                    now=now,
                    schedule=schedule,
                    level_temperatures=self._level_temperatures,
                    frost_temperature=self._frost_temperature,
                    room_mode=self._choice.room_mode,
                    override_temperature=self._choice.override_temperature,
                    mode_expires_at=self._choice.expires_at,
                )
            )
            if (
                decision.room_mode is RoomMode.AUTO
                and self._choice.room_mode is not RoomMode.AUTO
            ):
                await self._async_choose(RoomMode.AUTO, None)
            self._decision = decision
            self._notify_listeners()
            if decision.reevaluate_at is not None and decision.reevaluate_at > now:
                self._cancel_reevaluation = async_track_point_in_utc_time(
                    self._hass, self._reevaluation_due, decision.reevaluate_at
                )
            for trv in self._trvs:
                await self._async_command_if_deviating(trv, decision)

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
