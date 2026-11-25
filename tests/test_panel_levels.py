"""Panel API: level temperatures and lead time of a room, global temperatures."""

from typing import Any

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant.typing import MockHAClientWebSocket, WebSocketGenerator

from tests.scenario import (
    HEAT_21,
    Clock,
    Schedules,
    block,
    commands,
    duration,
    living_room,
    room_settings,
)
from tests.simulated_trv import SimulatedTrvs

HEAT_22 = ("set_temperature", {"temperature": 22.0, "hvac_mode": "heat"})


async def _send(client: MockHAClientWebSocket, **message: Any) -> dict[str, Any]:
    await client.send_json_auto_id(message)
    response: dict[str, Any] = await client.receive_json()
    return response


async def _set_levels(
    hass: HomeAssistant, client: MockHAClientWebSocket, room_id: str, **levels: Any
) -> dict[str, Any]:
    """Change levels of a room from the panel; wait until the room applied them."""
    response = await _send(
        client, type="climate_control/room/set_levels", room_id=room_id, **levels
    )
    await hass.async_block_till_done()
    return response


async def test_room_levels_show_level_temperatures_and_lead_time(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The living room has comfort 21 °C, night 16 °C, eco 17 °C, 45 min lead time."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs, lead_minutes=45)

    response = await _send(
        admin, type="climate_control/room/levels", room_id=room.subentry.subentry_id
    )

    assert response["success"], response
    assert response["result"] == {
        "comfort_temperature": 21.0,
        "night_temperature": 16.0,
        "eco_temperature": 17.0,
        "lead_time_minutes": 45,
    }


async def test_new_comfort_temperature_from_the_panel_applies_at_once(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Comfort 22 °C during the comfort block reaches the TRV and the room options."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    response = await _set_levels(
        hass, admin, room.subentry.subentry_id, comfort_temperature=22.0
    )

    assert response["success"], response
    assert room.state(hass).attributes["temperature"] == 22.0
    assert commands(room.trv) == [HEAT_21, HEAT_22]
    assert room_settings(room.entry.subentries[room.subentry.subentry_id]) == {
        **room_settings(room.subentry),
        "comfort_temperature": 22.0,
    }


async def test_lead_time_from_the_panel_preheats_at_once(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """At 06:15 night 18 °C and 60 min lead time preheat for night at 07:00."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 06:15")
    room = await living_room(
        hass, schedules, simulated_trvs, monday=[block("07:00", "09:00", "night")]
    )

    await _set_levels(
        hass,
        admin,
        room.subentry.subentry_id,
        night_temperature=18.0,
        lead_time_minutes=60,
    )

    assert room.entry.subentries[room.subentry.subentry_id].data[
        "lead_time"
    ] == duration(60)
    assert room.state(hass).attributes["temperature"] == 18.0
    assert room.reason(hass).attributes["reason_code"] == "preheat"


@pytest.mark.parametrize(
    "levels",
    [
        {"comfort_temperature": 26.0},
        {"eco_temperature": 4.0},
        {"lead_time_minutes": 195},
        {"lead_time_minutes": -15},
        {"lead_time_minutes": 20},
    ],
)
async def test_levels_outside_the_panel_limits_are_refused(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    levels: dict[str, float],
) -> None:
    """Temperatures stay within 5-25 °C, the lead time in 15 min steps up to 3 h."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    before = room_settings(room.subentry)

    response = await _set_levels(hass, admin, room.subentry.subentry_id, **levels)

    assert response["error"]["code"] == "invalid_format"
    assert room_settings(room.entry.subentries[room.subentry.subentry_id]) == before


async def test_night_warmer_than_comfort_is_saved_and_other_levels_kept(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The panel only hints at night above comfort; eco 17.5 °C stays as it is."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await _set_levels(hass, admin, room.subentry.subentry_id, eco_temperature=17.5)

    response = await _set_levels(
        hass, admin, room.subentry.subentry_id, night_temperature=22.0
    )

    assert response["success"], response
    levels = await _send(
        admin, type="climate_control/room/levels", room_id=room.subentry.subentry_id
    )
    assert levels["result"] == {
        "comfort_temperature": 21.0,
        "night_temperature": 22.0,
        "eco_temperature": 17.5,
        "lead_time_minutes": 0,
    }


async def test_room_overview_reports_levels_changed_in_the_panel(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """New levels reload the rooms; the room overview follows with the new target."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await admin.send_json_auto_id({"type": "climate_control/rooms/subscribe"})
    assert (await admin.receive_json())["success"]
    await admin.receive_json()

    await admin.send_json_auto_id(
        {
            "type": "climate_control/room/set_levels",
            "room_id": room.subentry.subentry_id,
            "comfort_temperature": 23.0,
        }
    )
    await hass.async_block_till_done()

    targets: list[float] = []
    while (message := await admin.receive_json())["type"] != "result":
        targets.append(message["event"]["rooms"][0]["target_temperature"])
    assert message["success"], message
    await admin.send_json_auto_id({"type": "ping"})
    while (message := await admin.receive_json())["type"] != "pong":
        targets.append(message["event"]["rooms"][0]["target_temperature"])
    assert targets[-1] == 23.0


async def test_levels_of_an_unknown_room_are_not_found(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room removed meanwhile is reported as not found."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    await living_room(hass, schedules, simulated_trvs)

    shown = await _send(admin, type="climate_control/room/levels", room_id="gone")
    changed = await _set_levels(hass, admin, "gone", comfort_temperature=22.0)

    assert shown["error"]["code"] == "room_not_found"
    assert changed["error"]["code"] == "room_not_found"


async def test_levels_are_refused_to_other_users(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A user without admin rights neither sees nor changes the levels."""
    user = await hass_ws_client(hass, hass_read_only_access_token)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    room_id = room.subentry.subentry_id

    shown = await _send(user, type="climate_control/room/levels", room_id=room_id)
    changed = await _set_levels(hass, user, room_id, comfort_temperature=25.0)

    assert shown["error"]["code"] == "unauthorized"
    assert changed["error"]["code"] == "unauthorized"
    assert room.state(hass).attributes["temperature"] == 21.0


async def test_new_frost_temperature_from_the_panel_applies_at_once(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room switched off holds frost protection, now 8 °C instead of 7 °C."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    shown = await _send(admin, type="climate_control/house/temperatures")
    response = await _send(
        admin, type="climate_control/house/set_temperatures", frost_temperature=8.0
    )
    await hass.async_block_till_done()

    assert shown["result"] == {
        "away_temperature": 17.0,
        "vacation_temperature": 15.0,
        "frost_temperature": 7.0,
    }
    assert response["success"], response
    assert room.entry.options["frost_temperature"] == 8.0
    assert room.entry.options["away_temperature"] == 17.0
    assert room.state(hass).attributes["temperature"] == 8.0


async def test_global_temperatures_outside_the_trv_range_are_refused(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Vacation 4 °C is below what the TRVs can do."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    response = await _send(
        admin, type="climate_control/house/set_temperatures", vacation_temperature=4.0
    )

    assert response["error"]["code"] == "invalid_format"
    assert room.entry.options["vacation_temperature"] == 15.0


async def test_global_temperatures_are_refused_to_other_users(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A user without admin rights neither sees nor changes them."""
    user = await hass_ws_client(hass, hass_read_only_access_token)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    shown = await _send(user, type="climate_control/house/temperatures")
    changed = await _send(
        user, type="climate_control/house/set_temperatures", away_temperature=20.0
    )

    assert shown["error"]["code"] == "unauthorized"
    assert changed["error"]["code"] == "unauthorized"
    assert room.entry.options["away_temperature"] == 17.0
