"""Override on the room entity: heat to a chosen temperature until it expires."""

from homeassistant.core import CoreState, HomeAssistant

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    Schedules,
    block,
    change_global_settings,
    change_room,
    commands,
    living_room,
    local,
    shut_down,
    start_up,
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


async def test_override_is_given_as_reason_until_auto(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The reason reads manual heating until the override expiry, then eco again."""
    await hass.config.async_update(language="de")
    clock.set("2026-11-16 11:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await room.call(hass, "set_temperature", temperature=23)
    assert room.reason(hass).state == "Heizen bis 14:00 (manuell)"
    assert room.state(hass).attributes["reason"] == "override"

    await room.call(hass, "set_hvac_mode", hvac_mode="auto")
    assert room.reason(hass).attributes["reason_code"] == "eco"
    assert room.state(hass).attributes["reason"] == "eco"


async def test_next_block_holds_the_override_until_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """With `next_block` an override at 12:00 lasts until the block at 17:00."""
    clock.set("2026-11-16 12:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        global_settings={"override_expiry_policy": "next_block"},
    )
    await schedules.update(
        room.schedule,
        "Wohnzimmer",
        monday=[block("07:00", "09:00"), block("17:00", "22:00")],
    )

    await room.call(hass, "set_temperature", temperature=23)

    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 17:00")
    await clock.advance_to("2026-11-16 16:59:00")
    assert room.state(hass).state == "heat"

    await clock.advance_to("2026-11-16 17:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_17, HEAT_23, HEAT_21]


async def test_duration_holds_the_override_past_the_next_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """With `duration` of 2 h an override at 08:00 outlasts the block end at 09:00."""
    clock.set("2026-11-16 08:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        global_settings={
            "override_expiry_policy": "duration",
            "override_expiry_duration": {"hours": 2, "minutes": 0, "seconds": 0},
        },
    )

    await room.call(hass, "set_temperature", temperature=23)

    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 10:00")
    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0

    await clock.advance_to("2026-11-16 10:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_21, HEAT_23, HEAT_17]


async def test_room_override_expiry_takes_precedence_over_the_global_one(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room set to fall back after 1 h ignores the global 3 h."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await change_room(
        hass,
        room.entry,
        room.subentry,
        override_expiry_policy="duration",
        override_expiry_duration={"hours": 1, "minutes": 0, "seconds": 0},
    )

    await room.call(hass, "set_temperature", temperature=23)

    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 13:00")
    await clock.advance_to("2026-11-16 13:00:00")
    assert room.state(hass).state == "auto"


async def test_room_with_global_override_expiry_follows_the_main_entry(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room left on the global setting uses the global rule and duration."""
    clock.set("2026-11-16 12:00")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        global_settings={
            "override_expiry_duration": {"hours": 2, "minutes": 0, "seconds": 0}
        },
    )
    await change_room(hass, room.entry, room.subentry, override_expiry_policy="global")

    await room.call(hass, "set_temperature", temperature=23)

    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 14:00")


async def test_new_temperature_during_an_override_updates_temperature_and_expiry(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Turning up again at 13:00 heats to the new value for another 3 h."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)
    await clock.advance_to("2026-11-16 13:00")

    await room.call(hass, "set_temperature", temperature=22)

    assert room.state(hass).attributes["temperature"] == 22.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 16:00")
    await clock.advance_to("2026-11-16 15:00:00")
    assert room.state(hass).state == "heat"
    await clock.advance_to("2026-11-16 16:00:00")
    assert room.state(hass).state == "auto"


async def test_override_survives_a_restart_with_its_remaining_time(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """After a restart at 13:00 the room still heats to 23 °C until 15:00."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)

    await shut_down(hass, room.entry)
    clock.set("2026-11-16 13:00")
    await start_up(hass, room.entry)

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:00")
    assert room.reason(hass).attributes["reason_code"] == "override"
    assert room.reason(hass).attributes["until"] == local("2026-11-16 15:00")
    assert commands(room.trv) == [HEAT_17, HEAT_23]

    await clock.advance_to("2026-11-16 15:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_17, HEAT_23, HEAT_17]


async def test_override_restored_while_home_assistant_starts_reaches_the_trv(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A TRV that lost the override meanwhile gets it again on the paced start."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)
    await shut_down(hass, room.entry)
    room.trv.report(target_temperature=17.0)
    clock.set("2026-11-16 13:00")

    hass.set_state(CoreState.starting)
    await start_up(hass, room.entry)

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:00")
    assert commands(room.trv) == [HEAT_17, HEAT_23, HEAT_23]


async def test_override_expired_during_a_restart_is_auto_right_after_start(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Home Assistant back at 15:30 finds the 15:00 override expiry passed."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)

    await shut_down(hass, room.entry)
    clock.set("2026-11-16 15:30")
    await start_up(hass, room.entry)

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_17, HEAT_23, HEAT_17]


async def test_override_survives_a_change_of_the_global_settings(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Changing the global settings reloads the rooms but keeps the override."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)

    await change_global_settings(hass, room.entry, away_temperature=16.0)

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:00")
    assert commands(room.trv) == [HEAT_17, HEAT_23]


async def test_auto_after_a_restart_stays_auto(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """An override ended with auto does not come back after a restart."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)
    await room.call(hass, "set_hvac_mode", hvac_mode="auto")

    await shut_down(hass, room.entry)
    await start_up(hass, room.entry)

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0


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
