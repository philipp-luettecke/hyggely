"""Room entity: the thermostat people see for a room."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ClimateControlConfigEntry
from .const import (
    DOMAIN,
    TEMPERATURE_STEP,
    TRV_MAX_TEMPERATURE,
    TRV_MIN_TEMPERATURE,
    room_entity_unique_id,
)
from .room_controller import RoomController
from .target_resolver import RoomMode

ATTR_LEVEL = "level"
ATTR_NEXT_BLOCK_BOUNDARY = "next_block_boundary"
ATTR_REASON = "reason"
ATTR_OVERRIDE_EXPIRY = "override_expiry"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one room entity per room."""
    for room_id, controller in entry.runtime_data.rooms.items():
        async_add_entities([RoomClimate(controller)], config_subentry_id=room_id)


class RoomClimate(ClimateEntity):
    """Shows the state of a room controller and passes commands to it."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]  # noqa: RUF012
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = TEMPERATURE_STEP
    _attr_min_temp = TRV_MIN_TEMPERATURE
    _attr_max_temp = TRV_MAX_TEMPERATURE

    def __init__(self, controller: RoomController) -> None:
        """Represent the room of `controller`."""
        self._controller = controller
        self._attr_unique_id = room_entity_unique_id(controller.room_id)
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, controller.room_id)})

    async def async_added_to_hass(self) -> None:
        """Follow the room controller."""
        self.async_on_remove(
            self._controller.async_add_listener(self.async_write_ha_state)
        )

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the room mode."""
        return HVACMode(self._controller.room_mode)

    @property
    def native_target_temperature(self) -> float | None:
        """Return the target temperature of the room."""
        return self._controller.target_temperature

    @property
    def native_current_temperature(self) -> float | None:
        """Return the current temperature of the room."""
        return self._controller.current_temperature

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return level, next block boundary, reason code and override expiry."""
        reason = self._controller.reason
        return {
            ATTR_LEVEL: self._controller.level,
            ATTR_NEXT_BLOCK_BOUNDARY: self._controller.next_block_boundary,
            ATTR_REASON: reason.code if reason else None,
            ATTR_OVERRIDE_EXPIRY: self._controller.mode_expires_at,
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Override the room with the new temperature.

        An `hvac_mode` sent along wins: off and auto switch the room mode and
        drop the temperature.
        """
        hvac_mode = kwargs.get(ATTR_HVAC_MODE)
        if hvac_mode in (HVACMode.OFF, HVACMode.AUTO):
            await self._controller.async_set_room_mode(RoomMode(hvac_mode))
            return
        await self._controller.async_set_override(float(kwargs[ATTR_TEMPERATURE]))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Switch the room mode."""
        await self._controller.async_set_room_mode(RoomMode(hvac_mode))
