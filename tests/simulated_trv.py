"""Simulated tado TRVs for scenario tests.

Each TRV is a real `climate` entity on its own device, so the integration talks to
it through the normal `climate.*` actions. The behaviour follows the measurements
in ticket 01: commands show up in the state at once, an off TRV reports no target
temperature and a 7-35 range, values reported by the TRV itself carry a fresh
context without user or parent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import (
    ATTR_DOMAIN,
    ATTR_ENTITY_ID,
    ATTR_SERVICE,
    ATTR_SERVICE_DATA,
    EVENT_CALL_SERVICE,
    Platform,
    UnitOfTemperature,
)
from homeassistant.core import Context, Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pytest_homeassistant.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    mock_integration,
    mock_platform,
)

TRV_DOMAIN = "simulated_tado"

_HEAT_RANGE = (5.0, 25.0)
_OFF_RANGE = (7.0, 35.0)


class _SimulatedTrvConfigFlow(ConfigFlow, domain=TRV_DOMAIN):
    """Owner of the config entries that carry the simulated TRVs."""

    VERSION = 1


@dataclass(frozen=True)
class TrvCall:
    """A `climate` action that targeted a TRV."""

    service: str
    data: dict[str, Any]
    context: Context


class SimulatedTrv(ClimateEntity):
    """A tado radiator thermostat as seen through HomeKit Device."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]  # noqa: RUF012
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_should_poll = False

    def __init__(
        self,
        object_id: str,
        *,
        hvac_mode: HVACMode,
        target_temperature: float,
        current_temperature: float,
    ) -> None:
        """Create a TRV; `target_temperature` is kept while it is off."""
        self.entity_id = f"climate.{object_id}"
        self._attr_unique_id = object_id
        self._attr_name = object_id
        self._attr_device_info = DeviceInfo(
            identifiers={(TRV_DOMAIN, object_id)},
            name=object_id,
            manufacturer="tado",
            model="SRT01",
        )
        self._attr_hvac_mode = hvac_mode
        self._setpoint = target_temperature
        self._attr_native_current_temperature = current_temperature
        self.calls: list[TrvCall] = []
        self.apply_commands = True
        """When False, commands are recorded but do not change the state."""

    @property
    def native_target_temperature(self) -> float | None:
        """Return the target temperature; tado reports none while off."""
        if self.hvac_mode == HVACMode.OFF:
            return None
        return self._setpoint

    @property
    def min_temp(self) -> float:
        """Return the lower bound; tado reports 7 while off."""
        return _OFF_RANGE[0] if self.hvac_mode == HVACMode.OFF else _HEAT_RANGE[0]

    @property
    def max_temp(self) -> float:
        """Return the upper bound; tado reports 35 while off."""
        return _OFF_RANGE[1] if self.hvac_mode == HVACMode.OFF else _HEAT_RANGE[1]

    def report(
        self,
        *,
        hvac_mode: HVACMode | None = None,
        target_temperature: float | None = None,
        current_temperature: float | None = None,
    ) -> None:
        """Make the TRV report new values, e.g. after a knob turn."""
        if hvac_mode is not None:
            self._attr_hvac_mode = hvac_mode
        if target_temperature is not None:
            self._setpoint = target_temperature
        if current_temperature is not None:
            self._attr_native_current_temperature = current_temperature
        self.async_set_context(Context())
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Apply mode and temperature at once."""
        if not self.apply_commands:
            return
        if (hvac_mode := kwargs.get("hvac_mode")) is not None:
            self._attr_hvac_mode = HVACMode(hvac_mode)
        if (temperature := kwargs.get("temperature")) is not None:
            self._setpoint = float(temperature)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Apply the mode at once."""
        if not self.apply_commands:
            return
        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

    @callback
    def record_call(self, event: Event) -> None:
        """Record a `climate` action that targets this TRV."""
        if event.data[ATTR_DOMAIN] != Platform.CLIMATE:
            return
        data = dict(event.data[ATTR_SERVICE_DATA])
        targets = data.pop(ATTR_ENTITY_ID, [])
        if isinstance(targets, str):
            targets = [targets]
        if self.entity_id in targets:
            self.calls.append(TrvCall(event.data[ATTR_SERVICE], data, event.context))


class SimulatedTrvs:
    """Factory that adds simulated TRVs to the test Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Register the simulated TRV integration."""
        self._hass = hass
        self._trvs_by_entry: dict[str, SimulatedTrv] = {}

        async def setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
            await hass.config_entries.async_forward_entry_setups(
                entry, [Platform.CLIMATE]
            )

        async def setup_climate(
            hass: HomeAssistant,
            entry: ConfigEntry,
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            async_add_entities([self._trvs_by_entry[entry.entry_id]])

        mock_integration(hass, MockModule(TRV_DOMAIN, async_setup_entry=setup_entry))
        mock_platform(hass, f"{TRV_DOMAIN}.config_flow")
        mock_platform(
            hass,
            f"{TRV_DOMAIN}.{Platform.CLIMATE}",
            MockPlatform(async_setup_entry=setup_climate),
        )

    async def add(
        self,
        object_id: str,
        *,
        hvac_mode: str = HVACMode.HEAT,
        target_temperature: float = 20.0,
        current_temperature: float = 20.0,
    ) -> SimulatedTrv:
        """Add a TRV as `climate.<object_id>` on its own device."""
        trv = SimulatedTrv(
            object_id,
            hvac_mode=HVACMode(hvac_mode),
            target_temperature=target_temperature,
            current_temperature=current_temperature,
        )
        entry = MockConfigEntry(domain=TRV_DOMAIN, title=object_id)
        entry.add_to_hass(self._hass)
        self._trvs_by_entry[entry.entry_id] = trv
        entry.async_on_unload(
            self._hass.bus.async_listen(EVENT_CALL_SERVICE, trv.record_call)
        )
        assert await self._hass.config_entries.async_setup(entry.entry_id)
        await self._hass.async_block_till_done()
        return trv
