"""After a restart of Home Assistant the TRVs are commanded one after another."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CoreState, HomeAssistant, State
from homeassistant.helpers import area_registry as ar, entity_registry as er

from tests.scenario import (
    DOMAIN,
    HEAT_21,
    Clock,
    Schedules,
    add_main_entry,
    add_room,
    block,
    commands,
)
from tests.simulated_trv import SimulatedTrv, SimulatedTrvs


async def _three_rooms(
    hass: HomeAssistant, schedules: Schedules, simulated_trvs: SimulatedTrvs
) -> tuple[ConfigEntry, list[SimulatedTrv]]:
    """Kitchen, living room and dining room share a schedule with 07:00-09:00."""
    schedule = await schedules.create("Erdgeschoss", monday=[block("07:00", "09:00")])
    entry = await add_main_entry(hass)
    trvs: list[SimulatedTrv] = []
    for name in ("Küche", "Wohnzimmer", "Esszimmer"):
        trv = await simulated_trvs.add(f"trv_{len(trvs)}", target_temperature=17.0)
        area = ar.async_get(hass).async_create(name)
        await add_room(
            hass,
            entry,
            name=name,
            trvs=[trv.entity_id],
            schedule=schedule,
            area=area.id,
        )
        trvs.append(trv)
    return entry, trvs


def _commanded(trvs: list[SimulatedTrv]) -> int:
    return sum(1 for trv in trvs if commands(trv) == [HEAT_21])


async def test_trvs_get_their_targets_two_seconds_apart_after_a_restart(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Home Assistant was down at the block start; on start the TRVs follow in turn."""
    clock.set("2026-11-16 06:00")
    entry, trvs = await _three_rooms(hass, schedules, simulated_trvs)
    assert _commanded(trvs) == 0
    assert await hass.config_entries.async_unload(entry.entry_id)
    await clock.advance_to("2026-11-16 07:30:00")

    hass.set_state(CoreState.starting)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert _commanded(trvs) == 1

    await clock.advance_to("2026-11-16 07:30:01")
    assert _commanded(trvs) == 1
    await clock.advance_to("2026-11-16 07:30:02")
    assert _commanded(trvs) == 2
    await clock.advance_to("2026-11-16 07:30:04")
    assert _commanded(trvs) == 3


async def test_trv_reporting_before_its_turn_after_a_restart_is_no_override(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The dining room TRV still at 17 °C reports 18 °C in the room before its turn."""
    clock.set("2026-11-16 06:00")
    entry, trvs = await _three_rooms(hass, schedules, simulated_trvs)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await clock.advance_to("2026-11-16 07:30:00")
    hass.set_state(CoreState.starting)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await clock.advance_to("2026-11-16 07:30:01")
    trvs[2].report(current_temperature=18.0)
    await clock.advance_to("2026-11-16 07:30:04")

    assert _commanded(trvs) == 3
    assert [state.state for state in _room_states(hass)] == ["auto"] * 3
    assert [state.attributes["temperature"] for state in _room_states(hass)] == [
        21.0
    ] * 3


def _room_states(hass: HomeAssistant) -> list[State]:
    states = [
        hass.states.get(entity.entity_id)
        for entity in er.async_get(hass).entities.values()
        if entity.platform == DOMAIN and entity.domain == "climate"
    ]
    return [state for state in states if state is not None]


async def test_trvs_returning_together_get_their_targets_two_seconds_apart(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """TRVs coming back at the same time, e.g. after a restart, are resent in turn."""
    clock.set("2026-11-16 06:00")
    _entry, trvs = await _three_rooms(hass, schedules, simulated_trvs)
    for trv in trvs:
        trv.set_available(False)
    await clock.advance_to("2026-11-16 07:30:00")
    assert _commanded(trvs) == 0

    for trv in trvs:
        trv.set_available(True)
    await hass.async_block_till_done()
    assert _commanded(trvs) == 1

    await clock.advance_to("2026-11-16 07:30:02")
    assert _commanded(trvs) == 2
    await clock.advance_to("2026-11-16 07:30:04")
    assert _commanded(trvs) == 3
