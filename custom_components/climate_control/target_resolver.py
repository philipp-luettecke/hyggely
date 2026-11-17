"""Target resolver: pure decision logic for one room, free of Home Assistant.

A room snapshot goes in; the target temperature, the room mode, the mode to send
to the TRVs, the reason and the next time the room must be re-evaluated come out.
Later inputs (window open, house mode, vacation) extend `RoomSnapshot` and take
their place in the ranking of `resolve`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Level(StrEnum):
    """Named temperature tiers.

    Schedule levels are comfort, night and eco (outside blocks); away and frost
    are global.
    """

    COMFORT = "comfort"
    NIGHT = "night"
    ECO = "eco"
    AWAY = "away"
    FROST = "frost"


class RoomMode(StrEnum):
    """Mode of the room entity."""

    AUTO = "auto"
    HEAT = "heat"
    OFF = "off"


class TrvMode(StrEnum):
    """HVAC mode sent to the TRVs."""

    HEAT = "heat"
    OFF = "off"


class ReasonCode(StrEnum):
    """Stable codes explaining a decision, offered to automations.

    Schedule levels share their value with their code. Parameters:
    `until` (datetime | None) for comfort, night, eco (next block boundary),
    override and room_off (when the room returns to auto) and vacation (its end);
    `since` (datetime) for window_open (when the window was opened);
    none for away and house_off.
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


@dataclass(frozen=True, kw_only=True)
class ScheduleLevel:
    """Effective level from the schedule and when it next changes."""

    level: Level
    next_block_boundary: datetime | None


@dataclass(frozen=True, kw_only=True)
class RoomSnapshot:
    """Everything the target resolver needs to decide for one room.

    `room_mode` heat carries `override_temperature`; heat and off end at
    `mode_expires_at` (None: no expiry). `away` is the same for all rooms.
    """

    now: datetime
    schedule: ScheduleLevel
    level_temperatures: Mapping[Level, float]
    frost_temperature: float
    away_temperature: float
    room_mode: RoomMode = RoomMode.AUTO
    override_temperature: float | None = None
    mode_expires_at: datetime | None = None
    away: bool = False


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


def resolve(snapshot: RoomSnapshot) -> Decision:
    """Decide the target of a room from its snapshot, highest rule first."""
    schedule = snapshot.schedule
    room_mode = snapshot.room_mode
    expires_at = snapshot.mode_expires_at
    if expires_at is not None and snapshot.now >= expires_at:
        room_mode = RoomMode.AUTO
    reevaluate_at = _earliest(schedule.next_block_boundary, expires_at)

    if room_mode is RoomMode.OFF:
        return Decision(
            room_mode=RoomMode.OFF,
            target_temperature=snapshot.frost_temperature,
            level=Level.FROST,
            trv_mode=TrvMode.OFF,
            reason=Reason(code=ReasonCode.ROOM_OFF, params={"until": expires_at}),
            reevaluate_at=reevaluate_at,
        )
    if room_mode is RoomMode.HEAT and snapshot.override_temperature is not None:
        return Decision(
            room_mode=RoomMode.HEAT,
            target_temperature=snapshot.override_temperature,
            level=None,
            trv_mode=TrvMode.HEAT,
            reason=Reason(code=ReasonCode.OVERRIDE, params={"until": expires_at}),
            reevaluate_at=reevaluate_at,
        )
    if snapshot.away:
        return Decision(
            room_mode=RoomMode.AUTO,
            target_temperature=snapshot.away_temperature,
            level=Level.AWAY,
            trv_mode=TrvMode.HEAT,
            reason=Reason(code=ReasonCode.AWAY),
            reevaluate_at=schedule.next_block_boundary,
        )
    return Decision(
        room_mode=RoomMode.AUTO,
        target_temperature=snapshot.level_temperatures[schedule.level],
        level=schedule.level,
        trv_mode=TrvMode.HEAT,
        reason=Reason(
            code=ReasonCode(schedule.level.value),
            params={"until": schedule.next_block_boundary},
        ),
        reevaluate_at=schedule.next_block_boundary,
    )


def _earliest(*moments: datetime | None) -> datetime | None:
    return min((moment for moment in moments if moment is not None), default=None)
