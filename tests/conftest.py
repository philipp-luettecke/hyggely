"""Shared fixtures for climate_control tests."""

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant.typing import WebSocketGenerator

from tests.scenario import TIME_ZONE, Clock, Persons, Schedules
from tests.simulated_trv import SimulatedTrvs


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Schedule helpers and rooms keep a timer to their next block boundary."""
    return True


@pytest.fixture
def simulated_trvs(hass: HomeAssistant) -> SimulatedTrvs:
    """Return a factory for simulated tado TRVs."""
    return SimulatedTrvs(hass)


@pytest.fixture
async def clock(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> Clock:
    """Return the local wall clock; the house is in Europe/Berlin."""
    await hass.config.async_set_time_zone(TIME_ZONE)
    return Clock(hass, freezer)


@pytest.fixture
async def schedules(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> Schedules:
    """Return a factory for native schedule helpers."""
    assert await async_setup_component(hass, "schedule", {})
    return Schedules(hass, await hass_ws_client(hass))


@pytest.fixture
def persons(hass: HomeAssistant) -> Persons:
    """Return a factory for native persons followed through their phones."""
    return Persons(hass)
