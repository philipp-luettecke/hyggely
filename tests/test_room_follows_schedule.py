"""A room in mode auto follows its schedule: comfort during a block, eco outside."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    Schedules,
    add_main_entry,
    add_room,
    block,
    change_room,
    commands,
    living_room,
    room_entity_id,
)
from tests.simulated_trv import SimulatedTrvs


async def test_added_room_is_a_device_in_its_area_with_a_room_entity(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Adding a room creates a device in the chosen area with a room entity."""
    clock.set("2026-11-16 12:00")
    schedule = await schedules.create("Wohnzimmer", monday=[block("07:00", "09:00")])
    trv = await simulated_trvs.add("trv_wohnzimmer")
    area = ar.async_get(hass).async_create("Wohnzimmer")
    entry = await add_main_entry(hass)

    subentry = await add_room(
        hass,
        entry,
        name="Wohnzimmer",
        trv=trv.entity_id,
        schedule=schedule,
        area=area.id,
    )

    room = hass.states.get(room_entity_id(hass, subentry))
    assert room is not None
    assert room.name == "Wohnzimmer"
    assert room.state == "auto"
    assert room.attributes["hvac_modes"] == ["auto", "heat", "off"]
    entity = er.async_get(hass).async_get(room.entity_id)
    assert entity is not None
    assert entity.device_id is not None
    device = dr.async_get(hass).async_get(entity.device_id)
    assert device is not None
    assert device.name == "Wohnzimmer"
    assert device.area_id == area.id


async def test_comfort_applies_during_a_block(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """During a block the room targets comfort and the TRV gets it with heat."""
    clock.set("2026-11-16 08:00")

    room = await living_room(hass, schedules, simulated_trvs)

    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21]


async def test_eco_applies_outside_blocks(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Outside the blocks the room targets eco."""
    clock.set("2026-11-16 12:00")

    room = await living_room(hass, schedules, simulated_trvs)

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_17]


async def test_off_trv_is_switched_to_heat_together_with_the_temperature(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """An off TRV gets mode and temperature in one command."""
    clock.set("2026-11-16 08:00")

    room = await living_room(hass, schedules, simulated_trvs, trv_mode="off")

    assert commands(room.trv) == [HEAT_21]
    trv_state = hass.states.get(room.trv.entity_id)
    assert trv_state is not None
    assert trv_state.state == "heat"
    assert trv_state.attributes["temperature"] == 21.0


async def test_trv_gets_the_new_target_at_each_block_boundary(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """At block start the TRV gets comfort, at block end eco, once each."""
    clock.set("2026-11-16 06:00")
    room = await living_room(hass, schedules, simulated_trvs)
    assert commands(room.trv) == [HEAT_17]

    await clock.advance_to("2026-11-16 06:59:59")
    assert commands(room.trv) == [HEAT_17]

    await clock.advance_to("2026-11-16 07:00:00")
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_17, HEAT_21]

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_17, HEAT_21, HEAT_17]


async def test_trv_already_at_target_gets_no_command(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A TRV already heating to the target is left alone, also at boundaries."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs, trv_temperature=21.0)
    assert commands(room.trv) == []

    room.trv.report(target_temperature=17.0)
    await clock.advance_to("2026-11-16 09:00:00")

    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == []


async def test_schedule_change_applies_to_the_room_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Adding a block covering now switches the room to comfort immediately."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await schedules.update(
        room.schedule,
        "Wohnzimmer",
        monday=[block("07:00", "09:00"), block("11:30", "13:00")],
    )

    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_17, HEAT_21]

    await clock.advance_to("2026-11-16 13:00:00")
    assert commands(room.trv) == [HEAT_17, HEAT_21, HEAT_17]


async def test_room_shows_the_current_temperature_of_the_trv(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The room entity mirrors the current temperature the TRV reports."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs, current_temperature=19.5)
    assert room.state(hass).attributes["current_temperature"] == 19.5

    room.trv.report(current_temperature=20.5)
    await hass.async_block_till_done()

    assert room.state(hass).attributes["current_temperature"] == 20.5


async def test_changed_levels_in_the_room_options_apply_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A new comfort temperature in the room options reaches the TRV."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await change_room(hass, room.entry, room.subentry, comfort_temperature=22.5)

    assert room.subentry.data["comfort_temperature"] == 22.5
    assert room.state(hass).attributes["temperature"] == 22.5
    assert commands(room.trv)[-1] == (
        "set_temperature",
        {"temperature": 22.5, "hvac_mode": "heat"},
    )


async def test_room_moves_to_another_area_in_the_room_options(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Choosing another area in the room options moves the room device."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    office = ar.async_get(hass).async_create("Büro")

    await change_room(hass, room.entry, room.subentry, area=office.id, name="Büro")

    entity = er.async_get(hass).async_get(room.state(hass).entity_id)
    assert entity is not None
    assert entity.device_id is not None
    device = dr.async_get(hass).async_get(entity.device_id)
    assert device is not None
    assert device.area_id == office.id
    assert device.name == "Büro"
    assert room.state(hass).name == "Büro"
