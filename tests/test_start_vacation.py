"""Service start_vacation: vacation end and vacation in one step, for automations."""

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.translation import async_get_translations
from homeassistant.util import dt as dt_util
import pytest

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    House,
    Schedules,
    commands,
    living_room,
    local,
    shut_down,
)
from tests.simulated_trv import SimulatedTrvs

DOMAIN = "climate_control"
HEAT_15 = ("set_temperature", {"temperature": 15.0, "hvac_mode": "heat"})


async def _start_vacation(hass: HomeAssistant, **data: Any) -> None:
    await hass.services.async_call(DOMAIN, "start_vacation", data, blocking=True)
    await hass.async_block_till_done()


async def test_start_vacation_sets_the_end_and_lowers_until_then(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """An automation starts vacation until Friday 18:00 local time in one call."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)

    await _start_vacation(hass, end="2026-11-20 18:00:00")

    assert house.house_mode.state == "vacation"
    assert dt_util.parse_datetime(house.vacation_end.state) == local("2026-11-20 18:00")
    assert room.state(hass).attributes["temperature"] == 15.0
    assert commands(room.trv) == [HEAT_21, HEAT_15]

    await clock.advance_to("2026-11-20 18:00:00")
    assert house.house_mode.state == "auto"
    assert commands(room.trv) == [HEAT_21, HEAT_15, HEAT_17]


@pytest.mark.parametrize("end", ["2026-11-16 07:00:00", "2026-11-16 08:00:00"])
async def test_start_vacation_refuses_an_end_not_in_the_future(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    end: str,
) -> None:
    """An end at or before now is refused; house mode and vacation end stay."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)

    with pytest.raises(ServiceValidationError) as refused:
        await _start_vacation(hass, end=end)

    assert refused.value.translation_key == "vacation_end_must_be_ahead"
    assert house.house_mode.state == "auto"
    assert house.vacation_end.state == "unknown"
    assert commands(room.trv) == [HEAT_21]


async def test_start_vacation_during_a_vacation_refuses_a_past_end(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A refused call does not end a running vacation, unlike setting the end."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)
    await _start_vacation(hass, end="2026-11-20 18:00:00")

    with pytest.raises(ServiceValidationError):
        await _start_vacation(hass, end="2026-11-16 07:00:00")

    assert house.house_mode.state == "vacation"
    assert dt_util.parse_datetime(house.vacation_end.state) == local("2026-11-20 18:00")
    assert commands(room.trv) == [HEAT_21, HEAT_15]


async def test_start_vacation_is_refused_while_the_main_entry_is_not_loaded(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """With the integration stopped the call fails with a readable error."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await shut_down(hass, room.entry)

    with pytest.raises(ServiceValidationError) as refused:
        await _start_vacation(hass, end="2026-11-20 18:00:00")

    assert refused.value.translation_key == "not_loaded"


@pytest.mark.parametrize(
    ("language", "name", "end"),
    [("en", "Start vacation", "End"), ("de", "Urlaub starten", "Ende")],
)
async def test_start_vacation_is_worded_in_the_language(
    hass: HomeAssistant, language: str, name: str, end: str
) -> None:
    """Service, its field and both refusals have texts."""
    services = await async_get_translations(hass, language, "services", [DOMAIN])
    errors = await async_get_translations(hass, language, "exceptions", [DOMAIN])
    prefix = f"component.{DOMAIN}.services.start_vacation"

    assert services[f"{prefix}.name"] == name
    assert services[f"{prefix}.description"]
    assert services[f"{prefix}.fields.end.name"] == end
    assert services[f"{prefix}.fields.end.description"]
    for key in ("vacation_end_must_be_ahead", "not_loaded"):
        assert errors[f"component.{DOMAIN}.exceptions.{key}.message"]
