"""Blocks carry a level; the lead time applies a block's level before it starts."""

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_16,
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
