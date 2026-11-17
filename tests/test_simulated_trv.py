"""Self-test of the simulated TRV test helper (behaviour measured in ticket 01)."""

from homeassistant.core import HomeAssistant

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
