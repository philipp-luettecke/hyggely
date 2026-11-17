"""Minimal room modes heat and off until the next block boundary; auto ends them.

Override expiry policies, restart behaviour and the reason come with later tickets.
"""

from typing import Any

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    LivingRoom,
    Schedules,
    commands,
    living_room,
)
from tests.simulated_trv import SimulatedTrvs

HEAT_23 = ("set_temperature", {"temperature": 23.0, "hvac_mode": "heat"})
TRV_OFF = ("set_hvac_mode", {"hvac_mode": "off"})


async def _call(
    hass: HomeAssistant, room: LivingRoom, service: str, **data: Any
) -> None:
    await hass.services.async_call(
        "climate",
        service,
        {"entity_id": room.entity_id(hass), **data},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_new_temperature_overrides_until_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A temperature set on the room entity puts the room into heat until 09:00."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await _call(hass, room, "set_temperature", temperature=23)

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    assert commands(room.trv) == [HEAT_21, HEAT_23]

    await clock.advance_to("2026-11-16 09:00:00")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, HEAT_23, HEAT_17]


async def test_auto_ends_the_override_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Tapping auto returns the room to its schedule level immediately."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await _call(hass, room, "set_temperature", temperature=23)

    await _call(hass, room, "set_hvac_mode", hvac_mode="auto")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21, HEAT_23, HEAT_21]


async def test_heat_without_temperature_overrides_with_the_current_target(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Heat keeps the current target and holds it past the block boundary."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await _call(hass, room, "set_hvac_mode", hvac_mode="heat")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 08:59:00")
    assert room.state(hass).state == "heat"
    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).state == "auto"


async def test_off_switches_the_trv_off_until_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Off means frost protection with the TRV off; at 09:00 auto returns."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await _call(hass, room, "set_hvac_mode", hvac_mode="off")

    assert room.state(hass).state == "off"
    assert room.state(hass).attributes["temperature"] == 7.0
    assert commands(room.trv) == [HEAT_21, TRV_OFF]

    await clock.advance_to("2026-11-16 09:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_21, TRV_OFF, HEAT_17]
