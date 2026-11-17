"""Room controller: one per room, drives the TRVs from target resolver decisions."""

from __future__ import annotations

import asyncio
from collections import deque
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
    ATTR_NAME,
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
    State,
    callback,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

from .command_pacer import CommandPacer
from .const import (
    ATTR_DECIDED_AT,
    ATTR_REASON_CODE,
    ATTR_REASON_PARAMS,
    ATTR_TARGET_TEMPERATURE,
    CONF_AWAY_TEMPERATURE,
    CONF_COMFORT_TEMPERATURE,
    CONF_ECO_TEMPERATURE,
    CONF_FROST_TEMPERATURE,
    CONF_LEAD_TIME,
    CONF_NIGHT_TEMPERATURE,
    CONF_OVERRIDE_EXPIRY_DURATION,
    CONF_OVERRIDE_EXPIRY_POLICY,
    CONF_SCHEDULE,
    CONF_TRVS,
    CONF_VACATION_TEMPERATURE,
    CONF_WINDOW_CONTACTS,
    CONF_WINDOW_DELAY,
    DATA_TARGETS_BEFORE_RELOAD,
    DEFAULT_LEAD_TIME,
    DEFAULT_NIGHT_TEMPERATURE,
    DOMAIN,
    EVENT_TARGET_CHANGED,
    OVERRIDE_EXPIRY_GLOBAL,
    room_entity_unique_id,
)
from .house_mode import HouseModeController
from .override_detector import Classification, OverrideDetector, TrvSetting
from .presence import Presence
from .room_mode_store import RoomModeChoice, RoomModeStore
from .schedule_reader import ScheduleReader
from .target_resolver import (
    Decision,
    Level,
    OverrideExpiry,
    OverrideExpiryPolicy,
    Reason,
    RoomMode,
    RoomSnapshot,
    ScheduleLevel,
    TrvMode,
    heat_temperature,
    mode_expires_at,
    resolve,
)
from .trv_reachability import TrvReachability
from .window import WindowContacts

RECENT_DECISIONS = 20


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


def _target_setting(decision: Decision) -> TrvSetting:
    """Return the setting the TRVs get for `decision`."""
    if decision.trv_mode is TrvMode.OFF:
        return TrvSetting(mode=TrvMode.OFF)
    return TrvSetting(mode=TrvMode.HEAT, temperature=decision.target_temperature)


def _reported_setting(state: State | None) -> TrvSetting | None:
    """Return the setting a TRV state shows; None for an invalid one.

    An off tado TRV reports no temperature and the 7-35 range (ticket 01); off
    compares by mode only.
    """
    if state is None:
        return None
    if state.state == TrvMode.OFF:
        return TrvSetting(mode=TrvMode.OFF)
    temperature = state.attributes.get(ATTR_TEMPERATURE)
    if state.state != TrvMode.HEAT or not isinstance(temperature, int | float):
        return None
    return TrvSetting(mode=TrvMode.HEAT, temperature=float(temperature))


class RoomController:
    """Subscribes the inputs of a room, resolves its target and commands its TRVs.

    Commands go out only when a TRV deviates from the decision; for `heat` the
    mode always travels with the temperature because an off tado TRV silently
    ignores a temperature alone (ticket 01). Unreachable TRVs and TRVs reporting
    an invalid mode get nothing; once they take commands again they get the
    current target again, deviating or not. These resends and the first commands
    while Home Assistant starts go through the command pacer, one after another.
    The override detector classifies what the TRVs report in between: an
    external change becomes an override, or room off if the TRV was switched off;
    a command the TRV did not take is sent once more.
    """

    def __init__(  # noqa: PLR0913
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
        presence: Presence,
        *,
        house_mode: HouseModeController,
        room_modes: RoomModeStore,
        pacer: CommandPacer,
    ) -> None:
        """Create the controller for the room `subentry` of the main entry.

        The room continues with the room mode saved in `room_modes`.
        """
        self._hass = hass
        self._entry = entry
        self._presence = presence
        self._house_mode = house_mode
        self._room_modes = room_modes
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
        self._vacation_temperature = float(entry.options[CONF_VACATION_TEMPERATURE])
        self._override_expiry = _override_expiry(entry, subentry)
        self._window = WindowContacts(
            hass,
            subentry.data.get(CONF_WINDOW_CONTACTS, []),
            timedelta(**entry.options[CONF_WINDOW_DELAY]),
        )
        self._choice = room_modes.get(self.room_id)
        self._decision: Decision | None = None
        self._next_block_boundary: datetime | None = None
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
        self._evaluation_requested = False
        self._evaluation_lock = asyncio.Lock()
        self._detector = OverrideDetector()
        self._reachability = TrvReachability(
            hass,
            self._trvs,
            on_back=self._trv_back,
            on_report=self._trv_reported,
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
    def mode_expires_at(self) -> datetime | None:
        """Return when the room returns to auto (override expiry)."""
        return self._decision.mode_expires_at if self._decision else None

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
        self._unsubscribers.append(
            self._house_mode.async_add_listener(self._async_request_evaluation)
        )
        self._unsubscribers.append(
            self._window.async_track(self._async_request_evaluation)
        )
        self._unsubscribers.append(self._reachability.async_start())
        await self._async_evaluate(catch_up=self._hass.state is not CoreState.running)

    async def async_set_override(self, temperature: float) -> None:
        """Heat to `temperature` until the override expiry."""
        await self._async_choose(RoomMode.HEAT, temperature)
        await self._async_evaluate()

    async def async_set_room_mode(self, room_mode: RoomMode) -> None:
        """Switch the room mode, on the room entity or at a TRV.

        Heat keeps the current target (a room switched off heats to what auto
        would); off lasts until the next block boundary, whatever the override
        expiry rule says.
        """
        if room_mode is RoomMode.HEAT:
            schedule = self._schedule.read()
            if schedule is None:
                return
            temperature = heat_temperature(
                self._snapshot_at(dt_util.utcnow(), schedule)
            )
            await self._async_choose(RoomMode.HEAT, temperature)
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
        """Evaluate soon, once for all requests arriving together.

        At a block boundary both the reevaluation timer and the schedule ask.
        """
        if self._evaluation_requested:
            return
        self._evaluation_requested = True
        self._entry.async_create_task(
            self._hass,
            self._async_evaluate_requested(),
            f"evaluate room {self.name}",
            eager_start=False,
        )

    async def _async_evaluate_requested(self) -> None:
        self._evaluation_requested = False
        await self._async_evaluate()

    @callback
    def _reevaluation_due(self, _now: datetime) -> None:
        self._cancel_reevaluation = None
        self._async_request_evaluation()

    @callback
    def _trv_changed(self, _event: Event[EventStateChangedData]) -> None:
        self._notify_listeners()

    @callback
    def _trv_reported(self, trv: str) -> None:
        """Turn an external change at `trv`, e.g. a knob turn, into a room mode."""
        decision = self._decision
        reported = _reported_setting(self._hass.states.get(trv))
        if decision is None or reported is None:
            return
        classification = self._detector.classify(
            trv, reported, target=_target_setting(decision), now=dt_util.utcnow()
        )
        # Not eager: a command sent while the report is still being written would
        # be overwritten by the reported state.
        if classification is Classification.EXTERNAL_CHANGE:
            self._entry.async_create_task(
                self._hass,
                self._async_take_external_change(reported),
                f"take external change of {trv}",
                eager_start=False,
            )
        elif classification is Classification.NOT_TAKEN:
            self._entry.async_create_task(
                self._hass,
                self._async_repeat_command(trv),
                f"repeat command to {trv}",
                eager_start=False,
            )

    async def _async_take_external_change(self, setting: TrvSetting) -> None:
        """Switched off at the TRV means room off, anything else an override."""
        if setting.mode is TrvMode.OFF or setting.temperature is None:
            await self.async_set_room_mode(RoomMode.OFF)
        else:
            await self.async_set_override(setting.temperature)

    async def _async_repeat_command(self, trv: str) -> None:
        """Send the current decision to `trv` again; it did not take it."""
        async with self._evaluation_lock:
            decision = self._decision
            if decision is not None and self._deviates(trv, decision):
                await self._async_command(trv, decision, repeated=True)

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
            snapshot = self._snapshot_at(now, schedule)
            decision = resolve(snapshot)
            self._snapshot = snapshot
            if not self._recent_decisions or self._recent_decisions[-1][1] != decision:
                self._recent_decisions.append((now, decision))
            if (
                decision.room_mode is RoomMode.AUTO
                and self._choice.room_mode is not RoomMode.AUTO
            ):
                await self._async_choose(RoomMode.AUTO, None)
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
    def _snapshot_at(self, now: datetime, schedule: ScheduleLevel) -> RoomSnapshot:
        return RoomSnapshot(
            now=now,
            schedule=schedule,
            level_temperatures=self._level_temperatures,
            frost_temperature=self._frost_temperature,
            away_temperature=self._away_temperature,
            vacation_temperature=self._vacation_temperature,
            room_mode=self._choice.room_mode,
            override_temperature=self._choice.override_temperature,
            mode_expires_at=self._choice.expires_at,
            away=self._presence.away,
            house_mode=self._house_mode.house_mode,
            vacation_end=self._house_mode.vacation_end,
            window_open_since=self._window.open_since,
        )

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

    async def _async_command(
        self, trv: str, decision: Decision, *, repeated: bool = False
    ) -> None:
        self._detector.command_sent(
            trv,
            before=_reported_setting(self._hass.states.get(trv)),
            now=dt_util.utcnow(),
            repeated=repeated,
        )
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
