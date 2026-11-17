"""Room mode off: frost protection with the TRVs off until the next block boundary."""

from typing import Any

from homeassistant.components.climate import HVACMode
from homeassistant.core import CoreState, HomeAssistant

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    LivingRoom,
    Schedules,
    block,
    commands,
    living_room,
    local,
    shut_down,
    start_up,
)
from tests.simulated_trv import SimulatedTrvs

TRV_OFF = ("set_hvac_mode", {"hvac_mode": "off"})
HEAT_23 = ("set_temperature", {"temperature": 23.0, "hvac_mode": "heat"})


async def _living_room_with_evening_block(
    hass: HomeAssistant,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    **global_settings: Any,
) -> LivingRoom:
    """Comfort on Monday 07:00-09:00 and 17:00-22:00, eco in between."""
    return await living_room(
        hass,
        schedules,
        simulated_trvs,
        global_settings=global_settings,
        monday=[block("07:00", "09:00"), block("17:00", "22:00")],
    )


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
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 09:00")
    assert commands(room.trv) == [HEAT_21, TRV_OFF]

    await clock.advance_to("2026-11-16 09:00:00")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert room.state(hass).attributes["override_expiry"] is None
    assert commands(room.trv) == [HEAT_21, TRV_OFF, HEAT_17]


async def test_off_reads_as_off_until_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Switched off at noon, the reason names the evening block at 17:00."""
    await hass.config.async_update(language="de")
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_evening_block(hass, schedules, simulated_trvs)

    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    assert room.reason(hass).state == "Aus bis 17:00"
    assert room.reason(hass).attributes["reason_code"] == "room_off"
    assert room.reason(hass).attributes["until"] == local("2026-11-16 17:00")
    assert room.state(hass).attributes["reason"] == "room_off"

    await clock.advance_to("2026-11-16 17:00:00")

    assert room.reason(hass).state == "Komfort bis 22:00"


async def test_off_outlasts_the_override_duration_until_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """An override would end after 1 h; off at noon holds until 17:00 regardless."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_evening_block(
        hass,
        schedules,
        simulated_trvs,
        override_expiry_policy="duration",
        override_expiry_duration={"hours": 1, "minutes": 0, "seconds": 0},
    )

    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 17:00")
    await clock.advance_to("2026-11-16 13:00:00")
    assert room.state(hass).state == "off"
    await clock.advance_to("2026-11-16 16:59:00")
    assert room.state(hass).state == "off"

    await clock.advance_to("2026-11-16 17:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_17, TRV_OFF, HEAT_21]


async def test_new_temperature_while_off_overrides_until_the_override_expiry(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Turning up a room switched off heats to 23 °C for 3 h, not until 17:00."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_evening_block(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    await room.call(hass, "set_temperature", temperature=23)

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:00")
    assert commands(room.trv) == [HEAT_17, TRV_OFF, HEAT_23]

    await clock.advance_to("2026-11-16 15:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_17, TRV_OFF, HEAT_23, HEAT_17]


async def test_heat_while_off_overrides_with_the_schedule_level_not_frost(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Tapping heat in a room switched off heats to eco 17 °C, not to 7 °C."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_evening_block(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    await room.call(hass, "set_hvac_mode", hvac_mode="heat")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:00")
    assert commands(room.trv) == [HEAT_17, TRV_OFF, HEAT_17]


async def test_auto_ends_off_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Tapping auto in a room switched off follows the schedule again right away."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    await room.call(hass, "set_hvac_mode", hvac_mode="auto")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.state(hass).attributes["override_expiry"] is None
    assert commands(room.trv) == [HEAT_21, TRV_OFF, HEAT_21]


async def test_off_survives_a_restart_until_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """After a restart at 13:00 the room stays off until the evening block at 17:00."""
    await hass.config.async_update(language="de")
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_evening_block(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    await shut_down(hass, room.entry)
    clock.set("2026-11-16 13:00")
    await start_up(hass, room.entry)

    assert room.state(hass).state == "off"
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 17:00")
    assert room.reason(hass).state == "Aus bis 17:00"
    assert commands(room.trv) == [HEAT_17, TRV_OFF]

    await clock.advance_to("2026-11-16 17:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_17, TRV_OFF, HEAT_21]


async def test_off_restored_while_home_assistant_starts_reaches_the_trv(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A TRV heating again after the restart is switched off on the paced start."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_evening_block(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")
    await shut_down(hass, room.entry)
    room.trv.report(hvac_mode=HVACMode.HEAT)
    clock.set("2026-11-16 13:00")

    hass.set_state(CoreState.starting)
    await start_up(hass, room.entry)

    assert room.state(hass).state == "off"
    assert commands(room.trv) == [HEAT_17, TRV_OFF, TRV_OFF]


async def test_off_ended_during_a_restart_is_auto_right_after_start(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Home Assistant back at 17:30 finds the 17:00 block boundary passed."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_evening_block(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    await shut_down(hass, room.entry)
    clock.set("2026-11-16 17:30")
    await start_up(hass, room.entry)

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_17, TRV_OFF, HEAT_21]
