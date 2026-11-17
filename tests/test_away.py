"""Away: once all persons are not home for the presence delay, rooms in auto lower."""

from homeassistant.core import HomeAssistant
import pytest

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

HEAT_15_5 = ("set_temperature", {"temperature": 15.5, "hvac_mode": "heat"})
HEAT_16 = ("set_temperature", {"temperature": 16.0, "hvac_mode": "heat"})
HEAT_23 = ("set_temperature", {"temperature": 23.0, "hvac_mode": "heat"})


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


async def test_house_is_away_once_all_persons_are_gone_for_the_presence_delay(
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
    assert room.state(hass).attributes["level"] == "away"
    assert commands(room.trv) == [HEAT_21, HEAT_16]


async def test_return_of_one_person_ends_away_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """When Anna comes home, the room is back at comfort without delay."""
    clock.set("2026-11-16 07:20")
    room = await _living_room_with_persons(
        hass, schedules, simulated_trvs, persons, anna="home", ben="home"
    )
    await persons.move("anna", "not_home")
    await persons.move("ben", "not_home")
    await clock.advance_to("2026-11-16 07:50")
    assert away_state(hass, room.entry).state == "on"

    await clock.advance_to("2026-11-16 08:15")
    await persons.move("anna", "home")

    assert away_state(hass, room.entry).state == "off"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21, HEAT_16, HEAT_21]


async def test_house_is_not_away_while_one_person_stays_home(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Anna leaves for the morning, Ben stays home: the room keeps comfort."""
    clock.set("2026-11-16 07:00")
    room = await _living_room_with_persons(
        hass, schedules, simulated_trvs, persons, anna="home", ben="home"
    )

    await persons.move("anna", "not_home")
    await clock.advance_to("2026-11-16 08:59")

    assert away_state(hass, room.entry).state == "off"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21]


@pytest.mark.parametrize("phone", ["unknown", "unavailable"])
async def test_person_with_unknown_presence_counts_as_home(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
    phone: str,
) -> None:
    """Ben's phone loses its presence: Ben counts as home until it is known again."""
    clock.set("2026-11-16 07:00")
    room = await _living_room_with_persons(
        hass, schedules, simulated_trvs, persons, anna="home", ben="home"
    )

    await persons.move("anna", "not_home")
    await persons.move("ben", phone)
    ben = hass.states.get("person.ben")
    assert ben is not None
    assert ben.state == "unknown"
    await clock.advance_to("2026-11-16 08:00")
    assert away_state(hass, room.entry).state == "off"
    assert room.state(hass).attributes["temperature"] == 21.0

    await persons.move("ben", "not_home")
    await clock.advance_to("2026-11-16 08:30")
    assert away_state(hass, room.entry).state == "on"
    assert room.state(hass).attributes["temperature"] == 16.0


async def test_brief_return_restarts_the_presence_delay(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Anna pops back home for five minutes; the 30 min count again from 07:50."""
    clock.set("2026-11-16 07:30")
    room = await _living_room_with_persons(
        hass, schedules, simulated_trvs, persons, anna="home", ben="home"
    )
    await persons.move("anna", "not_home")
    await persons.move("ben", "not_home")

    await clock.advance_to("2026-11-16 07:45")
    await persons.move("anna", "home")
    await clock.advance_to("2026-11-16 07:50")
    await persons.move("anna", "not_home")

    await clock.advance_to("2026-11-16 08:19:59")
    assert away_state(hass, room.entry).state == "off"
    await clock.advance_to("2026-11-16 08:20:00")
    assert away_state(hass, room.entry).state == "on"
    assert commands(room.trv) == [HEAT_21, HEAT_16]


async def test_override_holds_while_the_house_is_away(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """A room in heat keeps its override; back in auto it gets the away level."""
    clock.set("2026-11-16 07:20")
    room = await _living_room_with_persons(
        hass, schedules, simulated_trvs, persons, anna="home"
    )
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": room.entity_id(hass), "temperature": 23},
        blocking=True,
    )
    await persons.move("anna", "not_home")

    await clock.advance_to("2026-11-16 07:50")
    assert away_state(hass, room.entry).state == "on"
    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0

    await clock.advance_to("2026-11-16 09:00")
    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 16.0
    assert commands(room.trv) == [HEAT_21, HEAT_23, HEAT_16]


async def test_house_empty_for_longer_than_the_presence_delay_is_away_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Everyone left at 06:00; counting them at 07:30 lowers the room at once.

    Changing global settings later keeps the house away.
    """
    clock.set("2026-11-16 06:00")
    entity_ids = await persons.add(anna="not_home", ben="not_home")
    clock.set("2026-11-16 07:30")
    room = await living_room(hass, schedules, simulated_trvs)

    await change_global_settings(
        hass, room.entry, persons=entity_ids, away_temperature=16.0
    )
    assert away_state(hass, room.entry).state == "on"
    assert room.state(hass).attributes["temperature"] == 16.0

    await change_global_settings(hass, room.entry, away_temperature=15.5)
    assert away_state(hass, room.entry).state == "on"
    assert room.state(hass).attributes["temperature"] == 15.5
    assert commands(room.trv) == [HEAT_21, HEAT_16, HEAT_15_5]


async def test_house_without_persons_is_never_away(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """With no persons configured the room simply follows its schedule."""
    clock.set("2026-11-16 07:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await clock.advance_to("2026-11-16 08:59")

    assert away_state(hass, room.entry).state == "off"
    assert room.state(hass).attributes["temperature"] == 21.0
