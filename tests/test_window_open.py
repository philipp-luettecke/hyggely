"""Window open: a window contact open for the window delay sends the room to frost."""

from homeassistant.core import HomeAssistant
import pytest

from tests.scenario import (
    HEAT_17,
    HEAT_21,
    Clock,
    LivingRoom,
    Schedules,
    WindowContact,
    change_global_settings,
    change_room,
    commands,
    duration,
    living_room,
    local,
)
from tests.simulated_trv import SimulatedTrvs

FROST = ("set_hvac_mode", {"hvac_mode": "off"})
HEAT_23 = ("set_temperature", {"temperature": 23.0, "hvac_mode": "heat"})


async def _living_room_with_window(
    hass: HomeAssistant, schedules: Schedules, simulated_trvs: SimulatedTrvs
) -> tuple[LivingRoom, WindowContact]:
    """Add the living room with one window contact, closed."""
    window = WindowContact(hass, "fenster_wohnzimmer")
    room = await living_room(
        hass, schedules, simulated_trvs, window_contacts=[window.entity_id]
    )
    return room, window


async def test_window_opened_for_the_window_delay_sends_the_trv_to_frost_protection(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Airing at 08:00 during comfort switches the TRV off at 08:01."""
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)

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
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)

    await window.open()
    await clock.advance_to("2026-11-16 08:00:50")
    await window.close()
    await clock.advance_to("2026-11-16 08:05:00")

    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.reason(hass).attributes["reason_code"] == "comfort"
    assert commands(room.trv) == [HEAT_21]


async def test_window_delay_follows_the_global_settings(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """With a window delay of 2 min the TRV switches off at 08:02, not at 08:01."""
    clock.set("2026-11-16 08:00")
    window = WindowContact(hass, "fenster_wohnzimmer")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        window_contacts=[window.entity_id],
        global_settings={"window_delay": duration(2)},
    )

    await window.open()
    await clock.advance_to("2026-11-16 08:01:59")
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 08:02:00")
    assert commands(room.trv) == [HEAT_21, FROST]


async def test_closing_the_window_restores_the_schedule_level_at_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Closing the window at 08:10 heats to comfort again without delay."""
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await window.open()
    await clock.advance_to("2026-11-16 08:10:00")

    await window.close()

    assert room.state(hass).attributes["temperature"] == 21.0
    assert room.reason(hass).attributes["reason_code"] == "comfort"
    assert commands(room.trv) == [HEAT_21, FROST, HEAT_21]


async def test_window_open_during_an_override_restores_the_override_after_closing(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Airing beats the override at 23 °C; closing brings it back with its expiry."""
    clock.set("2026-11-16 12:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)

    await clock.advance_to("2026-11-16 12:10:00")
    await window.open()
    await clock.advance_to("2026-11-16 12:11:00")
    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 7.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:00")
    assert room.reason(hass).attributes["reason_code"] == "window_open"

    await clock.advance_to("2026-11-16 12:30:00")
    await window.close()

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 23.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 15:00")
    assert room.reason(hass).attributes["reason_code"] == "override"
    assert commands(room.trv) == [HEAT_17, HEAT_23, FROST, HEAT_23]


async def test_override_expiring_while_the_window_is_open_leaves_the_schedule_level(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The override ends at 15:00 with the window open; closing gives eco."""
    clock.set("2026-11-16 12:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await room.call(hass, "set_temperature", temperature=23)
    await clock.advance_to("2026-11-16 14:00:00")
    await window.open()
    await clock.advance_to("2026-11-16 14:01:00")

    await clock.advance_to("2026-11-16 15:00:00")
    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["override_expiry"] is None
    assert room.reason(hass).attributes["reason_code"] == "window_open"

    await clock.advance_to("2026-11-16 15:30:00")
    await window.close()

    assert room.state(hass).state == "auto"
    assert room.state(hass).attributes["temperature"] == 17.0
    assert commands(room.trv) == [HEAT_17, HEAT_23, FROST, HEAT_17]


async def test_window_open_beats_a_room_switched_off(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """An off room explains the open window; closed again it stays off until 09:00."""
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await room.call(hass, "set_hvac_mode", hvac_mode="off")

    await window.open()
    await clock.advance_to("2026-11-16 08:01:00")
    assert room.reason(hass).attributes["reason_code"] == "window_open"

    await window.close()
    assert room.state(hass).state == "off"
    assert room.reason(hass).attributes["reason_code"] == "room_off"
    assert commands(room.trv) == [HEAT_21, FROST]

    await clock.advance_to("2026-11-16 09:00:00")
    assert room.state(hass).state == "auto"
    assert commands(room.trv) == [HEAT_21, FROST, HEAT_17]


async def test_any_open_window_contact_of_the_room_counts(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Window and balcony door: frost while either is open long enough."""
    clock.set("2026-11-16 08:00")
    window = WindowContact(hass, "fenster_wohnzimmer")
    door = WindowContact(hass, "balkontuer_wohnzimmer")
    room = await living_room(
        hass,
        schedules,
        simulated_trvs,
        window_contacts=[window.entity_id, door.entity_id],
    )

    await window.open()
    await clock.advance_to("2026-11-16 08:00:30")
    await door.open()
    await clock.advance_to("2026-11-16 08:00:50")
    await window.close()
    await clock.advance_to("2026-11-16 08:01:00")
    assert commands(room.trv) == [HEAT_21]

    await clock.advance_to("2026-11-16 08:01:30")
    assert commands(room.trv) == [HEAT_21, FROST]
    assert room.reason(hass).attributes["since"] == local("2026-11-16 08:00:30")

    await clock.advance_to("2026-11-16 08:05:00")
    await window.open()
    await clock.advance_to("2026-11-16 08:06:30")
    await door.close()
    assert commands(room.trv) == [HEAT_21, FROST]

    await window.close()
    assert commands(room.trv) == [HEAT_21, FROST, HEAT_21]


@pytest.mark.parametrize("contact_state", ["unavailable", "unknown"])
async def test_unreachable_window_contact_counts_as_closed(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    contact_state: str,
) -> None:
    """A contact losing its battery while open lets the room heat again at once."""
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await window.open()
    await clock.advance_to("2026-11-16 08:01:00")

    await window.report(contact_state)

    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21, FROST, HEAT_21]
    await clock.advance_to("2026-11-16 08:30:00")
    assert commands(room.trv) == [HEAT_21, FROST, HEAT_21]


async def test_reason_counts_the_minutes_the_window_is_open(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The reason reads window open for 1 min, then counts up every minute."""
    await hass.config.async_update(language="de")
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await window.open()

    await clock.advance_to("2026-11-16 08:01:00")
    assert room.reason(hass).state == "Fenster offen seit 1 min"
    assert room.reason(hass).attributes["since"] == local("2026-11-16 08:00")

    await clock.advance_to("2026-11-16 08:02:00")
    assert room.reason(hass).state == "Fenster offen seit 2 min"

    await clock.advance_to("2026-11-16 08:04:30")
    assert room.reason(hass).state == "Fenster offen seit 4 min"


async def test_new_temperature_while_the_window_is_open_is_heated_after_closing(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Siri sets 23 °C while airing: the TRV stays off, closing heats to 23 °C."""
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await window.open()
    await clock.advance_to("2026-11-16 08:05:00")

    await room.call(hass, "set_temperature", temperature=23)
    assert room.state(hass).state == "heat"
    assert room.reason(hass).attributes["reason_code"] == "window_open"
    assert commands(room.trv) == [HEAT_21, FROST]

    await window.close()

    assert room.state(hass).attributes["temperature"] == 23.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 09:00")
    assert commands(room.trv) == [HEAT_21, FROST, HEAT_23]


async def test_knob_turn_while_the_window_is_open_is_heated_after_closing(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Turned to 23 °C while airing: back to frost at once, 23 °C after closing."""
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await window.open()
    await clock.advance_to("2026-11-16 08:05:20")

    room.trv.turn_knob(23.0)
    await clock.advance_to("2026-11-16 08:06:00")

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 7.0
    assert room.reason(hass).attributes["reason_code"] == "window_open"
    assert commands(room.trv) == [HEAT_21, FROST, FROST]
    trv_state = hass.states.get(room.trv.entity_id)
    assert trv_state is not None
    assert trv_state.state == "off"

    await window.close()

    assert room.state(hass).attributes["temperature"] == 23.0
    assert room.state(hass).attributes["override_expiry"] == local("2026-11-16 09:00")
    assert commands(room.trv) == [HEAT_21, FROST, FROST, HEAT_23]


async def test_heat_while_the_window_is_open_overrides_with_the_schedule_level(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Heat without a temperature while airing keeps comfort, not frost protection."""
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await window.open()
    await clock.advance_to("2026-11-16 08:05:00")

    await room.call(hass, "set_hvac_mode", hvac_mode="heat")
    await window.close()

    assert room.state(hass).state == "heat"
    assert room.state(hass).attributes["temperature"] == 21.0
    assert commands(room.trv) == [HEAT_21, FROST, HEAT_21]


async def test_window_stays_open_when_the_global_settings_change(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Reloading the rooms keeps an open window open, without a new delay."""
    clock.set("2026-11-16 08:00")
    room, window = await _living_room_with_window(hass, schedules, simulated_trvs)
    await window.open()
    await clock.advance_to("2026-11-16 08:05:00")

    await change_global_settings(hass, room.entry, away_temperature=16.0)

    assert room.reason(hass).attributes["reason_code"] == "window_open"
    assert room.reason(hass).attributes["since"] == local("2026-11-16 08:00")
    assert commands(room.trv) == [HEAT_21, FROST]


async def test_window_contacts_are_chosen_in_the_room_options(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room set up without contacts follows a contact chosen later."""
    clock.set("2026-11-16 08:00")
    window = WindowContact(hass, "fenster_wohnzimmer")
    room = await living_room(hass, schedules, simulated_trvs)
    await window.open()
    await clock.advance_to("2026-11-16 08:05:00")
    assert commands(room.trv) == [HEAT_21]

    await change_room(
        hass, room.entry, room.subentry, window_contacts=[window.entity_id]
    )

    assert room.subentry.data["window_contacts"] == [window.entity_id]
    assert commands(room.trv) == [HEAT_21, FROST]
