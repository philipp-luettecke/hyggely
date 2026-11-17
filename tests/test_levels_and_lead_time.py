"""Blocks carry a level; the lead time applies a block's level before it starts."""

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_16,
    HEAT_17,
    HEAT_21,
    Clock,
    Schedules,
    block,
    commands,
    living_room,
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
