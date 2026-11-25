"""Panel API: room overview with live updates and return to auto, for admins only."""

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from pytest_homeassistant.typing import MockHAClientWebSocket, WebSocketGenerator

from tests.scenario import (
    Clock,
    Schedules,
    add_room,
    block,
    change_room,
    living_room,
)
from tests.simulated_trv import SimulatedTrvs


async def _subscribe(client: MockHAClientWebSocket) -> list[dict[str, Any]]:
    """Subscribe to the room overview; return the rooms it starts with."""
    await client.send_json_auto_id({"type": "climate_control/rooms/subscribe"})
    response = await client.receive_json()
    assert response["success"], response
    return await _next_rooms(client)


async def _next_rooms(client: MockHAClientWebSocket) -> list[dict[str, Any]]:
    message = await client.receive_json()
    assert message["type"] == "event", message
    rooms: list[dict[str, Any]] = message["event"]["rooms"]
    return rooms


async def _latest_rooms(client: MockHAClientWebSocket) -> list[dict[str, Any]]:
    """Return the rooms of the last update sent so far."""
    await client.send_json_auto_id({"type": "ping"})
    latest = None
    while (message := await client.receive_json())["type"] != "pong":
        assert message["type"] == "event", message
        latest = message["event"]["rooms"]
    assert latest is not None, "no update"
    rooms: list[dict[str, Any]] = latest
    return rooms


async def _return_to_auto(
    client: MockHAClientWebSocket, room_id: str
) -> dict[str, Any]:
    await client.send_json_auto_id(
        {"type": "climate_control/room/return_to_auto", "room_id": room_id}
    )
    response: dict[str, Any] = await client.receive_json()
    return response


async def test_room_overview_lists_every_room_with_current_target_mode_and_reason(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Living room in its comfort block, bathroom without a block: both listed."""
    admin = await hass_ws_client(hass)
    await hass.config.async_update(language="de")
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    bath_schedule = await schedules.create("Bad", monday=[block("19:00", "21:00")])
    bath_trv = await simulated_trvs.add(
        "trv_bad", hvac_mode="heat", target_temperature=15.0, current_temperature=22.5
    )
    bath = await add_room(
        hass,
        room.entry,
        name="Bad",
        trvs=[bath_trv.entity_id],
        schedule=bath_schedule,
        area=ar.async_get(hass).async_create("Bad").id,
        comfort_temperature=23.0,
        eco_temperature=18.0,
    )

    rooms = await _subscribe(admin)

    assert rooms == [
        {
            "room_id": room.subentry.subentry_id,
            "name": "Wohnzimmer",
            "current_temperature": 19.5,
            "target_temperature": 21.0,
            "room_mode": "auto",
            "reason": "Komfort bis 09:00",
            "reason_code": "comfort",
        },
        {
            "room_id": bath.subentry_id,
            "name": "Bad",
            "current_temperature": 22.5,
            "target_temperature": 18.0,
            "room_mode": "auto",
            "reason": "Eco bis 19:00",
            "reason_code": "eco",
        },
    ]


async def test_room_overview_reports_an_override_without_reload(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Siri sets 23 °C: the panel learns of the override at once."""
    admin = await hass_ws_client(hass)
    await hass.config.async_update(language="de")
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await _subscribe(admin)

    await room.call(hass, "set_temperature", temperature=23)

    [living] = await _latest_rooms(admin)
    assert living["room_mode"] == "heat"
    assert living["target_temperature"] == 23.0
    assert living["reason"] == "Heizen bis 09:00 (manuell)"
    assert living["reason_code"] == "override"


async def test_room_overview_keeps_reporting_after_room_settings_change(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Changed settings reload the rooms; the subscription follows the new ones."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await _subscribe(admin)

    await change_room(hass, room.entry, room.subentry, comfort_temperature=22.0)

    [living] = await _latest_rooms(admin)
    assert living["target_temperature"] == 22.0


async def test_room_overview_is_refused_to_other_users(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A user without admin rights gets no room overview."""
    user = await hass_ws_client(hass, hass_read_only_access_token)
    clock.set("2026-11-16 08:00")
    await living_room(hass, schedules, simulated_trvs)

    await user.send_json_auto_id({"type": "climate_control/rooms/subscribe"})
    response = await user.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "unauthorized"