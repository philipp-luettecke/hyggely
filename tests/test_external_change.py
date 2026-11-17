"""External changes at the TRV, e.g. a knob turn, become an override of the room.

Measured in ticket 01: Home Assistant polls the TRVs once a minute, so a knob turn
arrives at the next full minute; a command shows in the TRV state at once.
"""

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
TRV_OFF = ("set_hvac_mode", {"hvac_mode": "off"})


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


async def test_own_command_at_a_block_boundary_is_no_override(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Comfort sent at 07:00 shows in the TRV at once; the room stays on auto."""
    clock.set("2026-11-16 06:50")
    room = await living_room(hass, schedules, simulated_trvs)

    await clock.advance_to("2026-11-16 07:00:00")
    await clock.advance_to("2026-11-16 07:01:00")
    await clock.advance_to("2026-11-16 07:02:00")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.reason(hass).attributes["reason_code"] == "comfort"
    assert commands(room.trv) == [HEAT_17, HEAT_21]


async def test_knob_turned_back_after_the_first_poll_overrides(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Siri set 23 °C at 12:00:30; turning back to 17 °C later is a wish, too."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await clock.advance_to("2026-11-16 12:00:30")
    await room.call(hass, "set_temperature", temperature=23)
    await clock.advance_to("2026-11-16 12:01:00")

    await clock.advance_to("2026-11-16 12:01:30")
    room.trv.turn_knob(17.0)
    await clock.advance_to("2026-11-16 12:02:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:02")
    assert commands(room.trv) == [HEAT_17, HEAT_23]


async def test_command_not_taken_is_sent_once_more_instead_of_overriding(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The first poll after 23 °C shows the 17 °C from before: send 23 °C again."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await clock.advance_to("2026-11-16 12:00:30")
    room.trv.commands_to_lose = 1
    await room.call(hass, "set_temperature", temperature=23)

    await clock.advance_to("2026-11-16 12:01:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    expiry = local("2026-11-16 15:00:30")
    assert room.state(hass).attributes["override_expiry"] == expiry
    assert commands(room.trv) == [HEAT_17, HEAT_23, HEAT_23]
    await clock.advance_to("2026-11-16 12:02:00")
    trv_state = hass.states.get(room.trv.entity_id)
    assert trv_state is not None
    assert trv_state.attributes["temperature"] == 23.0


async def test_command_not_taken_twice_is_not_sent_a_third_time(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Also the repeated 23 °C reverts to 17 °C: no further command, no override."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await clock.advance_to("2026-11-16 12:00:30")
    room.trv.commands_to_lose = 2
    await room.call(hass, "set_temperature", temperature=23)

    await clock.advance_to("2026-11-16 12:01:00")
    await clock.advance_to("2026-11-16 12:02:00")
    await clock.advance_to("2026-11-16 12:03:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    assert commands(room.trv) == [HEAT_17, HEAT_23, HEAT_23]


async def test_switching_off_at_the_trv_means_off_until_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Switched off at 08:10 during comfort, the room is off until 09:00."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await clock.advance_to("2026-11-16 08:10:20")
    room.trv.switch_off()
    await clock.advance_to("2026-11-16 08:11:00")

    assert room.state(hass).state == "off"
    assert room.state(hass).attributes["temperature"] == 7.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 09:00")
    assert room.reason(hass).attributes["reason_code"] == "room_off"
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 09:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_21, HEAT_17]


async def test_knob_turn_while_the_room_is_off_overrides_it(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The room was switched off; turning the knob to 20 °C heats to 20 °C."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    await clock.advance_to("2026-11-16 12:10:20")
    room.trv.turn_knob(20.0)
    await clock.advance_to("2026-11-16 12:11:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 20.0
    assert commands(room.trv) == [HEAT_17, TRV_OFF]


async def test_values_an_off_trv_reports_change_nothing(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """No target, the 7-35 range and a short mode None leave the room off."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    await clock.advance_to("2026-11-16 12:10:20")
    room.trv.report(current_temperature=18.5)
    trv_state = hass.states.get(room.trv.entity_id)
    assert trv_state is not None
    assert trv_state.attributes["temperature"] is None
    assert trv_state.attributes["min_temp"] == 7
    room.trv.report_invalid_mode()
    await clock.advance_to("2026-11-16 12:11:00")
    room.trv.report()
    await clock.advance_to("2026-11-16 12:12:00")

    assert room.state(hass).state == "off"
    assert room.reason(hass).attributes["reason_code"] == "room_off"
    assert commands(room.trv) == [HEAT_17, TRV_OFF, TRV_OFF]


async def test_frozen_values_after_a_bridge_outage_are_no_override(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Auto at 12:06 got lost in the outage; the TRV returns with 23 °C, gets 17 °C."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await clock.advance_to("2026-11-16 12:00:30")
    await room.call(hass, "set_temperature", temperature=23)
    await clock.advance_to("2026-11-16 12:05:30")
    room.trv.unplug_bridge()
    await clock.advance_to("2026-11-16 12:06:10")
    await room.call(hass, "set_hvac_mode", hvac_mode="auto")

    await clock.advance_to("2026-11-16 12:07:00")
    await clock.advance_to("2026-11-16 12:08:30")
    room.trv.plug_in_bridge()
    for minute in ("09", "10", "11", "12"):
        await clock.advance_to(f"2026-11-16 12:{minute}:00")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_17, HEAT_23, HEAT_17, HEAT_17]
    trv_state = hass.states.get(room.trv.entity_id)
    assert trv_state is not None
    assert trv_state.attributes["temperature"] == 17.0
