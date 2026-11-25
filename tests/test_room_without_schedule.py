"""A room without schedule, or whose schedule helper is missing, holds eco."""

from typing import Any

from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import area_registry as ar

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    Schedules,
    WindowContact,
    add_main_entry,
    add_room,
    block,
    change_global_settings,
    change_room,
    commands,
    living_room,
    reason_entity_id,
    room_entity_id,
)
from tests.simulated_trv import SimulatedTrv, SimulatedTrvs


async def _room_without_schedule(
    hass: HomeAssistant,
    simulated_trvs: SimulatedTrvs,
    *,
    window_contacts: list[str] | None = None,
) -> tuple[ConfigSubentry, SimulatedTrv]:
    """Add the living room without schedule: comfort 21 °C, eco 17 °C."""
    trv = await simulated_trvs.add("trv_wohnzimmer", target_temperature=15.0)
    area = ar.async_get(hass).async_create("Wohnzimmer")
    entry = await add_main_entry(hass)
    subentry = await add_room(
        hass,
        entry,
        name="Wohnzimmer",
        trvs=[trv.entity_id],
        schedule=None,
        area=area.id,
        comfort_temperature=21.0,
        eco_temperature=17.0,
        window_contacts=window_contacts,
    )
    return subentry, trv


def _state(hass: HomeAssistant, entity_id: str) -> State:
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def _call(
    hass: HomeAssistant, subentry: ConfigSubentry, service: str, **data: Any
) -> None:
    await hass.services.async_call(
        "climate",
        service,
        {"entity_id": room_entity_id(hass, subentry), **data},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_room_without_schedule_holds_eco(
    hass: HomeAssistant,
    clock: Clock,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room added without schedule targets eco and says so in its reason."""
    await hass.config.async_update(language="de")
    clock.set("2026-11-16 08:00")

    subentry, trv = await _room_without_schedule(hass, simulated_trvs)

    room = _state(hass, room_entity_id(hass, subentry))
    assert room.state == "auto"
    assert room.attributes["temperature"] == 17.0
    assert commands(trv) == [HEAT_17]
    reason = _state(hass, reason_entity_id(hass, subentry))
    assert reason.state == "Kein Zeitplan \N{EN DASH} Eco"
    assert reason.attributes["reason_code"] == "no_schedule"


async def test_room_holds_eco_once_its_schedule_helper_is_deleted(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """During a comfort block the helper disappears; the room lowers to eco."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    assert commands(room.trv) == [HEAT_21]

    await schedules.delete(room.schedule)

    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_21, HEAT_17]
    assert room.reason(hass).attributes["reason_code"] == "no_schedule"


async def test_window_open_in_a_room_without_schedule_gives_frost_protection(
    hass: HomeAssistant,
    clock: Clock,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The window rule still applies; closing it returns to eco."""
    clock.set("2026-11-16 08:00")
    window = WindowContact(hass, "fenster_wohnzimmer")
    subentry, trv = await _room_without_schedule(
        hass, simulated_trvs, window_contacts=[window.entity_id]
    )

    await window.open()
    await clock.advance_to("2026-11-16 08:01:00")

    assert commands(trv) == [HEAT_17, ("set_hvac_mode", {"hvac_mode": "off"})]
    reason = _state(hass, reason_entity_id(hass, subentry))
    assert reason.attributes["reason_code"] == "window_open"

    await window.close()

    assert commands(trv)[-1] == HEAT_17
    reason = _state(hass, reason_entity_id(hass, subentry))
    assert reason.attributes["reason_code"] == "no_schedule"


async def test_override_in_a_room_without_schedule_expires_after_the_duration(
    hass: HomeAssistant,
    clock: Clock,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Without block boundary the default rule ends the override after 3 hours."""
    clock.set("2026-11-16 08:00")
    subentry, trv = await _room_without_schedule(hass, simulated_trvs)

    await _call(hass, subentry, "set_temperature", temperature=21)

    assert _state(hass, room_entity_id(hass, subentry)).state == "heat"
    assert commands(trv) == [HEAT_17, HEAT_21]

    await clock.advance_to("2026-11-16 11:00:00")

    assert _state(hass, room_entity_id(hass, subentry)).state == "auto"
    assert commands(trv) == [HEAT_17, HEAT_21, HEAT_17]


async def test_heat_without_temperature_in_a_room_without_schedule_keeps_eco(
    hass: HomeAssistant,
    clock: Clock,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Choosing heat on the room entity overrides with the current eco target."""
    clock.set("2026-11-16 08:00")
    subentry, _trv = await _room_without_schedule(hass, simulated_trvs)

    await _call(hass, subentry, "set_hvac_mode", hvac_mode="heat")

    room = _state(hass, room_entity_id(hass, subentry))
    assert room.state == "heat"
    assert room.attributes["temperature"] == 17.0


async def test_room_off_without_schedule_returns_to_auto_after_the_duration(
    hass: HomeAssistant,
    clock: Clock,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Without block boundary off ends after the override duration, 3 hours."""
    await hass.config.async_update(language="de")
    clock.set("2026-11-16 08:00")
    subentry, trv = await _room_without_schedule(hass, simulated_trvs)

    await _call(hass, subentry, "set_hvac_mode", hvac_mode="off")

    assert _state(hass, reason_entity_id(hass, subentry)).state == "Aus bis 11:00"

    await clock.advance_to("2026-11-16 11:00:00")

    assert _state(hass, room_entity_id(hass, subentry)).state == "auto"
    assert commands(trv)[-1] == HEAT_17


async def test_override_with_next_block_rule_ends_after_the_duration_without_schedule(
    hass: HomeAssistant,
    clock: Clock,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The rule next block boundary falls back to the duration without one."""
    clock.set("2026-11-16 08:00")
    subentry, trv = await _room_without_schedule(hass, simulated_trvs)
    [entry] = hass.config_entries.async_entries("climate_control")
    await change_global_settings(hass, entry, override_expiry_policy="next_block")

    await _call(hass, subentry, "set_temperature", temperature=21)
    await clock.advance_to("2026-11-16 11:00:00")

    assert _state(hass, room_entity_id(hass, subentry)).state == "auto"
    assert commands(trv)[-1] == HEAT_17


async def test_room_off_with_a_schedule_without_blocks_returns_after_the_duration(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A schedule without blocks has no block boundary either."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs, monday=[])

    await room.call(hass, "set_hvac_mode", hvac_mode="off")
    await clock.advance_to("2026-11-16 11:00:00")

    assert room.state(hass).state == "auto"
    assert commands(room.trv)[-1] == HEAT_17


async def test_schedule_assigned_in_the_room_options_applies_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room set up without schedule follows the one chosen later."""
    clock.set("2026-11-16 08:00")
    subentry, trv = await _room_without_schedule(hass, simulated_trvs)
    schedule = await schedules.create("Wohnzimmer", monday=[block("07:00", "09:00")])

    [entry] = hass.config_entries.async_entries("climate_control")

    await change_room(hass, entry, subentry, schedule=schedule)

    assert commands(trv) == [HEAT_17, HEAT_21]
    reason = _state(hass, reason_entity_id(hass, subentry))
    assert reason.attributes["reason_code"] == "comfort"


async def test_schedule_removed_in_the_room_options_leaves_the_room_at_eco(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Clearing the schedule in the room options lowers the room to eco."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await change_room(hass, room.entry, room.subentry, without=("schedule",))

    assert commands(room.trv) == [HEAT_21, HEAT_17]
    assert room.reason(hass).attributes["reason_code"] == "no_schedule"
