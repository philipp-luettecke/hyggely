"""Blocks carry a level; the lead time applies a block's level before it starts."""

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_16,
    HEAT_17,
    HEAT_21,
    Clock,
    Schedules,
    block,
    change_room,
    commands,
    duration,
    living_room,
    local,
)
from tests.simulated_trv import SimulatedTrvs


async def test_night_block_targets_the_night_temperature(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """During a block with level night the room targets the night temperature."""
    clock.set("2026-11-16 23:00")

    room = await living_room(
        hass, schedules, simulated_trvs, monday=[block("22:00", "24:00", "night")]
    )

    assert room.state(hass).attributes["temperature"] == 16.0
    assert commands(room.trv) == [HEAT_16]


async def test_adjacent_blocks_switch_the_level_exactly_at_the_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A block without level is comfort; the night block after it starts on time."""
    clock.set("2026-11-16 08:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        monday=[block("07:00", "09:00"), block("09:00", "11:00", "night")],
    )
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 08:59:59")
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).attributes["temperature"] == 16.0
    assert commands(room.trv) == [HEAT_21, HEAT_16]

    await clock.advance_to("2026-11-16 11:00:00")
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, HEAT_16, HEAT_17]


async def test_lead_time_applies_the_level_of_a_block_before_it_starts(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """With 30 min lead time the room is warm when the 07:00 block starts."""
    clock.set("2026-11-16 06:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        lead_minutes=30,
        monday=[block("07:00", "09:00")],
    )
    assert commands(room.trv) == [HEAT_17]

    await clock.advance_to("2026-11-16 06:29:59")
    assert commands(room.trv) == [HEAT_17]

    await clock.advance_to("2026-11-16 06:30:00")
    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.state(hass).attributes["level"] == "comfort"
    assert commands(room.trv) == [HEAT_17, HEAT_21]

    await clock.advance_to("2026-11-16 07:00:00")
    assert commands(room.trv) == [HEAT_17, HEAT_21]


async def test_lead_time_does_not_lower_before_the_block_ends(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The lead time only moves block starts; eco follows exactly at the block end."""
    clock.set("2026-11-16 08:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        lead_minutes=30,
        monday=[block("07:00", "09:00")],
    )

    await clock.advance_to("2026-11-16 08:30:00")
    await clock.advance_to("2026-11-16 08:59:59")
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, HEAT_17]


async def test_lead_time_warms_up_at_the_end_of_a_night_block(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A comfort block right after a night block starts its lead time in the night."""
    clock.set("2026-11-16 05:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        lead_minutes=30,
        monday=[block("00:00", "06:30", "night"), block("06:30", "08:00")],
    )
    assert commands(room.trv) == [HEAT_16]

    await clock.advance_to("2026-11-16 06:00:00")
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_16, HEAT_21]


async def test_block_starting_at_midnight_starts_its_lead_time_the_evening_before(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A Tuesday block from 00:00 with 30 min lead time applies Monday 23:30."""
    clock.set("2026-11-16 23:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        lead_minutes=30,
        tuesday=[block("00:00", "06:00")],
    )
    assert room.state(hass).attributes["next_block_boundary"] == local(
        "2026-11-16 23:30"
    )

    await clock.advance_to("2026-11-16 23:30:00")
    assert room.state(hass).attributes["temperature"] == 21.0

    await clock.advance_to("2026-11-17 00:00:00")
    assert commands(room.trv) == [HEAT_17, HEAT_21]
    assert room.state(hass).attributes["next_block_boundary"] == local(
        "2026-11-17 06:00"
    )

    await clock.advance_to("2026-11-17 06:00:00")
    assert commands(room.trv) == [HEAT_17, HEAT_21, HEAT_17]


async def test_night_split_at_midnight_holds_through_midnight(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Night 22:00-24:00 and 00:00-06:00 the next day is one night without a switch."""
    clock.set("2026-11-16 22:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        monday=[block("22:00", "24:00", "night")],
        tuesday=[block("00:00", "06:00", "night")],
    )
    assert room.state(hass).attributes["next_block_boundary"] == local(
        "2026-11-17 06:00"
    )

    await clock.advance_to("2026-11-17 00:00:00")
    assert commands(room.trv) == [HEAT_16]

    await clock.advance_to("2026-11-17 06:00:00")
    assert commands(room.trv) == [HEAT_16, HEAT_17]


async def test_week_wraps_from_sunday_night_to_monday_morning(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Sunday's night runs into Monday; Monday's comfort starts with lead time."""
    clock.set("2026-11-22 23:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        lead_minutes=30,
        sunday=[block("22:00", "24:00", "night")],
        monday=[block("00:00", "06:00", "night"), block("06:00", "08:00")],
    )
    assert room.state(hass).attributes["temperature"] == 16.0
    assert room.state(hass).attributes["next_block_boundary"] == local(
        "2026-11-23 05:30"
    )

    await clock.advance_to("2026-11-23 00:00:00")
    assert commands(room.trv) == [HEAT_16]

    await clock.advance_to("2026-11-23 05:30:00")
    assert commands(room.trv) == [HEAT_16, HEAT_21]

    await clock.advance_to("2026-11-23 08:00:00")
    assert room.state(hass).attributes["next_block_boundary"] == local(
        "2026-11-29 21:30"
    )


async def test_next_block_boundary_follows_a_schedule_change(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A new block tomorrow moves the next block boundary, lead time included."""
    clock.set("2026-11-16 12:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        lead_minutes=30,
        monday=[block("07:00", "09:00")],
    )
    assert room.state(hass).attributes["next_block_boundary"] == local(
        "2026-11-23 06:30"
    )

    await schedules.update(
        room.schedule,
        "Wohnzimmer",
        monday=[block("07:00", "09:00")],
        tuesday=[block("08:00", "10:00")],
    )

    assert room.state(hass).attributes["next_block_boundary"] == local(
        "2026-11-17 07:30"
    )


async def test_changed_level_of_a_future_block_applies_at_its_lead_time(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Making tomorrow's block night counts, although the helper looks unchanged."""
    clock.set("2026-11-16 12:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        lead_minutes=30,
        monday=[block("07:00", "09:00")],
        tuesday=[block("07:00", "09:00")],
    )

    await schedules.update(
        room.schedule,
        "Wohnzimmer",
        monday=[block("07:00", "09:00")],
        tuesday=[block("07:00", "09:00", "night")],
    )
    await clock.advance_to("2026-11-17 06:30:00")

    assert room.state(hass).attributes["temperature"] == 16.0
    assert commands(room.trv) == [HEAT_17, HEAT_16]


async def test_night_temperature_and_lead_time_change_in_the_room_options(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A longer lead time and a new night temperature apply at once."""
    clock.set("2026-11-16 06:15")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        monday=[block("07:00", "09:00", "night")],
    )
    assert commands(room.trv) == [HEAT_17]

    await change_room(
        hass,
        room.entry,
        room.subentry,
        night_temperature=18.5,
        lead_time=duration(60),
    )

    assert room.subentry.data["night_temperature"] == 18.5
    assert room.subentry.data["lead_time"] == duration(60)
    assert room.state(hass).attributes["temperature"] == 18.5
    assert commands(room.trv) == [
        HEAT_17,
        ("set_temperature", {"temperature": 18.5, "hvac_mode": "heat"}),
    ]


async def test_room_entity_shows_the_active_level(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The room entity names the level that sets its target."""
    clock.set("2026-11-16 06:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        monday=[block("07:00", "09:00"), block("09:00", "11:00", "night")],
    )
    assert room.state(hass).attributes["level"] == "eco"

    await clock.advance_to("2026-11-16 07:00:00")
    assert room.state(hass).attributes["level"] == "comfort"

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).attributes["level"] == "night"


async def test_override_follows_no_level_and_off_is_the_frost_level(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Off is frost protection; an override follows no level."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": room.entity_id(hass), "temperature": 23},
        blocking=True,
    )
    assert room.state(hass).attributes["level"] is None

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": room.entity_id(hass), "hvac_mode": "off"},
        blocking=True,
    )
    assert room.state(hass).attributes["level"] == "frost"
