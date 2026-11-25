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
    applies from its start until its end, and already from the lead time
    before its start if it is warmer in the room than the level until then.
    Without a helper, or while it is missing or unavailable, eco applies.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entity_id: str | None,
        lead_time: timedelta,
        level_temperatures: Mapping[Level, float],
    ) -> None:
        """Read `entity_id` with the lead time and level temperatures of the room.

        `entity_id` is None for a room without schedule.
        """
        self._hass = hass
        self._entity_id = entity_id
        self._lead_time = lead_time
        self._level_temperatures = level_temperatures
        self._week: Mapping[str, Any] | None = None

    async def async_track(self, on_change: Callable[[], None]) -> CALLBACK_TYPE:
        """Load the blocks and call `on_change` whenever the helper changes.

        Edits of future blocks may leave state and attributes of the helper
        unchanged; it then only reports its state, so both events count.
        Returns the unsubscriber.
        """
        if self._entity_id is None:
            return lambda: None
        entity_id = self._entity_id
        await self._async_load(entity_id)
        stopped = False

        async def _async_reload() -> None:
            await self._async_load(entity_id)
            if not stopped:
                on_change()

        @callback
        def _changed(_event: Event[Any]) -> None:
            self._hass.async_create_task(
                _async_reload(), f"reload schedule {entity_id}"
            )

        unsubscribers = [
            async_track_state_change_event(self._hass, [entity_id], _changed),
            async_track_state_report_event(self._hass, [entity_id], _changed),
        ]

        @callback
        def _stop() -> None:
            nonlocal stopped
            stopped = True
            while unsubscribers:
                unsubscribers.pop()()

        return _stop

    @callback
    def read(self) -> ScheduleLevel:
        """Return the effective level now; eco while the helper is not known."""
        state = (
            self._hass.states.get(self._entity_id)
            if self._entity_id is not None
            else None
        )
        if (
            self._week is None
            or state is None
            or state.state not in (STATE_ON, STATE_OFF)
        ):
            return ScheduleLevel(
                level=Level.ECO, next_block_boundary=None, missing=True
            )
        now = dt_util.utcnow()
        return _schedule_level(
            _blocks_from(self._week, now),
            now,
            self._lead_time,
            self._level_temperatures,
        )

    async def _async_load(self, entity_id: str) -> None:
        try:
            response = await self._hass.services.async_call(
                SCHEDULE_DOMAIN,
                SERVICE_GET_SCHEDULE,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
                return_response=True,
            )
        except HomeAssistantError:
            self._week = None
            return
        week = (response or {}).get(entity_id)
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


def _level_at(
    blocks: list[_Block],
    moment: datetime,
    lead_time: timedelta,
    temperatures: Mapping[Level, float],
) -> tuple[Level, datetime | None]:
    """Return the level at `moment` and the start of the block it preheats for.

    A block starting within the lead time wins over the level in progress
    (a block or eco) only if it is warmer, the warmest of them if several; so
    the room preheats but never lowers early. An equally warm level waits for
    its start.
    """
    level = next(
        (block.level for block in blocks if block.start <= moment < block.end),
        Level.ECO,
    )
    preheat_start = None
    for block in blocks:
        if (
            moment < block.start <= moment + lead_time
            and temperatures[block.level] > temperatures[level]
        ):
            level = block.level
            preheat_start = block.start
    return level, preheat_start


def _schedule_level(
    blocks: list[_Block],
    now: datetime,
    lead_time: timedelta,
    temperatures: Mapping[Level, float],
) -> ScheduleLevel:
    """Return the level at `now`, the next moment it changes and any preheating."""
    level, preheat_start = _level_at(blocks, now, lead_time, temperatures)
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
            if _level_at(blocks, moment, lead_time, temperatures)[0] != level
        ),
        None,
    )
    return ScheduleLevel(
        level=level,
        next_block_boundary=next_block_boundary,
        preheat_start=preheat_start,
    )
