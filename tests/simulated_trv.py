"""Simulated tado TRVs for scenario tests.

Each TRV is a real `climate` entity on its own device, so the integration talks to
it through the normal `climate.*` actions. The behaviour follows the measurements
in ticket 01: commands show up in the state at once, an off TRV reports no target
temperature and a 7-35 range and ignores a temperature without mode, values
reported by the TRV itself carry a fresh context without user or parent.

Like HomeKit Device, the device also carries a temperature sensor, and Home
Assistant polls the TRV once a minute at the full minute (no push). Knob turns,
switching off at the device and commands the TRV did not take show up at the
next poll, with only the values the TRV holds by then. On a bridge
outage the climate entity freezes with its old values and ignores commands; only
the temperature sensor becomes unavailable, at the second poll after unplugging.
After plugging the bridge in again, the sensor returns at the second poll
together with an invalid mode (state `unknown`), and fresh climate values arrive
at the fourth poll.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
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
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.util import dt as dt_util
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


def _poll_after(moment: datetime, count: int) -> datetime:
    """Return the `count`-th full minute after `moment`."""
    return moment.replace(second=0, microsecond=0) + timedelta(minutes=count)


@dataclass
class _BridgeOutage:
    """When the polls after unplugging and plugging in the bridge take effect."""

    sensor_lost_at: datetime
    sensor_back_at: datetime | None = None
    fresh_at: datetime | None = None


class SimulatedTemperatureSensor(SensorEntity):
    """The current temperature sensor on the device of a TRV."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_should_poll = False

    def __init__(self, trv: SimulatedTrv, object_id: str) -> None:
        """Create the sensor on the device of `trv`."""
        self._trv = trv
        self.entity_id = f"sensor.{object_id}_current_temperature"
        self._attr_unique_id = f"{object_id}_current_temperature"
        self._attr_name = f"{object_id} current temperature"
        self._attr_device_info = DeviceInfo(identifiers={(TRV_DOMAIN, object_id)})

    @property
    def native_value(self) -> float | None:
        """Return the current temperature the TRV measures."""
        return self._trv.native_current_temperature

    @callback
    def set_available(self, available: bool) -> None:
        """Become available or unavailable."""
        if self._attr_available != available:
            self._attr_available = available
            self.async_write_ha_state()


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
        temperature_sensor: bool,
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
        self._device_mode: HVACMode | None = hvac_mode
        self._device_setpoint = target_temperature
        self._attr_native_current_temperature = current_temperature
        self._invalid_mode = False
        self._outage: _BridgeOutage | None = None
        self.temperature_sensor = (
            SimulatedTemperatureSensor(self, object_id) if temperature_sensor else None
        )
        self.calls: list[TrvCall] = []
        self.apply_commands = True
        """When False, commands are recorded but do not change the state."""
        self.commands_to_lose = 0
        """Number of coming commands the TRV does not take: Home Assistant shows
        them at once, the next poll reports the old values again."""

    @property
    def temperature_sensor_id(self) -> str:
        """Return the entity id of the temperature sensor on the device."""
        assert self.temperature_sensor is not None
        return self.temperature_sensor.entity_id

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return the mode; None while the bridge reports an invalid one."""
        return None if self._invalid_mode else self._attr_hvac_mode

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

    async def async_added_to_hass(self) -> None:
        """Start the minute poll of Home Assistant."""
        self.async_on_remove(
            async_track_utc_time_change(self.hass, self._poll, second=0)
        )

    def report(
        self,
        *,
        hvac_mode: HVACMode | None = None,
        target_temperature: float | None = None,
        current_temperature: float | None = None,
    ) -> None:
        """Make the TRV report new values at once, outside the poll."""
        if hvac_mode is not None:
            self._attr_hvac_mode = self._device_mode = hvac_mode
        if target_temperature is not None:
            self._setpoint = self._device_setpoint = target_temperature
        if current_temperature is not None:
            self._attr_native_current_temperature = current_temperature
        self._invalid_mode = False
        self.async_set_context(Context())
        self.async_write_ha_state()
        if current_temperature is not None and self.temperature_sensor is not None:
            self.temperature_sensor.async_write_ha_state()

    def turn_knob(self, target_temperature: float) -> None:
        """Turn the knob: the TRV heats to the new value, seen at the next poll."""
        self._device_mode = HVACMode.HEAT
        self._device_setpoint = target_temperature

    def switch_off(self) -> None:
        """Switch the TRV off at the device, seen at the next poll."""
        self._device_mode = HVACMode.OFF

    def report_invalid_mode(self) -> None:
        """Make the bridge report the mode None, shown as state `unknown`."""
        self._invalid_mode = True
        self.async_set_context(Context())
        self.async_write_ha_state()

    def set_available(self, available: bool) -> None:
        """Make the climate entity itself unavailable or available again."""
        self._attr_available = available
        self.async_write_ha_state()

    def unplug_bridge(self) -> None:
        """Cut the bridge: values freeze, commands get lost, the sensor follows."""
        self._outage = _BridgeOutage(sensor_lost_at=_poll_after(dt_util.utcnow(), 2))

    def plug_in_bridge(self) -> None:
        """Reconnect the bridge; values return over the next polls."""
        assert self._outage is not None
        now = dt_util.utcnow()
        self._outage.sensor_back_at = _poll_after(now, 2)
        self._outage.fresh_at = _poll_after(now, 4)

    @callback
    def _poll(self, _now: datetime) -> None:
        """Run the minute poll: report what the TRV holds unless the bridge is out."""
        outage = self._outage
        if outage is None:
            if (self._attr_hvac_mode, self._setpoint) != (
                self._device_mode,
                self._device_setpoint,
            ):
                self._report_device()
            return
        now = dt_util.utcnow()
        if outage.fresh_at is not None and now >= outage.fresh_at:
            self._outage = None
            self._report_device()
            self._set_sensor_available(True)
        elif outage.sensor_back_at is not None and now >= outage.sensor_back_at:
            if not self._invalid_mode:
                self.report_invalid_mode()
            self._set_sensor_available(True)
        elif now >= outage.sensor_lost_at:
            self._set_sensor_available(False)

    def _report_device(self) -> None:
        self.report(
            hvac_mode=self._device_mode, target_temperature=self._device_setpoint
        )

    def _set_sensor_available(self, available: bool) -> None:
        if self.temperature_sensor is not None:
            self.temperature_sensor.set_available(available)

    def _takes_commands(self) -> bool:
        return self.apply_commands and self._outage is None

    def _show_command(self) -> None:
        """Show the command at once; the TRV holds it unless it is lost."""
        if self.commands_to_lose > 0:
            self.commands_to_lose -= 1
        else:
            self._device_mode = self._attr_hvac_mode
            self._device_setpoint = self._setpoint
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Apply mode and temperature at once; off, a temperature alone is ignored."""
        if not self._takes_commands():
            return
        hvac_mode = kwargs.get("hvac_mode")
        if hvac_mode is None and self._device_mode == HVACMode.OFF:
            return
        if hvac_mode is not None:
            self._attr_hvac_mode = HVACMode(hvac_mode)
        if (temperature := kwargs.get("temperature")) is not None:
            self._setpoint = float(temperature)
        self._show_command()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Apply the mode at once."""
        if not self._takes_commands():
            return
        self._attr_hvac_mode = hvac_mode
        self._show_command()

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
                entry, [Platform.CLIMATE, Platform.SENSOR]
            )

        async def setup_climate(
            hass: HomeAssistant,
            entry: ConfigEntry,
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            async_add_entities([self._trvs_by_entry[entry.entry_id]])

        async def setup_sensor(
            hass: HomeAssistant,
            entry: ConfigEntry,
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            sensor = self._trvs_by_entry[entry.entry_id].temperature_sensor
            if sensor is not None:
                async_add_entities([sensor])

        mock_integration(hass, MockModule(TRV_DOMAIN, async_setup_entry=setup_entry))
        mock_platform(hass, f"{TRV_DOMAIN}.config_flow")
        mock_platform(
            hass,
            f"{TRV_DOMAIN}.{Platform.CLIMATE}",
            MockPlatform(async_setup_entry=setup_climate),
        )
        mock_platform(
            hass,
            f"{TRV_DOMAIN}.{Platform.SENSOR}",
            MockPlatform(async_setup_entry=setup_sensor),
        )

    async def add(
        self,
        object_id: str,
        *,
        hvac_mode: str = HVACMode.HEAT,
        target_temperature: float = 20.0,
        current_temperature: float = 20.0,
        temperature_sensor: bool = True,
    ) -> SimulatedTrv:
        """Add a TRV as `climate.<object_id>` on its own device.

        With `temperature_sensor` the device also carries
        `sensor.<object_id>_current_temperature`.
        """
        trv = SimulatedTrv(
            object_id,
            hvac_mode=HVACMode(hvac_mode),
            target_temperature=target_temperature,
            current_temperature=current_temperature,
            temperature_sensor=temperature_sensor,
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
