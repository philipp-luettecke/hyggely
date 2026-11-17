"""Shared fixtures for climate_control tests."""

from homeassistant.core import HomeAssistant
import pytest

from tests.simulated_trv import SimulatedTrvs


@pytest.fixture
def simulated_trvs(hass: HomeAssistant) -> SimulatedTrvs:
    """Return a factory for simulated tado TRVs."""
    return SimulatedTrvs(hass)
