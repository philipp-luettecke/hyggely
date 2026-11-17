"""Logbook: describes target changes of rooms with their reason."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.logbook import (
    LOGBOOK_ENTRY_ENTITY_ID,
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
    LazyEventPartialState,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DECIDED_AT,
    ATTR_REASON_CODE,
    ATTR_REASON_PARAMS,
    ATTR_TARGET_TEMPERATURE,
    DOMAIN,
    EVENT_TARGET_CHANGED,
)
from .reason_text import target_changed_text


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[
        [str, str, Callable[[LazyEventPartialState], dict[str, Any]]], None
    ],
) -> None:
    """Describe the target changes the room controllers announce."""

    @callback
    def describe_target_changed(event: LazyEventPartialState) -> dict[str, Any]:
        data = event.data
        decided_at = dt_util.parse_datetime(data[ATTR_DECIDED_AT]) or dt_util.utcnow()
        return {
            LOGBOOK_ENTRY_NAME: data[ATTR_NAME],
            LOGBOOK_ENTRY_MESSAGE: target_changed_text(
                hass,
                data[ATTR_TARGET_TEMPERATURE],
                data[ATTR_REASON_CODE],
                data[ATTR_REASON_PARAMS],
                decided_at,
            ),
            LOGBOOK_ENTRY_ENTITY_ID: data[ATTR_ENTITY_ID],
        }

    async_describe_event(DOMAIN, EVENT_TARGET_CHANGED, describe_target_changed)
