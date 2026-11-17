"""House mode entity: auto, vacation or off for the whole house."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ClimateControlConfigEntry
from .house_mode import HouseModeController, house_device_info
from .target_resolver import HouseMode


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the house mode entity to the house device."""
    async_add_entities([HouseModeSelect(entry.entry_id, entry.runtime_data.house_mode)])


class HouseModeSelect(SelectEntity):
    """Shows the house mode and passes a selection to the house mode controller."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "house_mode"
    _attr_options = [mode.value for mode in HouseMode]  # noqa: RUF012

    def __init__(self, entry_id: str, house_mode: HouseModeController) -> None:
        """Represent the house mode held by `house_mode`."""
        self._house_mode = house_mode
        self._attr_unique_id = f"{entry_id}_house_mode"
        self._attr_device_info = house_device_info(entry_id)

    async def async_added_to_hass(self) -> None:
        """Follow the house mode controller."""
        self.async_on_remove(
            self._house_mode.async_add_listener(self.async_write_ha_state)
        )

    @property
    def current_option(self) -> str:
        """Return the house mode."""
        return self._house_mode.house_mode.value

    async def async_select_option(self, option: str) -> None:
        """Switch the house mode."""
        await self._house_mode.async_set_house_mode(HouseMode(option))
