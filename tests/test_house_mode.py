"""House mode: vacation lowers all rooms until the vacation end, off protects them.

Ranking below window open: room off > override > house off > vacation > away >
schedule.
"""

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import area_registry as ar
from homeassistant.util import dt as dt_util
import pytest

from tests.scenario import (
    HEAT_16,
    HEAT_17,
    HEAT_21,
    Clock,
    House,
    LivingRoom,
    Persons,
    Schedules,
    add_room,
    away_state,
    block,
    change_global_settings,
    commands,
    living_room,
    local,
    room_entity_id,
    shut_down,
    start_up,
)
from tests.simulated_trv import SimulatedTrv, SimulatedTrvs

HEAT_14 = ("set_temperature", {"temperature": 14.0, "hvac_mode": "heat"})
HEAT_15 = ("set_temperature", {"temperature": 15.0, "hvac_mode": "heat"})
HEAT_20 = ("set_temperature", {"temperature": 20.0, "hvac_mode": "heat"})
HEAT_23 = ("set_temperature", {"temperature": 23.0, "hvac_mode": "heat"})
TRV_OFF = ("set_hvac_mode", {"hvac_mode": "off"})


async def _speak_german(hass: HomeAssistant) -> None:
    await hass.config.async_update(language="de")
    await hass.async_block_till_done()


async def _go_on_vacation(house: House, until: str) -> None:
    await house.set_vacation_end(until)
    await house.select("vacation")


async def _add_kitchen(
    hass: HomeAssistant,
    room: LivingRoom,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> tuple[str, SimulatedTrv]:
    """Add the kitchen, comfort 20 °C Monday to Friday 06:00-22:00.

    Return the entity id of its room entity and its TRV.
    """
    schedule = await schedules.create(
        "Küche",
        **{
            day: [block("06:00", "22:00")]
            for day in ("monday", "tuesday", "wednesday", "thursday", "friday")
        },
    )
    trv = await simulated_trvs.add("trv_kueche", target_temperature=15.0)
    area = ar.async_get(hass).async_create("Küche")
    subentry = await add_room(
        hass,
        room.entry,
        name="Küche",
        trv=trv.entity_id,
        schedule=schedule,
        area=area.id,
        comfort_temperature=20.0,
    )
    return room_entity_id(hass, subentry), trv


async def test_vacation_lowers_every_room_until_the_vacation_end(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Away from Monday 08:00 to Friday 18:00: both rooms at 15 °C, then auto."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    kitchen, kitchen_trv = await _add_kitchen(hass, room, schedules, simulated_trvs)
    house = House(hass, room.entry)

    await _go_on_vacation(house, "2026-11-20 18:00")

    assert house.house_mode.state == "vacation"
    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 15.0
    assert room.state(hass).attributes["level"] == "vacation"
    kitchen_state = hass.states.get(kitchen)
    assert kitchen_state is not None
    assert kitchen_state.attributes["temperature"] == 15.0
    assert commands(room.trv) == [HEAT_21, HEAT_15]
    assert commands(kitchen_trv) == [HEAT_20, HEAT_15]

    await clock.advance_to("2026-11-20 17:59:59")
    assert house.house_mode.state == "vacation"
    assert room.state(hass).attributes["temperature"] == 15.0

    await clock.advance_to("2026-11-20 18:00:00")
    assert house.house_mode.state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, HEAT_15, HEAT_17]
    assert commands(kitchen_trv) == [HEAT_20, HEAT_15, HEAT_20]


async def test_reason_names_the_vacation_end(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """On vacation the reason reads vacation until Friday 18:00, with the date."""
    await _speak_german(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await _go_on_vacation(House(hass, room.entry), "2026-11-20 18:00")

    assert room.reason(hass).state == "Urlaub bis 20.11. 18:00"
    assert room.reason(hass).attributes["reason_code"] == "vacation"
    assert room.reason(hass).attributes["until"] == local("2026-11-20 18:00")


async def test_vacation_without_a_vacation_end_in_the_future_is_refused(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Vacation never runs open-ended: without a future end the house stays auto."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)
    assert house.vacation_end.state == "unknown"

    with pytest.raises(ServiceValidationError) as no_end:
        await house.select("vacation")
    await house.set_vacation_end("2026-11-16 07:00")
    with pytest.raises(ServiceValidationError):
        await house.select("vacation")

    assert no_end.value.translation_key == "vacation_end_not_ahead"
    assert house.house_mode.state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21]


async def test_moving_the_vacation_end_lengthens_or_ends_the_vacation(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Vacation extended to Friday, then ended early on Thursday by setting the end."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)
    await _go_on_vacation(house, "2026-11-18 18:00")

    await house.set_vacation_end("2026-11-20 18:00")
    await clock.advance_to("2026-11-18 18:00:00")
    assert house.house_mode.state == "vacation"

    await clock.advance_to("2026-11-19 10:00:00")
    await house.set_vacation_end("2026-11-19 10:00")

    assert house.house_mode.state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, HEAT_15, HEAT_17]


async def test_house_off_gives_every_room_frost_protection_until_auto(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """House off switches the TRVs off past block boundaries; auto resumes the plan."""
    await _speak_german(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    _kitchen, kitchen_trv = await _add_kitchen(hass, room, schedules, simulated_trvs)
    house = House(hass, room.entry)

    await house.select("off")

    assert house.house_mode.state == "off"
    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 7.0
    assert room.state(hass).attributes["level"] == "frost"
    assert room.reason(hass).state == "Haus aus"
    assert room.reason(hass).attributes["reason_code"] == "house_off"
    assert commands(room.trv) == [HEAT_21, TRV_OFF]
    assert commands(kitchen_trv) == [HEAT_20, TRV_OFF]

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).attributes["temperature"] == 7.0

    await house.select("auto")
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, TRV_OFF, HEAT_17]
    assert commands(kitchen_trv) == [HEAT_20, TRV_OFF, HEAT_20]


async def test_override_beats_vacation_and_returns_to_vacation(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Heating to 23 °C holds when vacation starts; at expiry the room gets 15 °C."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)

    await _go_on_vacation(House(hass, room.entry), "2026-11-20 18:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    assert room.reason(hass).attributes["reason_code"] == "override"

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 15.0
    assert commands(room.trv) == [HEAT_21, HEAT_23, HEAT_15]


async def test_override_beats_house_off_and_returns_to_frost_protection(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Coming home early to a house off: 23 °C until 09:00, then the TRV is off."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await House(hass, room.entry).select("off")

    await room.call(hass, "set_temperature", temperature=23)

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 7.0
    assert commands(room.trv) == [HEAT_21, TRV_OFF, HEAT_23, TRV_OFF]


async def test_room_off_beats_house_off(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room switched off reads as off until 09:00, then as house off."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await House(hass, room.entry).select("off")

    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    assert room.state(hass).state == "off"
    assert room.reason(hass).attributes["reason_code"] == "room_off"

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).state == "auto"
    assert room.reason(hass).attributes["reason_code"] == "house_off"
    assert commands(room.trv) == [HEAT_21, TRV_OFF]


async def _living_room_while_away(
    hass: HomeAssistant,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
    clock: Clock,
) -> LivingRoom:
    """At 08:30 Anna has been gone for 30 min: the house is away at 16 °C."""
    clock.set("2026-11-16 08:00")
    entity_ids = await persons.add(anna="not_home")
    room = await living_room(hass, schedules, simulated_trvs)
    await change_global_settings(
        hass, room.entry, persons=entity_ids, away_temperature=16.0
    )
    await clock.advance_to("2026-11-16 08:30")
    assert away_state(hass, room.entry).state == "on"
    return room


async def test_vacation_beats_away(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Away and on vacation: 15 °C; after the vacation end the house is away again."""
    room = await _living_room_while_away(
        hass, schedules, simulated_trvs, persons, clock
    )

    await _go_on_vacation(House(hass, room.entry), "2026-11-20 18:00")

    assert room.state(hass).attributes["temperature"] == 15.0
    assert room.reason(hass).attributes["reason_code"] == "vacation"

    await clock.advance_to("2026-11-20 18:00:00")
    assert room.state(hass).attributes["temperature"] == 16.0
    assert room.reason(hass).attributes["reason_code"] == "away"
    assert commands(room.trv) == [HEAT_21, HEAT_16, HEAT_15, HEAT_16]


async def test_house_off_beats_away(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Away and house off: frost protection; back to auto the house is away."""
    room = await _living_room_while_away(
        hass, schedules, simulated_trvs, persons, clock
    )
    house = House(hass, room.entry)

    await house.select("off")
    assert room.reason(hass).attributes["reason_code"] == "house_off"

    await house.select("auto")
    assert room.reason(hass).attributes["reason_code"] == "away"
    assert commands(room.trv) == [HEAT_21, HEAT_16, TRV_OFF, HEAT_16]


async def test_vacation_survives_a_restart(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """After a restart on Tuesday the house is still on vacation until Friday 18:00."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)
    await _go_on_vacation(house, "2026-11-20 18:00")

    await shut_down(hass, room.entry)
    clock.set("2026-11-17 08:00")
    await start_up(hass, room.entry)

    assert house.house_mode.state == "vacation"
    assert dt_util.parse_datetime(house.vacation_end.state) == local(
        "2026-11-20 18:00"
    )
    assert room.state(hass).attributes["temperature"] == 15.0
    assert commands(room.trv) == [HEAT_21, HEAT_15]

    await clock.advance_to("2026-11-20 18:00:00")
    assert house.house_mode.state == "auto"
    assert commands(room.trv) == [HEAT_21, HEAT_15, HEAT_17]


async def test_vacation_ended_during_a_restart_is_auto_right_after_start(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Home Assistant back at 19:00 finds the 18:00 vacation end passed."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)
    await _go_on_vacation(house, "2026-11-20 18:00")

    await shut_down(hass, room.entry)
    clock.set("2026-11-20 19:00")
    await start_up(hass, room.entry)

    assert house.house_mode.state == "auto"
    assert dt_util.parse_datetime(house.vacation_end.state) == local(
        "2026-11-20 18:00"
    )
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, HEAT_15, HEAT_17]


async def test_house_off_survives_a_restart(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A house switched off stays off after a restart, whatever the schedule says."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)
    await house.select("off")

    await shut_down(hass, room.entry)
    clock.set("2026-11-23 07:30")
    await start_up(hass, room.entry)

    assert house.house_mode.state == "off"
    assert room.state(hass).attributes["temperature"] == 7.0
    assert commands(room.trv) == [HEAT_21, TRV_OFF]


async def test_vacation_follows_a_changed_vacation_temperature(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Lowering the vacation temperature during vacation keeps the vacation."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)
    await _go_on_vacation(house, "2026-11-20 18:00")

    await change_global_settings(hass, room.entry, vacation_temperature=14.0)

    assert house.house_mode.state == "vacation"
    assert room.state(hass).attributes["temperature"] == 14.0
    assert commands(room.trv) == [HEAT_21, HEAT_15, HEAT_14]
