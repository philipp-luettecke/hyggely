"""Reason sensor: explains in plain text why a room has its target."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

from . import ClimateControlConfigEntry
from .const import ATTR_REASON_CODE, DOMAIN
from .reason_text import async_load_reason_texts, minutes_since, reason_text
from .room_controller import RoomController


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one reason sensor per room."""
    for room_id, controller in entry.runtime_data.rooms.items():
        async_add_entities([RoomReason(controller)], config_subentry_id=room_id)


class RoomReason(SensorEntity):
    """Translates the reason of a room controller's decision into plain text.

    The state is the text, the attributes carry the stable reason code and its
    parameters. A reason counting minutes since a moment refreshes every minute.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "reason"
    _attr_should_poll = False

    def __init__(self, controller: RoomController) -> None:
        """Explain the room of `controller`."""
        self._controller = controller
        self._attr_unique_id = f"{controller.room_id}_reason"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, controller.room_id)})
        self._cancel_refresh: CALLBACK_TYPE | None = None

    async def async_added_to_hass(self) -> None:
        """Follow the room controller and the language of Home Assistant."""
        await async_load_reason_texts(self.hass)
        self.async_on_remove(self._controller.async_add_listener(self._async_refresh))
        self.async_on_remove(
            self.hass.bus.async_listen(
                EVENT_CORE_CONFIG_UPDATE, self._async_core_config_updated
            )
        )
        self.async_on_remove(self._cancel_pending_refresh)
        self._schedule_refresh()

    @property
    def native_value(self) -> str | None:
        """Return the reason as text."""
        if (reason := self._controller.reason) is None:
            return None
        return reason_text(self.hass, reason.code, reason.params, dt_util.utcnow())

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the reason code and its parameters."""
        if (reason := self._controller.reason) is None:
            return None
        return {ATTR_REASON_CODE: reason.code, **reason.params}

    async def _async_core_config_updated(self, event: Event) -> None:
        if "language" in event.data:
            await async_load_reason_texts(self.hass)
            self.async_write_ha_state()

    @callback
    def _async_refresh(self, _now: datetime | None = None) -> None:
        self._schedule_refresh()
        self.async_write_ha_state()

    @callback
    def _schedule_refresh(self) -> None:
        self._cancel_pending_refresh()
        reason = self._controller.reason
        since = reason.params.get("since") if reason else None
        if isinstance(since, datetime):
            elapsed = minutes_since(since, dt_util.utcnow())
            self._cancel_refresh = async_track_point_in_utc_time(
                self.hass,
                self._async_refresh,
                since + timedelta(minutes=elapsed + 1),
            )

    @callback
    def _cancel_pending_refresh(self) -> None:
        if self._cancel_refresh is not None:
            self._cancel_refresh()
            self._cancel_refresh = None
