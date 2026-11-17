"""Vacation end entity: when the house returns from vacation to auto."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ClimateControlConfigEntry
from .house_mode import HouseModeController, house_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the vacation end entity to the house device."""
    async_add_entities(
        [VacationEndDateTime(entry.entry_id, entry.runtime_data.house_mode)]
    )


class VacationEndDateTime(DateTimeEntity):
    """Shows the vacation end and passes a new one to the house mode controller."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "vacation_end"

    def __init__(self, entry_id: str, house_mode: HouseModeController) -> None:
        """Represent the vacation end held by `house_mode`."""
        self._house_mode = house_mode
        self._attr_unique_id = f"{entry_id}_vacation_end"
        self._attr_device_info = house_device_info(entry_id)

    async def async_added_to_hass(self) -> None:
        """Follow the house mode controller."""
        self.async_on_remove(
            self._house_mode.async_add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> datetime | None:
        """Return the vacation end."""
        return self._house_mode.vacation_end

    async def async_set_value(self, value: datetime) -> None:
        """Set the vacation end."""
        await self._house_mode.async_set_vacation_end(value)
