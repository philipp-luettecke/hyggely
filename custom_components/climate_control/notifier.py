"""Notifier: tells the recipients about windows left open and offline TRVs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import StrEnum
import logging

from homeassistant.components.notify import (
    ATTR_MESSAGE,
    ATTR_TITLE,
    DOMAIN as NOTIFY_DOMAIN,
    SERVICE_SEND_MESSAGE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.translation import async_get_translations
from homeassistant.util import dt as dt_util
from homeassistant.util.hass_dict import HassKey

from .const import CONF_NOTIFY_TARGETS, CONF_QUIET_END, CONF_QUIET_START, DOMAIN
from .room_controller import RoomController
from .trv_reachability import OFFLINE_AFTER

_LOGGER = logging.getLogger(__name__)

WINDOW_OPEN_AFTER = timedelta(minutes=20)
BUNDLING_WINDOW = timedelta(minutes=1)

_TEXTS = f"component.{DOMAIN}.common"


class AlertKind(StrEnum):
    """What the recipients hear about."""

    WINDOW_OPEN = "window_open"
    TRV_OFFLINE = "trv_offline"


@dataclass(frozen=True)
class Alert:
    """A window open for `WINDOW_OPEN_AFTER` in a room, or an offline TRV."""

    kind: AlertKind
    room_id: str
    trv: str | None = None


# Alerts already sent when the main entry stopped for a reload.
DATA_ALERTS_BEFORE_RELOAD: HassKey[set[Alert]] = HassKey(
    f"{DOMAIN}_alerts_before_reload"
)


@dataclass(frozen=True)
class QuietTime:
    """Daily local time range without notifications; may span midnight."""

    start: time
    end: time

    def contains(self, moment: datetime) -> bool:
        """Return whether `moment` lies in the quiet time; start equal to end is none."""
        now = dt_util.as_local(moment).time()
        if self.start <= self.end:
            return self.start <= now < self.end
        return now >= self.start or now < self.end

    def end_after(self, moment: datetime) -> datetime:
        """Return the next end of the quiet time after `moment`."""
        local = dt_util.as_local(moment)
        end = datetime.combine(local.date(), self.end, local.tzinfo)
        if end <= local:
            end = datetime.combine(local.date() + timedelta(days=1), self.end, local.tzinfo)
        return dt_util.as_utc(end)


def _quiet_time(entry: ConfigEntry) -> QuietTime:
    start = dt_util.parse_time(entry.options[CONF_QUIET_START])
    end = dt_util.parse_time(entry.options[CONF_QUIET_END])
    assert start is not None
    assert end is not None
    return QuietTime(start, end)


class Notifier:
    """Notifies the recipients of windows open for 20 min and offline TRVs.

    Each alert goes out once and again only after it resolved and came back.
    Alerts coming up within the bundling window share one message. During the
    quiet time nothing goes out; at its end one message names the alerts that
    still apply. Resolving sends nothing.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        rooms: Mapping[str, RoomController],
    ) -> None:
        """Watch `rooms` and notify the recipients of the main entry."""
        self._hass = hass
        self._entry = entry
        self._rooms = rooms
        self._targets: list[str] = list(entry.options.get(CONF_NOTIFY_TARGETS, []))
        self._quiet_time = _quiet_time(entry)
        self._sent: set[Alert] = hass.data.pop(DATA_ALERTS_BEFORE_RELOAD, set())
        self._send_at: datetime | None = None
        self._unsubscribers: list[CALLBACK_TYPE] = []
        self._cancel_timer: CALLBACK_TYPE | None = None

    @callback
    def async_start(self) -> None:
        """Follow the rooms."""
        self._unsubscribers = [
            room.async_add_listener(self._update) for room in self._rooms.values()
        ]
        self._update()

    @callback
    def async_stop(self) -> None:
        """Stop following the rooms; a reload does not repeat sent alerts."""
        while self._unsubscribers:
            self._unsubscribers.pop()()
        self._cancel_pending_timer()
        self._hass.data[DATA_ALERTS_BEFORE_RELOAD] = set(self._sent)

    @callback
    def _update(self, _now: datetime | None = None) -> None:
        self._cancel_pending_timer()
        now = dt_util.utcnow()
        due, next_due = self._alerts(now)
        self._sent &= due
        pending = due - self._sent
        if not pending:
            self._send_at = None
        elif self._quiet_time.contains(now):
            self._send_at = self._quiet_time.end_after(now)
        elif self._send_at is None:
            self._send_at = now + BUNDLING_WINDOW
        if self._send_at is not None and self._send_at <= now:
            self._send_at = None
            self._sent |= pending
            self._entry.async_create_task(
                self._hass, self._async_send(pending), "notify recipients"
            )
        wake_at = min(
            (moment for moment in (next_due, self._send_at) if moment is not None),
            default=None,
        )
        if wake_at is not None:
            self._cancel_timer = async_track_point_in_utc_time(
                self._hass, self._update, wake_at
            )

    @callback
    def _alerts(self, now: datetime) -> tuple[set[Alert], datetime | None]:
        """Return the alerts due at `now` and when the next window becomes due."""
        due: set[Alert] = set()
        next_due: datetime | None = None
        for room_id, room in self._rooms.items():
            if (open_since := room.window_open_since) is not None:
                if (due_at := open_since + WINDOW_OPEN_AFTER) <= now:
                    due.add(Alert(AlertKind.WINDOW_OPEN, room_id))
                elif next_due is None or due_at < next_due:
                    next_due = due_at
            due.update(
                Alert(AlertKind.TRV_OFFLINE, room_id, trv) for trv in room.offline_trvs
            )
        return due, next_due

    @callback
    def _cancel_pending_timer(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None

    async def _async_send(self, alerts: set[Alert]) -> None:
        """Send one message about `alerts` in the language of Home Assistant."""
        if not self._targets:
            return
        texts = await async_get_translations(
            self._hass, self._hass.config.language, "common", [DOMAIN]
        )
        lines = []
        if rooms := sorted(
            self._rooms[alert.room_id].name
            for alert in alerts
            if alert.kind is AlertKind.WINDOW_OPEN
        ):
            lines.append(
                texts[f"{_TEXTS}.window_open"].format(
                    minutes=_minutes(WINDOW_OPEN_AFTER), rooms=", ".join(rooms)
                )
            )
        if trvs := sorted(
            (self._rooms[alert.room_id].name, self._name(alert.trv))
            for alert in alerts
            if alert.kind is AlertKind.TRV_OFFLINE and alert.trv is not None
        ):
            lines.append(
                texts[f"{_TEXTS}.trv_offline"].format(
                    minutes=_minutes(OFFLINE_AFTER),
                    trvs=", ".join(f"{trv} ({room})" for room, trv in trvs),
                )
            )
        try:
            await self._hass.services.async_call(
                NOTIFY_DOMAIN,
                SERVICE_SEND_MESSAGE,
                {
                    ATTR_ENTITY_ID: self._targets,
                    ATTR_TITLE: texts[f"{_TEXTS}.notification_title"],
                    ATTR_MESSAGE: "\n".join(lines),
                },
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.warning("Could not notify %s: %s", ", ".join(self._targets), err)

    def _name(self, entity_id: str) -> str:
        state = self._hass.states.get(entity_id)
        if state is None:
            return entity_id
        return str(state.attributes.get(ATTR_FRIENDLY_NAME, entity_id))


def _minutes(duration: timedelta) -> int:
    return duration // timedelta(minutes=1)
