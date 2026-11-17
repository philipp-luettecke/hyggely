"""Self-test of the simulated TRV test helper against the measured tado behaviour."""

from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from tests.scenario import Clock
from tests.simulated_trv import SimulatedTrvs, TrvCall


async def test_command_is_applied_immediately_and_recorded(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs
) -> None:
    """A climate command shows up in the TRV state at once, like real tado."""
    trv = await simulated_trvs.add("office", hvac_mode="off")

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": trv.entity_id, "temperature": 21, "hvac_mode": "heat"},
        blocking=True,
    )

    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.state == "heat"
    assert state.attributes["temperature"] == 21
    assert [(call.service, call.data) for call in trv.calls] == [
        ("set_temperature", {"temperature": 21, "hvac_mode": "heat"})
    ]


async def test_off_trv_reports_like_tado(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs
) -> None:
    """An off TRV has no target temperature and reports the 7-35 range."""
    trv = await simulated_trvs.add("office", hvac_mode="off")

    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.state == "off"
    assert state.attributes["temperature"] is None
    assert state.attributes["min_temp"] == 7
    assert state.attributes["max_temp"] == 35
    assert state.attributes["hvac_modes"] == ["off", "heat"]


async def test_reported_change_arrives_with_a_fresh_context(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs
) -> None:
    """A value reported by the TRV itself carries no user and no parent."""
    trv = await simulated_trvs.add("office", target_temperature=20)

    trv.report(target_temperature=23, current_temperature=19.5)

    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.attributes["temperature"] == 23
    assert state.attributes["current_temperature"] == 19.5
    assert state.context.user_id is None
    assert state.context.parent_id is None
    assert trv.calls == []


def _trv_changes(hass: HomeAssistant, entity_id: str) -> list[State]:
    """Start recording the states a TRV changes to."""
    changes: list[State] = []

    @callback
    def record(event: Event[EventStateChangedData]) -> None:
        if (new_state := event.data["new_state"]) is not None:
            changes.append(new_state)

    async_track_state_change_event(hass, entity_id, record)
    return changes


async def test_knob_turns_arrive_at_the_next_poll_with_only_the_end_value(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs, clock: Clock
) -> None:
    """Four quick turns give one change at the full minute."""
    clock.set("2026-11-16 12:42:10")
    trv = await simulated_trvs.add("office", target_temperature=23.0)
    changes = _trv_changes(hass, trv.entity_id)

    for temperature in (22.0, 21.0, 20.0, 19.0):
        trv.turn_knob(temperature)
    await clock.advance_to("2026-11-16 12:42:59")
    assert changes == []

    await clock.advance_to("2026-11-16 12:43:00")

    [state] = changes
    assert state.state == "heat"
    assert state.attributes["temperature"] == 19.0
    assert state.context.user_id is None
    assert state.context.parent_id is None


async def test_switching_off_at_the_device_arrives_at_the_next_poll(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs, clock: Clock
) -> None:
    """Switched off at the TRV, it reports off without a target at the full minute."""
    clock.set("2026-11-16 12:00:20")
    trv = await simulated_trvs.add("office", target_temperature=21.0)

    trv.switch_off()
    assert _state(hass, trv.entity_id) == "heat"
    await clock.advance_to("2026-11-16 12:01:00")

    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.state == "off"
    assert state.attributes["temperature"] is None


async def test_command_not_taken_shows_at_once_and_reverts_at_the_next_poll(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs, clock: Clock
) -> None:
    """Home Assistant shows a command at once; the poll brings the old values back."""
    clock.set("2026-11-16 12:00:30")
    trv = await simulated_trvs.add("office", target_temperature=17.0)
    trv.commands_to_lose = 1

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": trv.entity_id, "temperature": 23, "hvac_mode": "heat"},
        blocking=True,
    )
    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.attributes["temperature"] == 23

    await clock.advance_to("2026-11-16 12:01:00")
    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.attributes["temperature"] == 17


async def test_off_trv_ignores_a_temperature_without_mode(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs, clock: Clock
) -> None:
    """The call is accepted, the TRV stays off."""
    clock.set("2026-11-16 12:00:30")
    trv = await simulated_trvs.add("office", hvac_mode="off")

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": trv.entity_id, "temperature": 21},
        blocking=True,
    )
    await clock.advance_to("2026-11-16 12:01:00")

    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.state == "off"
    assert state.attributes["temperature"] is None

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": trv.entity_id, "hvac_mode": "heat"},
        blocking=True,
    )
    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.attributes["temperature"] == 20.0


async def test_trv_that_ignores_commands_still_records_them(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs
) -> None:
    """With applying switched off, a command is recorded but changes nothing."""
    trv = await simulated_trvs.add("office", target_temperature=20)
    trv.apply_commands = False

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": trv.entity_id, "hvac_mode": "off"},
        blocking=True,
    )

    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.state == "heat"
    assert state.attributes["temperature"] == 20
    assert trv.calls == [
        TrvCall("set_hvac_mode", {"hvac_mode": "off"}, trv.calls[0].context)
    ]


async def test_temperature_sensor_sits_on_the_device_of_the_trv(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs
) -> None:
    """Like HomeKit Device, the TRV device also carries a temperature sensor."""
    trv = await simulated_trvs.add("office", current_temperature=19.5)

    registry = er.async_get(hass)
    climate = registry.async_get(trv.entity_id)
    sensor = registry.async_get(trv.temperature_sensor_id)
    assert climate is not None
    assert sensor is not None
    assert sensor.device_id == climate.device_id
    state = hass.states.get(trv.temperature_sensor_id)
    assert state is not None
    assert state.state == "19.5"
    assert state.attributes["device_class"] == "temperature"


async def test_trv_can_come_without_temperature_sensor(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs
) -> None:
    """A TRV added without sensor has only its climate entity on the device."""
    trv = await simulated_trvs.add("office", temperature_sensor=False)

    registry = er.async_get(hass)
    climate = registry.async_get(trv.entity_id)
    assert climate is not None
    assert climate.device_id is not None
    entities = er.async_entries_for_device(registry, climate.device_id)
    assert [entity.entity_id for entity in entities] == [trv.entity_id]


def _state(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


async def test_bridge_outage_follows_the_measurement(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs, clock: Clock
) -> None:
    """The climate entity freezes, the sensor goes away.

    Unplugged 13:52:25, sensor unavailable at the second poll (13:54), plugged in
    13:53:32, sensor back with an invalid mode at the second poll (13:55), fresh
    climate values at the fourth poll (13:57).
    """
    clock.set("2026-11-16 13:50:00")
    trv = await simulated_trvs.add("office", target_temperature=22.0)
    sensor = trv.temperature_sensor_id

    clock.set("2026-11-16 13:52:25")
    trv.unplug_bridge()
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": trv.entity_id, "temperature": 18, "hvac_mode": "heat"},
        blocking=True,
    )
    await clock.advance_to("2026-11-16 13:53:00")
    assert _state(hass, trv.entity_id) == "heat"
    assert _state(hass, sensor) != "unavailable"

    clock.set("2026-11-16 13:53:32")
    trv.plug_in_bridge()
    await clock.advance_to("2026-11-16 13:54:00")
    assert _state(hass, trv.entity_id) == "heat"
    assert _state(hass, sensor) == "unavailable"

    await clock.advance_to("2026-11-16 13:55:00")
    assert _state(hass, trv.entity_id) == "unknown"
    assert _state(hass, sensor) == "20.0"

    await clock.advance_to("2026-11-16 13:56:00")
    assert _state(hass, trv.entity_id) == "unknown"

    await clock.advance_to("2026-11-16 13:57:00")
    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.state == "heat"
    assert state.attributes["temperature"] == 22.0


async def test_trv_applies_commands_again_after_the_bridge_returned(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs, clock: Clock
) -> None:
    """Once fresh values arrive the TRV takes commands again."""
    clock.set("2026-11-16 12:00:30")
    trv = await simulated_trvs.add("office", target_temperature=20.0)
    trv.unplug_bridge()
    trv.plug_in_bridge()
    await clock.advance_to("2026-11-16 12:04:00")

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": trv.entity_id, "temperature": 23, "hvac_mode": "heat"},
        blocking=True,
    )

    state = hass.states.get(trv.entity_id)
    assert state is not None
    assert state.attributes["temperature"] == 23


async def test_trv_reports_an_invalid_mode(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs
) -> None:
    """A mode None from the bridge shows as state unknown until the next report."""
    trv = await simulated_trvs.add("office", target_temperature=20.0)

    trv.report_invalid_mode()
    assert _state(hass, trv.entity_id) == "unknown"

    trv.report()
    assert _state(hass, trv.entity_id) == "heat"


async def test_climate_entity_can_become_unavailable(
    hass: HomeAssistant, simulated_trvs: SimulatedTrvs
) -> None:
    """The climate entity itself can become unavailable and come back."""
    trv = await simulated_trvs.add("office", temperature_sensor=False)

    trv.set_available(False)
    assert _state(hass, trv.entity_id) == "unavailable"

    trv.set_available(True)
    assert _state(hass, trv.entity_id) == "heat"
