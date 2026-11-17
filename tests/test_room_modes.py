"""Minimal room mode off until the next block boundary; auto ends it.

Restoring off after a restart and its reason come with ticket 07.
"""

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    Schedules,
    commands,
    living_room,
)
from tests.simulated_trv import SimulatedTrvs

TRV_OFF = ("set_hvac_mode", {"hvac_mode": "off"})


async def test_off_switches_the_trv_off_until_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Off means frost protection with the TRV off; at 09:00 auto returns."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    assert room.state(hass).state == "off"
    assert room.state(hass).attributes["temperature"] == 7.0
    assert commands(room.trv) == [HEAT_21, TRV_OFF]

    await clock.advance_to("2026-11-16 09:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_21, TRV_OFF, HEAT_17]
