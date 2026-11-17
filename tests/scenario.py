"""Building blocks for scenario tests: local clock, schedules, main entry, rooms."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigEntry,
    ConfigSubentry,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import area_registry as ar, entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant.common import async_fire_time_changed
from pytest_homeassistant.typing import MockHAClientWebSocket

from tests.simulated_trv import SimulatedTrv, SimulatedTrvs

DOMAIN = "climate_control"
TIME_ZONE = "Europe/Berlin"


def local(local_time: str) -> datetime:
    """Return a moment in local time (Europe/Berlin), e.g. `2026-11-16 08:00`."""
    return datetime.fromisoformat(local_time).replace(tzinfo=ZoneInfo(TIME_ZONE))


class Clock:
    """Wall clock of the test Home Assistant in local time (Europe/Berlin)."""

    def __init__(self, hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
        """Wrap the frozen time of the test."""
        self._hass = hass
        self._freezer = freezer

    def set(self, local_time: str) -> None:
        """Set the time without firing timers, e.g. `2026-11-16 08:00`."""
        self._freezer.move_to(local(local_time))

    async def advance_to(self, local_time: str) -> None:
        """Move the time forward and run everything that became due."""
        self.set(local_time)
        async_fire_time_changed(self._hass)
        await self._hass.async_block_till_done()


def block(start: str, end: str, level: str | None = None) -> dict[str, Any]:
    """Return a schedule block from `start` to `end` (HH:MM) with an optional level."""
    result: dict[str, Any] = {"from": f"{start}:00", "to": f"{end}:00"}
    if level is not None:
        result["data"] = {"level": level}
    return result


def duration(minutes: int) -> dict[str, int]:
    """Return a duration as the duration fields of a dialog take it."""
    return {"hours": minutes // 60, "minutes": minutes % 60, "seconds": 0}


class Schedules:
    """Native schedule helpers, created and edited like the frontend does."""

    def __init__(self, hass: HomeAssistant, client: MockHAClientWebSocket) -> None:
        """Use an admin websocket connection."""
        self._hass = hass
        self._client = client
        self._ids: dict[str, str] = {}

    async def create(self, name: str, **weekdays: list[dict[str, Any]]) -> str:
        """Create a schedule and return its entity id."""
        item = await self._send({"type": "schedule/create", "name": name, **weekdays})
        entity_id = er.async_get(self._hass).async_get_entity_id(
            "schedule", "schedule", item["id"]
        )
        assert entity_id is not None
        self._ids[entity_id] = item["id"]
        return entity_id

    async def update(
        self, entity_id: str, name: str, **weekdays: list[dict[str, Any]]
    ) -> None:
        """Replace all blocks of a schedule; weekdays left out become empty."""
        await self._send(
            {
                "type": "schedule/update",
                "schedule_id": self._ids[entity_id],
                "name": name,
                **weekdays,
            }
        )

    async def _send(self, message: dict[str, Any]) -> dict[str, Any]:
        await self._client.send_json_auto_id(message)
        response = await self._client.receive_json()
        assert response["success"], response
        await self._hass.async_block_till_done()
        result: dict[str, Any] = response["result"]
        return result


async def add_main_entry(hass: HomeAssistant, **settings: Any) -> ConfigEntry:
    """Set up the main entry; global settings left out keep their defaults."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], settings)
    await hass.async_block_till_done()
    entry: ConfigEntry = result["result"]
    return entry


async def shut_down(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Stop the integration as Home Assistant does when it shuts down."""
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def start_up(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Start the integration as Home Assistant does when it starts."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def room_settings(subentry: ConfigSubentry) -> dict[str, Any]:
    """Return the values of the room dialog as currently configured."""
    optional = ("override_expiry_policy", "override_expiry_duration")
    return {
        "name": subentry.title,
        "trvs": subentry.data["trvs"][0],
        "schedule": subentry.data["schedule"],
        "comfort_temperature": subentry.data["comfort_temperature"],
        "night_temperature": subentry.data["night_temperature"],
        "eco_temperature": subentry.data["eco_temperature"],
        "lead_time": subentry.data["lead_time"],
        "area": subentry.data["area"],
        **{key: subentry.data[key] for key in optional if key in subentry.data},
    }


async def add_room(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    name: str,
    trv: str,
    schedule: str,
    area: str,
    comfort_temperature: float = 21.0,
    night_temperature: float = 16.0,
    eco_temperature: float = 17.0,
    lead_minutes: int = 0,
) -> ConfigSubentry:
    """Add a room through the room dialog of the main entry."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": name,
            "trvs": trv,
            "schedule": schedule,
            "comfort_temperature": comfort_temperature,
            "night_temperature": night_temperature,
            "eco_temperature": eco_temperature,
            "lead_time": duration(lead_minutes),
            "area": area,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    return next(
        subentry for subentry in entry.subentries.values() if subentry.title == name
    )


def room_entity_id(hass: HomeAssistant, subentry: ConfigSubentry) -> str:
    """Return the entity id of the room entity of a room."""
    return next(
        entry.entity_id
        for entry in er.async_get(hass).entities.values()
        if entry.config_subentry_id == subentry.subentry_id
        and entry.domain == "climate"
    )


@dataclass
class LivingRoom:
    """The living room: one TRV and its schedule."""

    entry: ConfigEntry
    subentry: ConfigSubentry
    trv: SimulatedTrv
    schedule: str

    def entity_id(self, hass: HomeAssistant) -> str:
        """Return the entity id of the room entity."""
        return room_entity_id(hass, self.subentry)

    def state(self, hass: HomeAssistant) -> State:
        """Return the state of the room entity."""
        state = hass.states.get(self.entity_id(hass))
        assert state is not None
        return state

    async def call(self, hass: HomeAssistant, service: str, **data: Any) -> None:
        """Call a `climate` action on the room entity, e.g. from Siri or the app."""
        await hass.services.async_call(
            "climate",
            service,
            {"entity_id": self.entity_id(hass), **data},
            blocking=True,
        )
        await hass.async_block_till_done()


async def living_room(
    hass: HomeAssistant,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    *,
    trv_mode: str = "heat",
    trv_temperature: float = 15.0,
    current_temperature: float = 19.5,
    lead_minutes: int = 0,
    global_settings: dict[str, Any] | None = None,
    **weekdays: list[dict[str, Any]],
) -> LivingRoom:
    """Add the living room with comfort 21 °C, night 16 °C and eco 17 °C.

    Its schedule has the blocks given per weekday, by default one comfort block
    Monday 07:00-09:00.
    """
    schedule = await schedules.create(
        "Wohnzimmer", **(weekdays or {"monday": [block("07:00", "09:00")]})
    )
    trv = await simulated_trvs.add(
        "trv_wohnzimmer",
        hvac_mode=trv_mode,
        target_temperature=trv_temperature,
        current_temperature=current_temperature,
    )
    area = ar.async_get(hass).async_create("Wohnzimmer")
    entry = await add_main_entry(hass, **(global_settings or {}))
    subentry = await add_room(
        hass,
        entry,
        name="Wohnzimmer",
        trv=trv.entity_id,
        schedule=schedule,
        area=area.id,
        comfort_temperature=21.0,
        night_temperature=16.0,
        eco_temperature=17.0,
        lead_minutes=lead_minutes,
    )
    return LivingRoom(entry, subentry, trv, schedule)


def commands(trv: SimulatedTrv) -> list[tuple[str, dict[str, Any]]]:
    """Return the `climate` actions a TRV received as (service, data)."""
    return [(call.service, call.data) for call in trv.calls]


HEAT_21 = ("set_temperature", {"temperature": 21.0, "hvac_mode": "heat"})
HEAT_17 = ("set_temperature", {"temperature": 17.0, "hvac_mode": "heat"})
HEAT_16 = ("set_temperature", {"temperature": 16.0, "hvac_mode": "heat"})


async def change_room(
    hass: HomeAssistant,
    entry: ConfigEntry,
    subentry: ConfigSubentry,
    **changes: Any,
) -> None:
    """Change settings of a room in its options dialog."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**room_settings(subentry), **changes}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"


async def change_global_settings(
    hass: HomeAssistant, entry: ConfigEntry, **changes: Any
) -> None:
    """Change global settings in the options dialog of the main entry."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**entry.options, **changes}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


class Persons:
    """Native person entities, each following the device tracker of a phone."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Use the test Home Assistant."""
        self._hass = hass

    async def add(self, **presences: str) -> list[str]:
        """Add persons with their presence, e.g. `anna="home"`; return entity ids."""
        for name, presence in presences.items():
            self._report(name, presence)
        assert await async_setup_component(
            self._hass,
            "person",
            {
                "person": [
                    {
                        "id": name,
                        "name": name.title(),
                        "device_trackers": [f"device_tracker.{name}_phone"],
                    }
                    for name in presences
                ]
            },
        )
        await self._hass.async_block_till_done()
        return [f"person.{name}" for name in presences]

    async def move(self, name: str, presence: str) -> None:
        """Let the phone of a person report a presence, e.g. `not_home`."""
        self._report(name, presence)
        await self._hass.async_block_till_done()

    def _report(self, name: str, presence: str) -> None:
        self._hass.states.async_set(
            f"device_tracker.{name}_phone", presence, {"source_type": "router"}
        )


def away_state(hass: HomeAssistant, entry: ConfigEntry) -> State:
    """Return the state of the global away entity."""
    entity_id = er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, f"{entry.entry_id}_away"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state
