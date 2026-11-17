"""Schedule reader: the effective level of a native schedule helper."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any

from homeassistant.components.schedule.const import (
    CONF_DATA,
    CONF_FROM,
    CONF_TO,
    DOMAIN as SCHEDULE_DOMAIN,
    WEEKDAY_TO_CONF,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_state_report_event,
)
from homeassistant.util import dt as dt_util

from .target_resolver import Level, ScheduleLevel

SERVICE_GET_SCHEDULE = "get_schedule"
BLOCK_LEVEL = "level"
"""Key of the level in the additional data of a block."""

_DAYS_AHEAD = 10
_HORIZON = timedelta(days=8)
"""A weekly schedule changes its level within a week or never."""


@dataclass(frozen=True, kw_only=True)
class _Block:
    start: datetime
    end: datetime
    level: Level


class ScheduleReader:
    """Reads the blocks of one schedule helper and reports changes to it.

    A block carries its level under `level` in its additional data; a block
    without one is comfort, outside blocks eco applies. The level of a block
    applies from the lead time before its start until its end.
    """

    def __init__(
        self, hass: HomeAssistant, entity_id: str, lead_time: timedelta
    ) -> None:
        """Read the schedule helper `entity_id` with the lead time of the room."""
        self._hass = hass
        self._entity_id = entity_id
        self._lead_time = lead_time
        self._week: Mapping[str, Any] | None = None

    async def async_track(self, on_change: Callable[[], None]) -> CALLBACK_TYPE:
        """Load the blocks and call `on_change` whenever the helper changes.

        Edits of future blocks may leave state and attributes of the helper
        unchanged; it then only reports its state, so both events count.
        Returns the unsubscriber.
        """
        await self._async_load()
        stopped = False

        async def _async_reload() -> None:
            await self._async_load()
            if not stopped:
                on_change()

        @callback
        def _changed(_event: Event[Any]) -> None:
            self._hass.async_create_task(
                _async_reload(), f"reload schedule {self._entity_id}"
            )

        unsubscribers = [
            async_track_state_change_event(self._hass, [self._entity_id], _changed),
            async_track_state_report_event(self._hass, [self._entity_id], _changed),
        ]

        @callback
        def _stop() -> None:
            nonlocal stopped
            stopped = True
            while unsubscribers:
                unsubscribers.pop()()

        return _stop

    @callback
    def read(self) -> ScheduleLevel | None:
        """Return the effective level now, or None while it is not known."""
        state = self._hass.states.get(self._entity_id)
        if (
            self._week is None
            or state is None
            or state.state not in (STATE_ON, STATE_OFF)
        ):
            return None
        now = dt_util.utcnow()
        return _schedule_level(_blocks_from(self._week, now), now, self._lead_time)

    async def _async_load(self) -> None:
        try:
            response = await self._hass.services.async_call(
                SCHEDULE_DOMAIN,
                SERVICE_GET_SCHEDULE,
                {ATTR_ENTITY_ID: self._entity_id},
                blocking=True,
                return_response=True,
            )
        except HomeAssistantError:
            self._week = None
            return
        week = (response or {}).get(self._entity_id)
        self._week = week if isinstance(week, Mapping) else None


def _blocks_from(week: Mapping[str, Any], now: datetime) -> list[_Block]:
    """Return the blocks from today on, sorted by start."""
    time_zone = dt_util.get_default_time_zone()
    today = dt_util.as_local(now).date()
    blocks = []
    for offset in range(_DAYS_AHEAD):
        day = today + timedelta(days=offset)
        for block in week.get(WEEKDAY_TO_CONF[day.weekday()], []):
            start = datetime.combine(day, block[CONF_FROM], tzinfo=time_zone)
            if block[CONF_TO] == time.max:
                end = datetime.combine(
                    day + timedelta(days=1), time(), tzinfo=time_zone
                )
            else:
                end = datetime.combine(day, block[CONF_TO], tzinfo=time_zone)
            blocks.append(
                _Block(
                    start=dt_util.as_utc(start),
                    end=dt_util.as_utc(end),
                    level=_block_level(block.get(CONF_DATA)),
                )
            )
    return sorted(blocks, key=lambda block: block.start)


def _block_level(data: Mapping[str, Any] | None) -> Level:
    if data is not None and data.get(BLOCK_LEVEL) == Level.NIGHT:
        return Level.NIGHT
    return Level.COMFORT


def _level_at(blocks: list[_Block], moment: datetime, lead_time: timedelta) -> Level:
    """Return the level at `moment`.

    The next block starting within the lead time wins, also over a block in
    progress; the end of a block is never brought forward.
    """
    for block in blocks:
        if moment < block.start <= moment + lead_time:
            return block.level
    for block in blocks:
        if block.start <= moment < block.end:
            return block.level
    return Level.ECO


def _schedule_level(
    blocks: list[_Block], now: datetime, lead_time: timedelta
) -> ScheduleLevel:
    """Return the level at `now` and the next moment it changes."""
    level = _level_at(blocks, now, lead_time)
    moments = sorted(
        {
            moment
            for block in blocks
            for moment in (block.start - lead_time, block.start, block.end)
            if now < moment <= now + _HORIZON
        }
    )
    next_block_boundary = next(
        (
            moment
            for moment in moments
            if _level_at(blocks, moment, lead_time) != level
        ),
        None,
    )
    return ScheduleLevel(level=level, next_block_boundary=next_block_boundary)
