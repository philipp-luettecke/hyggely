"""Away: once all persons are not home for the away delay, rooms in auto lower."""

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_21,
    Clock,
    LivingRoom,
    Persons,
    Schedules,
    away_state,
    change_global_settings,
    commands,
    living_room,
)
from tests.simulated_trv import SimulatedTrvs

HEAT_16 = ("set_temperature", {"temperature": 16.0, "hvac_mode": "heat"})


async def _living_room_with_persons(
    hass: HomeAssistant,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
    **presences: str,
) -> LivingRoom:
    """Add the living room; the main entry counts the persons, away is 16 °C."""
    entity_ids = await persons.add(**presences)
    room = await living_room(hass, schedules, simulated_trvs)
    await change_global_settings(
        hass, room.entry, persons=entity_ids, away_temperature=16.0
    )
    return room


async def test_house_is_away_once_all_persons_are_gone_for_the_away_delay(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Away starts 30 min after the last person left; the room gets 16 °C."""
    clock.set("2026-11-16 07:30")
    room = await _living_room_with_persons(
        hass, schedules, simulated_trvs, persons, anna="home", ben="home"
    )
    assert away_state(hass, room.entry).state == "off"

    await persons.move("anna", "not_home")
    await clock.advance_to("2026-11-16 07:40")
    await persons.move("ben", "Arbeit")

    await clock.advance_to("2026-11-16 08:09:59")
    assert away_state(hass, room.entry).state == "off"
    assert room.state(hass).attributes["temperature"] == 21.0

    await clock.advance_to("2026-11-16 08:10:00")
    assert away_state(hass, room.entry).state == "on"
    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 16.0
    assert commands(room.trv) == [HEAT_21, HEAT_16]
