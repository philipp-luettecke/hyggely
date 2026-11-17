"""Target resolver: pure decision logic for one room, free of Home Assistant.

A room snapshot goes in; the target temperature, the mode to send to the TRVs,
the reason and the next time the room must be re-evaluated come out. Later inputs
(window open, override, house mode, away) extend `RoomSnapshot` and the ranking
in `resolve`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Level(StrEnum):
    """Schedule levels; eco applies outside blocks."""

    COMFORT = "comfort"
    ECO = "eco"


class TrvMode(StrEnum):
    """HVAC mode sent to the TRVs together with the target temperature."""

    HEAT = "heat"


class ReasonCode(StrEnum):
    """Stable codes explaining a decision."""

    SCHEDULE = "schedule"


@dataclass(frozen=True, kw_only=True)
class ScheduleLevel:
    """Effective level from the schedule and when it next changes."""

    level: Level
    next_block_boundary: datetime | None


@dataclass(frozen=True, kw_only=True)
class RoomSnapshot:
    """Everything the target resolver needs to decide for one room."""

    now: datetime
    schedule: ScheduleLevel
    level_temperatures: Mapping[Level, float]


@dataclass(frozen=True, kw_only=True)
class Reason:
    """Why a room has its target; `params` fill the human-readable text."""

    code: ReasonCode
    params: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class Decision:
    """Outcome for one room."""

    target_temperature: float
    trv_mode: TrvMode
    reason: Reason
    reevaluate_at: datetime | None


def resolve(snapshot: RoomSnapshot) -> Decision:
    """Decide the target of a room from its snapshot."""
    schedule = snapshot.schedule
    return Decision(
        target_temperature=snapshot.level_temperatures[schedule.level],
        trv_mode=TrvMode.HEAT,
        reason=Reason(
            code=ReasonCode.SCHEDULE,
            params={"level": schedule.level, "until": schedule.next_block_boundary},
        ),
        reevaluate_at=schedule.next_block_boundary,
    )
