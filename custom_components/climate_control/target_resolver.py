"""Target resolver: pure decision logic for one room, free of Home Assistant.

A room snapshot goes in; the target temperature, the room mode, the mode to send
to the TRVs, the reason and the next time the room must be re-evaluated come out.
Ranking, highest first: window open, room off, override, house off, vacation,
away, schedule. New inputs extend `RoomSnapshot` and take their place in it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any


class Level(StrEnum):
    """Named temperature tiers.

    Schedule levels are comfort, night and eco (outside blocks); away, vacation
    and frost are global.
    """

    COMFORT = "comfort"
    NIGHT = "night"
    ECO = "eco"
    AWAY = "away"
    VACATION = "vacation"
    FROST = "frost"


class RoomMode(StrEnum):
    """Mode of the room entity."""

    AUTO = "auto"
    HEAT = "heat"
    OFF = "off"


class HouseMode(StrEnum):
    """Global mode of the house; vacation lasts until the vacation end."""

    AUTO = "auto"
    VACATION = "vacation"
    OFF = "off"


class TrvMode(StrEnum):
    """HVAC mode sent to the TRVs."""

    HEAT = "heat"
    OFF = "off"


class OverrideExpiryPolicy(StrEnum):
    """When an override returns to auto."""

    NEXT_BLOCK = "next_block"
    DURATION = "duration"
    EARLIEST = "earliest"


@dataclass(frozen=True, kw_only=True)
class OverrideExpiryRule:
    """How a room finds its override expiry: the policy and the duration it uses."""

    policy: OverrideExpiryPolicy
    duration: timedelta


class ReasonCode(StrEnum):
    """Stable codes explaining a decision, offered to automations.

    Schedule levels share their value with their code. Parameters:
    `until` (datetime | None) for comfort, night, eco (next block boundary),
    override and room_off (when the room returns to auto) and vacation (its end);
    `since` (datetime) for window_open (when the window was opened);
    none for away, house_off and no_schedule.
    """

    COMFORT = "comfort"
    NIGHT = "night"
    ECO = "eco"
    OVERRIDE = "override"
    ROOM_OFF = "room_off"
    WINDOW_OPEN = "window_open"
    AWAY = "away"
    VACATION = "vacation"
    HOUSE_OFF = "house_off"
    NO_SCHEDULE = "no_schedule"


@dataclass(frozen=True, kw_only=True)
class ScheduleLevel:
    """Effective level from the schedule and when it next changes.

    `missing` while the room has no schedule or its helper is missing or
    unavailable; eco applies then, without block boundary.
    """

    level: Level
    next_block_boundary: datetime | None
    missing: bool = False


@dataclass(frozen=True, kw_only=True)
class RoomSnapshot:
    """Everything the target resolver needs to decide for one room.

    `room_mode` heat carries `override_temperature`; heat and off end at the
    `override_expiry` (None: no expiry). `away`, `house_mode` and `vacation_end`
    are the same for all rooms; ending the vacation is up to the caller.
    `window_open_since` is set while the window is open.
    """

    now: datetime
    schedule: ScheduleLevel
    level_temperatures: Mapping[Level, float]
    frost_temperature: float
    away_temperature: float
    vacation_temperature: float
    room_mode: RoomMode = RoomMode.AUTO
    override_temperature: float | None = None
    override_expiry: datetime | None = None
    away: bool = False
    house_mode: HouseMode = HouseMode.AUTO
    vacation_end: datetime | None = None
    window_open_since: datetime | None = None


@dataclass(frozen=True, kw_only=True)
class Reason:
    """Why a room has its target; `params` fill the human-readable text."""

    code: ReasonCode
    params: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class Decision:
    """Outcome for one room; `level` is None while the target follows no level."""

    room_mode: RoomMode
    target_temperature: float
    level: Level | None
    trv_mode: TrvMode
    reason: Reason
    reevaluate_at: datetime | None
    override_expiry: datetime | None = None


def override_expiry_for(
    room_mode: RoomMode,
    *,
    now: datetime,
    next_block_boundary: datetime | None,
    rule: OverrideExpiryRule,
) -> datetime | None:
    """Return the override expiry of a room mode chosen at `now` (None: never).

    Off always returns at the next block boundary; heat follows the override
    expiry rule.
    """
    if room_mode is RoomMode.AUTO:
        return None
    if room_mode is RoomMode.OFF or rule.policy is OverrideExpiryPolicy.NEXT_BLOCK:
        return next_block_boundary
    after_duration = now + rule.duration
    if rule.policy is OverrideExpiryPolicy.DURATION:
        return after_duration
    return _earliest(next_block_boundary, after_duration)


def heat_temperature(snapshot: RoomSnapshot) -> float:
    """Return the override temperature when heat is chosen without a temperature.

    Usually that is the current target. While the room or the house is off, it is
    what auto would heat to instead, so heat never holds frost protection. An open
    window is ignored: heat gets the target the room will have once the window is
    closed.
    """
    closed = replace(snapshot, window_open_since=None)
    decision = resolve(closed)
    if decision.level is not Level.FROST:
        return decision.target_temperature
    return resolve(
        replace(
            closed,
            room_mode=RoomMode.AUTO,
            override_temperature=None,
            override_expiry=None,
            house_mode=(
                HouseMode.AUTO
                if closed.house_mode is HouseMode.OFF
                else closed.house_mode
            ),
        )
    ).target_temperature


def resolve(snapshot: RoomSnapshot) -> Decision:
    """Decide the target of a room from its snapshot, highest rule first.

    An open window keeps the room mode with its override expiry, so closing it
    returns to the room mode, unless it expired meanwhile.
    """
    room_mode = snapshot.room_mode
    expiry = snapshot.override_expiry
    if expiry is not None and snapshot.now >= expiry:
        room_mode = RoomMode.AUTO
        expiry = None
    situation = _Situation(
        snapshot=snapshot,
        room_mode=room_mode,
        override_expiry=expiry,
        reevaluate_at=_earliest(snapshot.schedule.next_block_boundary, expiry),
    )
    for rule in _RULES:
        if (decision := rule(situation)) is not None:
            return decision
    return _schedule_level(situation)


@dataclass(frozen=True, kw_only=True)
class _Situation:
    """A snapshot with the room mode still in force and its override expiry."""

    snapshot: RoomSnapshot
    room_mode: RoomMode
    override_expiry: datetime | None
    reevaluate_at: datetime | None


def _window_open(situation: _Situation) -> Decision | None:
    snapshot = situation.snapshot
    if snapshot.window_open_since is None:
        return None
    return Decision(
        room_mode=situation.room_mode,
        target_temperature=snapshot.frost_temperature,
        level=Level.FROST,
        trv_mode=TrvMode.OFF,
        reason=Reason(
            code=ReasonCode.WINDOW_OPEN,
            params={"since": snapshot.window_open_since},
        ),
        reevaluate_at=situation.reevaluate_at,
        override_expiry=situation.override_expiry,
    )


def _room_off(situation: _Situation) -> Decision | None:
    if situation.room_mode is not RoomMode.OFF:
        return None
    return Decision(
        room_mode=RoomMode.OFF,
        target_temperature=situation.snapshot.frost_temperature,
        level=Level.FROST,
        trv_mode=TrvMode.OFF,
        reason=Reason(
            code=ReasonCode.ROOM_OFF, params={"until": situation.override_expiry}
        ),
        reevaluate_at=situation.reevaluate_at,
        override_expiry=situation.override_expiry,
    )


def _override(situation: _Situation) -> Decision | None:
    temperature = situation.snapshot.override_temperature
    if situation.room_mode is not RoomMode.HEAT or temperature is None:
        return None
    return Decision(
        room_mode=RoomMode.HEAT,
        target_temperature=temperature,
        level=None,
        trv_mode=TrvMode.HEAT,
        reason=Reason(
            code=ReasonCode.OVERRIDE, params={"until": situation.override_expiry}
        ),
        reevaluate_at=situation.reevaluate_at,
        override_expiry=situation.override_expiry,
    )


def _house_off(situation: _Situation) -> Decision | None:
    snapshot = situation.snapshot
    if snapshot.house_mode is not HouseMode.OFF:
        return None
    return Decision(
        room_mode=RoomMode.AUTO,
        target_temperature=snapshot.frost_temperature,
        level=Level.FROST,
        trv_mode=TrvMode.OFF,
        reason=Reason(code=ReasonCode.HOUSE_OFF),
        reevaluate_at=snapshot.schedule.next_block_boundary,
    )


def _vacation(situation: _Situation) -> Decision | None:
    snapshot = situation.snapshot
    if snapshot.house_mode is not HouseMode.VACATION:
        return None
    return Decision(
        room_mode=RoomMode.AUTO,
        target_temperature=snapshot.vacation_temperature,
        level=Level.VACATION,
        trv_mode=TrvMode.HEAT,
        reason=Reason(
            code=ReasonCode.VACATION, params={"until": snapshot.vacation_end}
        ),
        reevaluate_at=snapshot.schedule.next_block_boundary,
    )


def _away(situation: _Situation) -> Decision | None:
    snapshot = situation.snapshot
    if not snapshot.away:
        return None
    return Decision(
        room_mode=RoomMode.AUTO,
        target_temperature=snapshot.away_temperature,
        level=Level.AWAY,
        trv_mode=TrvMode.HEAT,
        reason=Reason(code=ReasonCode.AWAY),
        reevaluate_at=snapshot.schedule.next_block_boundary,
    )


def _schedule_level(situation: _Situation) -> Decision:
    schedule = situation.snapshot.schedule
    if schedule.missing:
        return Decision(
            room_mode=RoomMode.AUTO,
            target_temperature=situation.snapshot.level_temperatures[Level.ECO],
            level=Level.ECO,
            trv_mode=TrvMode.HEAT,
            reason=Reason(code=ReasonCode.NO_SCHEDULE),
            reevaluate_at=None,
        )
    return Decision(
        room_mode=RoomMode.AUTO,
        target_temperature=situation.snapshot.level_temperatures[schedule.level],
        level=schedule.level,
        trv_mode=TrvMode.HEAT,
        reason=Reason(
            code=ReasonCode(schedule.level.value),
            params={"until": schedule.next_block_boundary},
        ),
        reevaluate_at=schedule.next_block_boundary,
    )


_RULES: tuple[Callable[[_Situation], Decision | None], ...] = (
    _window_open,
    _room_off,
    _override,
    _house_off,
    _vacation,
    _away,
)
"""Rules that may decide, highest first; the schedule level decides otherwise."""


def _earliest(*moments: datetime | None) -> datetime | None:
    return min((moment for moment in moments if moment is not None), default=None)
