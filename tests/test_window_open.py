"""Window open: a window contact open for the window delay sends the room to frost."""

from homeassistant.core import HomeAssistant

from tests.scenario import (
    HEAT_21,
    Clock,
    Schedules,
    WindowContact,
    commands,
    living_room,
)
from tests.simulated_trv import SimulatedTrvs

FROST = ("set_hvac_mode", {"hvac_mode": "off"})


async def test_window_opened_for_the_window_delay_sends_the_trv_to_frost_protection(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Airing at 08:00 during comfort switches the TRV off at 08:01."""
    clock.set("2026-11-16 08:00")
    window = WindowContact(hass, "fenster_wohnzimmer")
    room = await living_room(
        hass, schedules, simulated_trvs, window_contacts=[window.entity_id]
    )

    await window.open()
    await clock.advance_to("2026-11-16 08:00:59")
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 08:01:00")

    assert commands(room.trv) == [HEAT_21, FROST]
    assert room.state(hass).attributes["temperature"] == 7.0
    assert room.state(hass).attributes["level"] == "frost"
    assert room.reason(hass).attributes["reason_code"] == "window_open"


async def test_window_closed_within_the_window_delay_changes_nothing(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Opening the window for 50 s keeps comfort, also after the delay is up."""
    clock.set("2026-11-16 08:00")
    window = WindowContact(hass, "fenster_wohnzimmer")
    room = await living_room(
        hass, schedules, simulated_trvs, window_contacts=[window.entity_id]
    )

    await window.open()
    await clock.advance_to("2026-11-16 08:00:50")
    await window.close()
    await clock.advance_to("2026-11-16 08:05:00")

    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.reason(hass).attributes["reason_code"] == "comfort"
    assert commands(room.trv) == [HEAT_21]


async def test_closing_the_window_restores_the_schedule_level_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Closing the window at 08:10 heats to comfort again without delay."""
    clock.set("2026-11-16 08:00")
    window = WindowContact(hass, "fenster_wohnzimmer")
    room = await living_room(
        hass, schedules, simulated_trvs, window_contacts=[window.entity_id]
    )
    await window.open()
    await clock.advance_to("2026-11-16 08:10:00")

    await window.close()

    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.reason(hass).attributes["reason_code"] == "comfort"
    assert commands(room.trv) == [HEAT_21, FROST, HEAT_21]
