"""Override on the room entity: heat to a chosen temperature until the override expiry."""

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    Schedules,
    commands,
    living_room,
    local,
)
from tests.simulated_trv import SimulatedTrvs

HEAT_23 = ("set_temperature", {"temperature": 23.0, "hvac_mode": "heat"})


async def test_new_temperature_overrides_until_the_earlier_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """At 08:00 the block ends at 09:00, before 3 h are up: heat until 09:00."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await room.call(hass, "set_temperature", temperature=23)

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 09:00")
    assert commands(room.trv) == [HEAT_21, HEAT_23]

    await clock.advance_to("2026-11-16 09:00:00")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, HEAT_23, HEAT_17]


async def test_override_falls_back_after_the_duration_when_that_comes_first(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """At 12:00 the next block boundary is a week away: heat for 3 h."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await room.call(hass, "set_temperature", temperature=23)

    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:00")
    await clock.advance_to("2026-11-16 14:59:00")
    assert room.state(hass).state == "heat"

    await clock.advance_to("2026-11-16 15:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_17, HEAT_23, HEAT_17]


async def test_auto_ends_the_override_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Tapping auto returns the room to its schedule level immediately."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)

    await room.call(hass, "set_hvac_mode", hvac_mode="auto")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.state(hass).attributes["override_expiry"] is None
    assert commands(room.trv) == [HEAT_21, HEAT_23, HEAT_21]


async def test_heat_without_temperature_overrides_with_the_current_target(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Heat keeps the current target and holds it until the override expiry."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await room.call(hass, "set_hvac_mode", hvac_mode="heat")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 09:00")
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 08:59:00")
    assert room.state(hass).state == "heat"
    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).state == "auto"
