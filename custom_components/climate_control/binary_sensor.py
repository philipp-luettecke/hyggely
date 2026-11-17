"""Away entity: shows whether the whole house is away."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ClimateControlConfigEntry
from .const import DOMAIN
from .presence import Presence


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the away entity to the house device."""
    async_add_entities([AwayBinarySensor(entry.entry_id, entry.runtime_data.presence)])


class AwayBinarySensor(BinarySensorEntity):
    """On while all persons are not home for the away delay."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "away"

    def __init__(self, entry_id: str, presence: Presence) -> None:
        """Represent away as derived by `presence`."""
        self._presence = presence
        self._attr_unique_id = f"{entry_id}_away"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            translation_key="house",
            manufacturer="Climate Control",
            model="House",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Follow the presence."""
        self.async_on_remove(
            self._presence.async_add_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        """Return whether the house is away."""
        return self._presence.away
