"""TRVs that become unreachable, e.g. on a bridge outage, and come back.

Measured in ticket 01: on a bridge outage the climate entity of a TRV freezes,
only the temperature sensor of its device becomes unavailable.
"""

from homeassistant.core import HomeAssistant

from tests.scenario import HEAT_21, Clock, Schedules, commands, living_room
from tests.simulated_trv import SimulatedTrvs


async def test_trv_gets_no_command_while_its_bridge_is_out(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """At the block boundary during the outage the room changes, the TRV gets nothing."""
    clock.set("2026-11-16 06:50")
    room = await living_room(hass, schedules, simulated_trvs, trv_temperature=17.0)
    assert commands(room.trv) == []

    clock.set("2026-11-16 06:57:30")
    room.trv.unplug_bridge()
    await clock.advance_to("2026-11-16 06:58:00")
    await clock.advance_to("2026-11-16 06:59:00")
    await clock.advance_to("2026-11-16 07:00:00")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == []


async def test_returning_trv_gets_the_target_once_it_reports_a_valid_mode(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Back from the outage, the TRV waits out the invalid mode, then gets comfort."""
    clock.set("2026-11-16 06:50")
    room = await living_room(hass, schedules, simulated_trvs, trv_temperature=17.0)
    clock.set("2026-11-16 06:57:30")
    room.trv.unplug_bridge()
    await clock.advance_to("2026-11-16 06:59:00")
    await clock.advance_to("2026-11-16 07:00:00")

    clock.set("2026-11-16 07:05:30")
    room.trv.plug_in_bridge()
    await clock.advance_to("2026-11-16 07:06:00")
    await clock.advance_to("2026-11-16 07:07:00")
    trv_state = hass.states.get(room.trv.entity_id)
    assert trv_state is not None
    assert trv_state.state == "unknown"
    assert commands(room.trv) == []

    await clock.advance_to("2026-11-16 07:08:00")
    await clock.advance_to("2026-11-16 07:09:00")

    assert commands(room.trv) == [HEAT_21]
    trv_state = hass.states.get(room.trv.entity_id)
    assert trv_state is not None
    assert trv_state.state == "heat"
    assert trv_state.attributes["temperature"] == 21.0
