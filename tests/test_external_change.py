"""External changes at the TRV, e.g. a knob turn, become an override of the room.

Measured in ticket 01: Home Assistant polls the TRVs once a minute, so a knob turn
arrives at the next full minute; a command shows in the TRV state at once.
"""

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_17,
    Clock,
    Schedules,
    commands,
    living_room,
    local,
)
from tests.simulated_trv import SimulatedTrvs


async def test_knob_turn_overrides_the_room_with_the_new_temperature(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Turned to 22 °C at 12:10:20, the room heats to 22 °C from the poll at 12:11."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await clock.advance_to("2026-11-16 12:10:20")
    room.trv.turn_knob(22.0)
    await clock.advance_to("2026-11-16 12:10:59")
    assert room.state(hass).state == "auto"

    await clock.advance_to("2026-11-16 12:11:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 22.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:11")
    assert room.reason(hass).attributes["reason_code"] == "override"
    assert commands(room.trv) == [HEAT_17]

    await clock.advance_to("2026-11-16 15:11:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_17, HEAT_17]
