"""A room with several TRVs: same target for all, the mean as current temperature."""

from dataclasses import dataclass

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import area_registry as ar

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    LivingRoom,
    Schedules,
    add_main_entry,
    add_room,
    block,
    change_room,
    commands,
    duration,
    living_room,
    local,
)
from tests.simulated_trv import SimulatedTrv, SimulatedTrvs

HEAT_22 = ("set_temperature", {"temperature": 22.0, "hvac_mode": "heat"})
TRV_OFF = ("set_hvac_mode", {"hvac_mode": "off"})


@dataclass
class LivingRoomWithTwoTrvs(LivingRoom):
    """The living room with a TRV below the window and one next to the sofa."""

    sofa_trv: SimulatedTrv

    @property
    def trvs(self) -> list[SimulatedTrv]:
        """Return both TRVs, the one below the window first."""
        return [self.trv, self.sofa_trv]


async def _living_room_with_two_trvs(
    hass: HomeAssistant,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    *,
    window_temperature: float = 19.5,
    sofa_temperature: float = 20.5,
) -> LivingRoomWithTwoTrvs:
    """Add the living room with comfort 21 °C Monday 07:00-09:00 and eco 17 °C.

    Both TRVs heat to 17 °C and measure the given current temperatures.
    """
    schedule = await schedules.create("Wohnzimmer", monday=[block("07:00", "09:00")])
    window_trv = await simulated_trvs.add(
        "trv_wohnzimmer_fenster",
        target_temperature=17.0,
        current_temperature=window_temperature,
    )
    sofa_trv = await simulated_trvs.add(
        "trv_wohnzimmer_sofa",
        target_temperature=17.0,
        current_temperature=sofa_temperature,
    )
    area = ar.async_get(hass).async_create("Wohnzimmer")
    entry = await add_main_entry(hass)
    subentry = await add_room(
        hass,
        entry,
        name="Wohnzimmer",
        trvs=[window_trv.entity_id, sofa_trv.entity_id],
        schedule=schedule,
        area=area.id,
        comfort_temperature=21.0,
        eco_temperature=17.0,
    )
    return LivingRoomWithTwoTrvs(entry, subentry, window_trv, schedule, sofa_trv)


async def test_room_with_two_trvs_sends_both_the_same_target(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Both TRVs chosen in the room dialog get comfort at 07:00 and eco at 09:00."""
    clock.set("2026-11-16 06:50")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)
    assert room.subentry.data["trvs"] == [
        "climate.trv_wohnzimmer_fenster",
        "climate.trv_wohnzimmer_sofa",
    ]
    assert [commands(trv) for trv in room.trvs] == [[], []]

    await clock.advance_to("2026-11-16 07:00:00")
    assert [commands(trv) for trv in room.trvs] == [[HEAT_21], [HEAT_21]]

    await clock.advance_to("2026-11-16 09:00:00")
    assert [commands(trv) for trv in room.trvs] == [
        [HEAT_21, HEAT_17],
        [HEAT_21, HEAT_17],
    ]


async def test_trv_added_in_the_room_options_gets_the_target_of_the_room(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A second TRV added to the living room during comfort heats to 21 °C at once."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs, trv_temperature=21.0)
    sofa_trv = await simulated_trvs.add("trv_sofa", target_temperature=17.0)

    await change_room(
        hass,
        room.entry,
        room.subentry,
        trvs=[room.trv.entity_id, sofa_trv.entity_id],
    )

    assert room.subentry.data["trvs"] == [room.trv.entity_id, sofa_trv.entity_id]
    assert commands(room.trv) == []
    assert commands(sofa_trv) == [HEAT_21]


async def test_room_without_trv_is_refused_in_the_room_dialog(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
) -> None:
    """A room needs at least one TRV; the dialog asks again."""
    clock.set("2026-11-16 12:00")
    schedule = await schedules.create("Abstellraum")
    area = ar.async_get(hass).async_create("Abstellraum")
    entry = await add_main_entry(hass)
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": "Abstellraum",
            "trvs": [],
            "schedule": schedule,
            "comfort_temperature": 21.0,
            "night_temperature": 16.0,
            "eco_temperature": 17.0,
            "lead_time": duration(0),
            "area": area.id,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"trvs": "no_trvs"}
    assert entry.subentries == {}


async def test_room_shows_the_mean_current_temperature_of_its_trvs(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """19.5 °C at the window and 20.5 °C at the sofa make 20 °C in the room."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)
    assert room.state(hass).attributes["current_temperature"] == 20.0

    room.sofa_trv.report(current_temperature=21.5)
    await hass.async_block_till_done()

    assert room.state(hass).attributes["current_temperature"] == 20.5


async def test_frozen_trv_does_not_count_for_the_current_temperature(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """During the bridge outage of the sofa TRV only the window TRV counts."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)
    clock.set("2026-11-16 12:00:30")
    room.sofa_trv.unplug_bridge()
    await clock.advance_to("2026-11-16 12:01:00")
    assert room.state(hass).attributes["current_temperature"] == 20.0

    await clock.advance_to("2026-11-16 12:02:00")
    assert room.state(hass).attributes["current_temperature"] == 19.5
    room.trv.report(current_temperature=19.1)
    await hass.async_block_till_done()
    assert room.state(hass).attributes["current_temperature"] == 19.1

    clock.set("2026-11-16 12:10:30")
    room.sofa_trv.plug_in_bridge()
    await clock.advance_to("2026-11-16 12:11:00")
    await clock.advance_to("2026-11-16 12:12:00")
    sofa_state = hass.states.get(room.sofa_trv.entity_id)
    assert sofa_state is not None
    assert sofa_state.state == "unknown"
    assert room.state(hass).attributes["current_temperature"] == 19.1

    await clock.advance_to("2026-11-16 12:13:00")
    await clock.advance_to("2026-11-16 12:14:00")
    assert room.state(hass).attributes["current_temperature"] == 19.8


async def test_room_without_reachable_trv_shows_no_current_temperature(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Both TRVs unavailable: the room shows no current temperature."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)

    room.trv.set_available(False)
    await hass.async_block_till_done()
    assert room.state(hass).attributes["current_temperature"] == 20.5
    room.sofa_trv.set_available(False)
    await hass.async_block_till_done()

    assert room.state(hass).attributes["current_temperature"] is None


async def test_knob_turn_at_one_trv_overrides_the_room_and_syncs_the_other(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Turned to 22 °C at the window, the sofa TRV follows; no second override."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)

    await clock.advance_to("2026-11-16 12:10:20")
    room.trv.turn_knob(22.0)
    await clock.advance_to("2026-11-16 12:11:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 22.0
    assert room.reason(hass).attributes["reason_code"] == "override"
    assert [commands(trv) for trv in room.trvs] == [[], [HEAT_22]]

    await clock.advance_to("2026-11-16 12:12:00")
    await clock.advance_to("2026-11-16 12:13:00")

    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:11")
    assert [commands(trv) for trv in room.trvs] == [[], [HEAT_22]]
    for trv in room.trvs:
        trv_state = hass.states.get(trv.entity_id)
        assert trv_state is not None
        assert trv_state.attributes["temperature"] == 22.0

    await clock.advance_to("2026-11-16 15:11:00")

    assert room.state(hass).state == "auto"
    assert [commands(trv) for trv in room.trvs] == [[HEAT_17], [HEAT_22, HEAT_17]]


async def test_synced_trv_that_did_not_take_the_override_gets_it_once_more(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The sofa TRV reports its 17 °C again; it gets 22 °C again, no new override."""
    clock.set("2026-11-16 12:00")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)
    room.sofa_trv.commands_to_lose = 1

    await clock.advance_to("2026-11-16 12:10:20")
    room.trv.turn_knob(22.0)
    await clock.advance_to("2026-11-16 12:11:00")
    await clock.advance_to("2026-11-16 12:12:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 22.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:11")
    assert [commands(trv) for trv in room.trvs] == [[], [HEAT_22, HEAT_22]]


async def test_switching_off_one_trv_switches_the_room_and_the_other_trv_off(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Switched off at the window during comfort, the sofa TRV goes off as well."""
    clock.set("2026-11-16 08:00")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)

    await clock.advance_to("2026-11-16 08:10:20")
    room.trv.switch_off()
    await clock.advance_to("2026-11-16 08:11:00")
    await clock.advance_to("2026-11-16 08:12:00")

    assert room.state(hass).state == "off"
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 09:00")
    assert [commands(trv) for trv in room.trvs] == [[HEAT_21], [HEAT_21, TRV_OFF]]


async def test_unreachable_trv_gets_the_target_when_it_returns_the_other_follows_now(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """During the outage of the sofa TRV comfort reaches only the window TRV."""
    clock.set("2026-11-16 06:50")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)
    clock.set("2026-11-16 06:57:30")
    room.sofa_trv.unplug_bridge()
    await clock.advance_to("2026-11-16 06:59:00")

    await clock.advance_to("2026-11-16 07:00:00")
    assert [commands(trv) for trv in room.trvs] == [[HEAT_21], []]

    clock.set("2026-11-16 07:05:30")
    room.sofa_trv.plug_in_bridge()
    for minute in ("06", "07", "08", "09"):
        await clock.advance_to(f"2026-11-16 07:{minute}:00")

    assert room.state(hass).state == "auto"
    assert [commands(trv) for trv in room.trvs] == [[HEAT_21], [HEAT_21]]


async def test_trvs_of_one_room_get_their_targets_two_seconds_apart_after_a_restart(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Home Assistant was down at 07:00; on start the sofa TRV follows 2 s later."""
    clock.set("2026-11-16 06:00")
    room = await _living_room_with_two_trvs(hass, schedules, simulated_trvs)
    assert await hass.config_entries.async_unload(room.entry.entry_id)
    await clock.advance_to("2026-11-16 07:30:00")

    hass.set_state(CoreState.starting)
    assert await hass.config_entries.async_setup(room.entry.entry_id)
    await hass.async_block_till_done()
    assert [commands(trv) for trv in room.trvs] == [[HEAT_21], []]

    await clock.advance_to("2026-11-16 07:30:01")
    assert [commands(trv) for trv in room.trvs] == [[HEAT_21], []]
    await clock.advance_to("2026-11-16 07:30:02")
    assert [commands(trv) for trv in room.trvs] == [[HEAT_21], [HEAT_21]]
