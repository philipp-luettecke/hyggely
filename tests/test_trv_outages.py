"""TRVs that become unreachable, e.g. on a bridge outage, and come back.

On a bridge outage the climate entity of a TRV freezes, only the temperature
sensor of its device becomes unavailable.
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, issue_registry as ir

from tests.scenario import (
    HEAT_21,
    Clock,
    Schedules,
    add_main_entry,
    add_room,
    block,
    commands,
    living_room,
)
from tests.simulated_trv import SimulatedTrvs


async def test_trv_gets_no_command_while_its_bridge_is_out(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """At a block boundary during the outage the room changes, the TRV gets nothing."""
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


async def test_command_lost_before_the_outage_was_noticed_is_sent_again(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Comfort sent right after the bridge went out is lost; the return repairs it."""
    clock.set("2026-11-16 06:50")
    room = await living_room(hass, schedules, simulated_trvs, trv_temperature=17.0)
    clock.set("2026-11-16 06:59:30")
    room.trv.unplug_bridge()
    await clock.advance_to("2026-11-16 07:00:00")
    assert commands(room.trv) == [HEAT_21]
    await clock.advance_to("2026-11-16 07:01:00")

    clock.set("2026-11-16 07:05:30")
    room.trv.plug_in_bridge()
    for minute in ("06", "07", "08", "09"):
        await clock.advance_to(f"2026-11-16 07:{minute}:00")

    assert commands(room.trv) == [HEAT_21, HEAT_21]
    trv_state = hass.states.get(room.trv.entity_id)
    assert trv_state is not None
    assert trv_state.attributes["temperature"] == 21.0


async def test_invalid_mode_is_ignored_until_the_trv_reports_a_valid_one(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A mode None changes nothing; the next valid report brings the current target."""
    clock.set("2026-11-16 06:50")
    room = await living_room(hass, schedules, simulated_trvs, trv_temperature=17.0)

    room.trv.report_invalid_mode()
    await clock.advance_to("2026-11-16 07:00:00")

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == []

    room.trv.report()
    await hass.async_block_till_done()

    assert commands(room.trv) == [HEAT_21]


async def test_trv_without_temperature_sensor_counts_only_its_climate_entity(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Without a sensor on its device the TRV is unreachable only while unavailable."""
    clock.set("2026-11-16 06:50")
    schedule = await schedules.create("Bad", monday=[block("07:00", "09:00")])
    trv = await simulated_trvs.add(
        "trv_bad", target_temperature=17.0, temperature_sensor=False
    )
    area = ar.async_get(hass).async_create("Bad")
    entry = await add_main_entry(hass)
    await add_room(
        hass, entry, name="Bad", trvs=[trv.entity_id], schedule=schedule, area=area.id
    )

    trv.set_available(False)
    await clock.advance_to("2026-11-16 07:00:00")
    assert commands(trv) == []

    trv.set_available(True)
    await hass.async_block_till_done()
    assert commands(trv) == [HEAT_21]


def _repair_issues(issue_registry: ir.IssueRegistry) -> list[ir.IssueEntry]:
    return [
        issue
        for (domain, _), issue in issue_registry.issues.items()
        if domain == "hyggely"
    ]


async def test_trv_unreachable_for_30_minutes_appears_under_repairs_until_it_returns(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    issue_registry: ir.IssueRegistry,
) -> None:
    """One repair issue per TRV after 30 min unreachable, gone when it is back."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    clock.set("2026-11-16 12:00:30")
    room.trv.unplug_bridge()
    await clock.advance_to("2026-11-16 12:01:00")
    await clock.advance_to("2026-11-16 12:02:00")

    await clock.advance_to("2026-11-16 12:31:59")
    assert _repair_issues(issue_registry) == []

    await clock.advance_to("2026-11-16 12:32:00")
    [issue] = _repair_issues(issue_registry)
    assert issue.translation_key == "trv_offline"
    assert issue.translation_placeholders == {
        "trv": "trv_wohnzimmer",
        "room": "Wohnzimmer",
    }
    assert issue.severity is ir.IssueSeverity.WARNING
    assert not issue.is_fixable

    await clock.advance_to("2026-11-16 13:00:00")
    assert len(_repair_issues(issue_registry)) == 1

    clock.set("2026-11-16 13:00:30")
    room.trv.plug_in_bridge()
    await clock.advance_to("2026-11-16 13:01:00")
    await clock.advance_to("2026-11-16 13:02:00")
    assert _repair_issues(issue_registry) == []


async def test_repair_issue_is_raised_again_when_the_trv_drops_out_again(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    issue_registry: ir.IssueRegistry,
) -> None:
    """A TRV that returns and fails again needs another 30 minutes."""
    clock.set("2026-11-16 12:00")
    room = await living_room(hass, schedules, simulated_trvs)
    room.trv.set_available(False)
    await clock.advance_to("2026-11-16 12:30:00")
    assert len(_repair_issues(issue_registry)) == 1

    room.trv.set_available(True)
    await hass.async_block_till_done()
    assert _repair_issues(issue_registry) == []

    clock.set("2026-11-16 12:40:00")
    room.trv.set_available(False)
    await clock.advance_to("2026-11-16 13:09:59")
    assert _repair_issues(issue_registry) == []
    await clock.advance_to("2026-11-16 13:10:00")
    assert len(_repair_issues(issue_registry)) == 1
