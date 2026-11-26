"""Every change of a room's target appears once in the logbook, with its reason."""

from typing import Any

from homeassistant.components.recorder import Recorder
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant.components.recorder.common import (
    async_wait_recording_done,
)
from pytest_homeassistant.typing import MockHAClientWebSocket, WebSocketGenerator

from tests.scenario import (
    Clock,
    LivingRoom,
    Schedules,
    WindowContact,
    block,
    change_room,
    living_room,
    shut_down,
    start_up,
)
from tests.simulated_trv import SimulatedTrvs

DOMAIN = "hyggely"


@pytest.fixture
async def logbook(
    recorder_mock: Recorder, hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> MockHAClientWebSocket:
    """Set up the logbook with an in-memory recorder; the frontend is not needed.

    The connection is opened before the test moves the clock back, so that its
    access token is not issued in the future.
    """
    hass.config.components.add("frontend")
    assert await async_setup_component(hass, "logbook", {})
    await hass.config.async_update(language="de")
    await hass.async_block_till_done()
    return await hass_ws_client(hass)


async def _target_entries(
    hass: HomeAssistant, client: MockHAClientWebSocket, room: LivingRoom
) -> list[tuple[str, str]]:
    """Return (name, message) of the logbook entries about the room's target."""
    await async_wait_recording_done(hass)
    await client.send_json_auto_id(
        {
            "type": "logbook/get_events",
            "start_time": "2026-11-15T00:00:00+01:00",
            "end_time": "2026-11-17T00:00:00+01:00",
            "entity_ids": [room.entity_id(hass)],
        }
    )
    response = await client.receive_json()
    assert response["success"], response
    entries: list[dict[str, Any]] = response["result"]
    return [
        (entry["name"], entry["message"])
        for entry in entries
        if entry.get("domain") == DOMAIN
    ]


async def test_each_block_boundary_logs_the_new_target_with_its_reason(
    logbook: MockHAClientWebSocket,
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Block start and block end each log exactly one entry with target and reason."""
    clock.set("2026-11-16 06:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await clock.advance_to("2026-11-16 07:00:00")
    await clock.advance_to("2026-11-16 09:00:00")

    assert await _target_entries(hass, logbook, room) == [
        ("Wohnzimmer", "21 °C (Komfort bis 09:00)"),
        ("Wohnzimmer", "17 °C (Eco bis 23.11. 07:00)"),
    ]


async def test_open_window_logs_frost_protection_once_with_the_opening_time(
    logbook: MockHAClientWebSocket,
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Airing from 08:03 to 08:20 logs frost since 08:03, then comfort again."""
    clock.set("2026-11-16 08:00")
    window = WindowContact(hass, "fenster_wohnzimmer")
    room = await living_room(
        hass, schedules, simulated_trvs, window_contacts=[window.entity_id]
    )

    await clock.advance_to("2026-11-16 08:03:00")
    await window.open()
    await clock.advance_to("2026-11-16 08:04:00")
    await clock.advance_to("2026-11-16 08:20:00")
    await window.close()

    assert await _target_entries(hass, logbook, room) == [
        ("Wohnzimmer", "7 °C (Fenster offen seit 08:03)"),
        ("Wohnzimmer", "21 °C (Komfort bis 09:00)"),
    ]


async def test_unchanged_target_logs_nothing(
    logbook: MockHAClientWebSocket,
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Setting up, editing a later block and heat at the current target log nothing."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await schedules.update(
        room.schedule,
        "Wohnzimmer",
        monday=[block("07:00", "09:00"), block("17:00", "19:00")],
    )
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": room.entity_id(hass), "hvac_mode": "heat"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert await _target_entries(hass, logbook, room) == []


async def test_target_changed_during_a_restart_is_logged_once_after_start(
    logbook: MockHAClientWebSocket,
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Home Assistant was down from 06:30 to 07:30 and missed the 07:00 block start."""
    clock.set("2026-11-16 06:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await shut_down(hass, room.entry)
    await clock.advance_to("2026-11-16 07:30:00")

    await start_up(hass, room.entry)

    assert await _target_entries(hass, logbook, room) == [
        ("Wohnzimmer", "21 °C (Komfort bis 09:00)"),
    ]


async def test_target_unchanged_during_a_restart_logs_nothing(
    logbook: MockHAClientWebSocket,
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Down from 07:30 to 08:00 within the comfort block: nothing to log."""
    clock.set("2026-11-16 07:30")
    room = await living_room(hass, schedules, simulated_trvs)
    await shut_down(hass, room.entry)
    await clock.advance_to("2026-11-16 08:00:00")

    await start_up(hass, room.entry)

    assert await _target_entries(hass, logbook, room) == []


async def test_new_comfort_temperature_in_the_room_options_is_logged_once(
    logbook: MockHAClientWebSocket,
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Changing the comfort temperature during a block logs the new target."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await change_room(hass, room.entry, room.subentry, comfort_temperature=21.5)

    assert await _target_entries(hass, logbook, room) == [
        ("Wohnzimmer", "21,5 °C (Komfort bis 09:00)"),
    ]
