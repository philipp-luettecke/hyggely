"""Panel API, house: house mode, vacation with its end, away with the persons."""

from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant.typing import MockHAClientWebSocket, WebSocketGenerator
import pytest

from tests.scenario import (
    Clock,
    House,
    Persons,
    Schedules,
    change_global_settings,
    living_room,
)
from tests.simulated_trv import SimulatedTrvs


async def _subscribe(client: MockHAClientWebSocket) -> dict[str, Any]:
    """Subscribe to the house; return the state it starts with."""
    await client.send_json_auto_id({"type": "climate_control/house/subscribe"})
    response = await client.receive_json()
    assert response["success"], response
    message = await client.receive_json()
    assert message["type"] == "event", message
    house: dict[str, Any] = message["event"]
    return house


async def _latest_house(client: MockHAClientWebSocket) -> dict[str, Any]:
    """Return the house of the last update sent so far."""
    await client.send_json_auto_id({"type": "ping"})
    latest = None
    while (message := await client.receive_json())["type"] != "pong":
        assert message["type"] == "event", message
        latest = message["event"]
    assert latest is not None, "no update"
    house: dict[str, Any] = latest
    return house


async def _set_house_mode(
    client: MockHAClientWebSocket, house_mode: str
) -> dict[str, Any]:
    await client.send_json_auto_id(
        {"type": "climate_control/house/set_mode", "house_mode": house_mode}
    )
    response: dict[str, Any] = await client.receive_json()
    return response


async def _start_vacation(client: MockHAClientWebSocket, end: str) -> dict[str, Any]:
    """Start vacation until `end`, local time as the panel sends it."""
    await client.send_json_auto_id(
        {"type": "climate_control/house/start_vacation", "end": end}
    )
    response: dict[str, Any] = await client.receive_json()
    return response


async def test_house_shows_house_mode_vacation_end_away_and_every_person(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Anna at home, Ben at work, Carla's phone silent: Carla counts as home."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    entity_ids = await persons.add(anna="home", ben="Arbeit", carla="unknown")
    room = await living_room(hass, schedules, simulated_trvs)
    await change_global_settings(hass, room.entry, persons=entity_ids)

    house = await _subscribe(admin)

    assert house == {
        "house_mode": "auto",
        "vacation_end": None,
        "away": False,
        "persons": [
            {"entity_id": "person.anna", "name": "Anna", "presence": "home"},
            {"entity_id": "person.ben", "name": "Ben", "presence": "not_home"},
            {"entity_id": "person.carla", "name": "Carla", "presence": "unknown"},
        ],
    }


async def test_house_reports_changes_made_outside_the_panel_at_once(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Siri switches the house off, Anna leaves and the house becomes away."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    entity_ids = await persons.add(anna="home")
    room = await living_room(hass, schedules, simulated_trvs)
    await change_global_settings(hass, room.entry, persons=entity_ids)
    await _subscribe(admin)

    await House(hass, room.entry).select("off")
    assert (await _latest_house(admin))["house_mode"] == "off"

    await persons.move("anna", "not_home")
    house = await _latest_house(admin)
    assert house["persons"][0]["presence"] == "not_home"
    assert house["away"] is False

    await clock.advance_to("2026-11-16 08:30")
    assert (await _latest_house(admin))["away"] is True


async def test_house_keeps_reporting_after_the_global_settings_change(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    persons: Persons,
) -> None:
    """Adding Ben in the options reloads the entry; the panel lists him and follows on."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    entity_ids = await persons.add(anna="home", ben="home")
    room = await living_room(hass, schedules, simulated_trvs)
    await change_global_settings(hass, room.entry, persons=entity_ids[:1])
    await _subscribe(admin)

    await change_global_settings(hass, room.entry, persons=entity_ids)
    house = await _latest_house(admin)
    assert [person["name"] for person in house["persons"]] == ["Anna", "Ben"]

    await House(hass, room.entry).select("off")
    assert (await _latest_house(admin))["house_mode"] == "off"


async def test_house_mode_can_be_switched_from_the_panel(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Off gives frost protection, auto brings back the schedule."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)

    assert (await _set_house_mode(admin, "off"))["success"]
    assert house.house_mode.state == "off"
    assert room.state(hass).attributes["temperature"] == 7.0

    assert (await _set_house_mode(admin, "auto"))["success"]
    assert house.house_mode.state == "auto"
    assert room.state(hass).attributes["temperature"] == 21.0


async def test_vacation_is_not_a_house_mode_to_switch_to_directly(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Vacation starts only with its end, so switching to it is refused."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    response = await _set_house_mode(admin, "vacation")

    assert not response["success"]
    assert House(hass, room.entry).house_mode.state == "auto"


async def test_vacation_starts_with_its_end_in_one_command(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The panel sends the end in local time; the panel shows it back."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    response = await _start_vacation(admin, "2026-11-20T18:00")

    assert response["success"], response
    assert House(hass, room.entry).house_mode.state == "vacation"
    assert room.state(hass).attributes["temperature"] == 15.0
    house = await _subscribe(admin)
    assert house["house_mode"] == "vacation"
    assert house["vacation_end"] == "2026-11-20T18:00:00+01:00"


async def test_vacation_end_can_be_moved_during_the_vacation(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Extended from Friday to Sunday: the house stays on vacation until Sunday."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    house = House(hass, room.entry)
    await _start_vacation(admin, "2026-11-20T18:00")

    await _start_vacation(admin, "2026-11-22T18:00")

    await clock.advance_to("2026-11-20 18:00:00")
    assert house.house_mode.state == "vacation"
    await clock.advance_to("2026-11-22 18:00:00")
    assert house.house_mode.state == "auto"


async def test_vacation_with_an_end_not_in_the_future_is_refused(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """An end before now is refused with the same code as the service."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    response = await _start_vacation(admin, "2026-11-16T07:00")

    assert not response["success"]
    assert response["error"]["code"] == "vacation_end_must_be_ahead"
    assert House(hass, room.entry).house_mode.state == "auto"


@pytest.mark.parametrize(
    "message",
    [
        {"type": "climate_control/house/subscribe"},
        {"type": "climate_control/house/set_mode", "house_mode": "off"},
        {"type": "climate_control/house/start_vacation", "end": "2026-11-20T18:00"},
    ],
)
async def test_house_is_refused_to_other_users(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    message: dict[str, Any],
) -> None:
    """A user without admin rights neither sees nor changes the house."""
    user = await hass_ws_client(hass, hass_read_only_access_token)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await user.send_json_auto_id(message)
    response = await user.receive_json()

    assert response["error"]["code"] == "unauthorized"
    assert House(hass, room.entry).house_mode.state == "auto"
