"""Panel API, schedule of a room: assign a schedule and follow the assignments."""

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from pytest_homeassistant.typing import MockHAClientWebSocket, WebSocketGenerator

from tests.scenario import (
    HEAT_16,
    HEAT_17,
    HEAT_21,
    Clock,
    LivingRoom,
    Schedules,
    add_main_entry,
    add_room,
    block,
    commands,
    living_room,
    reason_entity_id,
)
from tests.simulated_trv import SimulatedTrvs


async def _assign(
    client: MockHAClientWebSocket, room_id: str, **schedule: Any
) -> dict[str, Any]:
    await client.send_json_auto_id(
        {"type": "climate_control/room/assign_schedule", "room_id": room_id, **schedule}
    )
    response: dict[str, Any] = await client.receive_json()
    return response


async def _subscribe(client: MockHAClientWebSocket) -> dict[str, Any]:
    """Subscribe to the assignments; return what it starts with."""
    await client.send_json_auto_id({"type": "climate_control/schedules/subscribe"})
    response = await client.receive_json()
    assert response["success"], response
    message = await client.receive_json()
    assert message["type"] == "event", message
    event: dict[str, Any] = message["event"]
    return event


async def _latest(client: MockHAClientWebSocket) -> dict[str, Any]:
    """Return the last update of the assignments sent so far."""
    await client.send_json_auto_id({"type": "ping"})
    latest = None
    while (message := await client.receive_json())["type"] != "pong":
        if message["type"] == "event":
            latest = message["event"]
    assert latest is not None, "no update"
    event: dict[str, Any] = latest
    return event


def _schedule_of(room: LivingRoom) -> str | None:
    """Return the schedule the room is configured with now."""
    schedule: str | None = room.entry.subentries[room.subentry.subentry_id].data.get(
        "schedule"
    )
    return schedule


async def test_schedule_assigned_in_the_panel_applies_to_the_room(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room without schedule follows the schedule assigned in the panel."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    trv = await simulated_trvs.add("trv_wohnzimmer", target_temperature=15.0)
    entry = await add_main_entry(hass)
    subentry = await add_room(
        hass,
        entry,
        name="Wohnzimmer",
        trvs=[trv.entity_id],
        schedule=None,
        area=ar.async_get(hass).async_create("Wohnzimmer").id,
    )
    schedule = await schedules.create("Wohnzimmer", monday=[block("07:00", "09:00")])

    response = await _assign(admin, subentry.subentry_id, entity_id=schedule)
    await hass.async_block_till_done()

    assert response["success"], response
    assert commands(trv) == [HEAT_17, HEAT_21]
    reason = hass.states.get(reason_entity_id(hass, subentry))
    assert reason is not None
    assert reason.attributes["reason_code"] == "comfort"


async def test_schedule_created_in_the_panel_is_assigned_by_its_id(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The panel creates "Heizung Wohnzimmer" natively and assigns it by its id."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await admin.send_json_auto_id(
        {
            "type": "schedule/create",
            "name": "Heizung Wohnzimmer",
            "monday": [block("07:00", "09:00", "night")],
        }
    )
    created = await admin.receive_json()
    assert created["success"], created

    response = await _assign(
        admin, room.subentry.subentry_id, schedule_id=created["result"]["id"]
    )
    await hass.async_block_till_done()

    assert response["success"], response
    assert commands(room.trv) == [HEAT_21, HEAT_16]
    assert room.reason(hass).attributes["reason_code"] == "night"


async def test_assigning_an_unknown_schedule_fails_and_keeps_the_room(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A schedule deleted meanwhile is reported; the room keeps its schedule."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    by_id = await _assign(admin, room.subentry.subentry_id, schedule_id="gone")
    by_entity = await _assign(
        admin, room.subentry.subentry_id, entity_id="schedule.gone"
    )
    await hass.async_block_till_done()

    assert by_id["error"]["code"] == "schedule_not_found"
    assert by_entity["error"]["code"] == "schedule_not_found"
    assert _schedule_of(room) == room.schedule
    assert commands(room.trv) == [HEAT_21]


async def test_room_without_assigned_schedule_holds_eco(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Removing the schedule in the panel leaves the room at eco."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    response = await _assign(admin, room.subentry.subentry_id, entity_id=None)
    await hass.async_block_till_done()

    assert response["success"], response
    assert commands(room.trv) == [HEAT_21, HEAT_17]
    assert room.reason(hass).attributes["reason_code"] == "no_schedule"


async def test_panel_learns_which_schedule_applies_to_which_room(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Rooms with their schedule, and every schedule helper to choose from."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    garden = await schedules.create("Bewässerung", monday=[block("05:00", "05:30")])

    assignments = await _subscribe(admin)

    assert assignments == {
        "rooms": [
            {
                "room_id": room.subentry.subentry_id,
                "name": "Wohnzimmer",
                "entity_id": room.schedule,
            }
        ],
        "schedules": [
            {"entity_id": garden, "schedule_id": "bewasserung", "name": "Bewässerung"},
            {
                "entity_id": room.schedule,
                "schedule_id": "wohnzimmer",
                "name": "Wohnzimmer",
            },
        ],
    }


async def test_panel_learns_of_new_assignments_and_schedules(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A created schedule appears, an assignment follows, a deleted one goes."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await _subscribe(admin)

    copy = await schedules.create(
        "Heizung Wohnzimmer", monday=[block("06:00", "09:00")]
    )
    assert [helper["entity_id"] for helper in (await _latest(admin))["schedules"]] == [
        copy,
        room.schedule,
    ]

    await _assign(admin, room.subentry.subentry_id, entity_id=copy)
    await hass.async_block_till_done()
    [living] = (await _latest(admin))["rooms"]
    assert living["entity_id"] == copy

    await schedules.delete(room.schedule)
    assert [helper["entity_id"] for helper in (await _latest(admin))["schedules"]] == [
        copy
    ]


async def test_assignments_are_refused_to_other_users(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A user without admin rights does not learn of the schedules of the rooms."""
    user = await hass_ws_client(hass, hass_read_only_access_token)
    clock.set("2026-11-16 08:00")
    await living_room(hass, schedules, simulated_trvs)

    await user.send_json_auto_id({"type": "climate_control/schedules/subscribe"})
    response = await user.receive_json()

    assert response["error"]["code"] == "unauthorized"


async def test_assigning_a_schedule_to_an_unknown_room_fails(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room removed meanwhile is reported as not found."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    response = await _assign(admin, "no-such-room", entity_id=room.schedule)

    assert response["error"]["code"] == "room_not_found"


async def test_assigning_a_schedule_is_refused_to_other_users(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A user without admin rights cannot change the schedule of a room."""
    user = await hass_ws_client(hass, hass_read_only_access_token)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    response = await _assign(user, room.subentry.subentry_id, entity_id=None)

    assert response["error"]["code"] == "unauthorized"
    assert _schedule_of(room) == room.schedule
