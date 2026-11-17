"""Notifications: windows left open and offline TRVs, once, bundled, not at night."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers import area_registry as ar

from tests.scenario import (
    Clock,
    Schedules,
    WindowContact,
    add_main_entry,
    add_room,
    block,
    change_global_settings,
    duration,
    shut_down,
    start_up,
)
from tests.simulated_phone import Message, SimulatedPhone, SimulatedPhones
from tests.simulated_trv import SimulatedTrv, SimulatedTrvs

TITLE = "Heizung"


@dataclass
class House:
    """Rooms with one TRV and one window contact each, and the recipients."""

    entry: ConfigEntry
    windows: dict[str, WindowContact]
    trvs: dict[str, SimulatedTrv]
    anna: SimulatedPhone
    ben: SimulatedPhone


async def _house(
    hass: HomeAssistant,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
    *rooms: str,
    language: str = "de",
    **global_settings: object,
) -> House:
    """Set up the rooms (default: the living room); Anna and Ben get the messages."""
    await hass.config.async_update(language=language)
    anna = await phones.add("anna")
    ben = await phones.add("ben")
    entry = await add_main_entry(
        hass, notify_targets=[anna.entity_id, ben.entity_id], **global_settings
    )
    windows: dict[str, WindowContact] = {}
    trvs: dict[str, SimulatedTrv] = {}
    for name in rooms or ("Wohnzimmer",):
        slug = name.lower()
        schedule = await schedules.create(name, monday=[block("07:00", "09:00")])
        trvs[name] = await simulated_trvs.add(f"trv_{slug}")
        windows[name] = WindowContact(hass, f"fenster_{slug}")
        await add_room(
            hass,
            entry,
            name=name,
            trvs=[trvs[name].entity_id],
            schedule=schedule,
            area=ar.async_get(hass).async_create(name).id,
            window_contacts=[windows[name].entity_id],
        )
    return House(entry, windows, trvs, anna, ben)


async def test_window_open_for_20_minutes_notifies_every_recipient_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Airing from 12:00: after 20 min and the bundling window, one message each."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)

    await house.windows["Wohnzimmer"].open()
    await clock.advance_to("2026-11-16 12:01:00")
    await clock.advance_to("2026-11-16 12:20:00")
    await clock.advance_to("2026-11-16 12:20:59")
    assert house.anna.messages == []

    await clock.advance_to("2026-11-16 12:21:00")

    expected = [Message(TITLE, "Fenster seit über 20 min offen: Wohnzimmer")]
    assert house.anna.messages == expected
    assert house.ben.messages == expected


async def test_window_still_open_hours_later_is_not_reported_again(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """A window forgotten for the afternoon gives one message, not one per check."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    await house.windows["Wohnzimmer"].open()
    for moment in ("12:01", "12:20", "12:21", "13:00", "16:00", "18:30"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert len(house.anna.messages) == 1


async def test_trv_offline_for_30_minutes_notifies_every_recipient_once(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Unreachable from 12:00, offline at 12:30, one message each, no repetition."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)

    house.trvs["Wohnzimmer"].set_available(False)
    await clock.advance_to("2026-11-16 12:30:00")
    await clock.advance_to("2026-11-16 12:30:59")
    assert house.anna.messages == []

    await clock.advance_to("2026-11-16 12:31:00")
    await clock.advance_to("2026-11-16 15:00:00")

    expected = [
        Message(
            TITLE,
            "Heizkörperthermostat seit über 30 min nicht erreichbar: "
            "trv_wohnzimmer (Wohnzimmer)",
        )
    ]
    assert house.anna.messages == expected
    assert house.ben.messages == expected


async def test_bridge_outage_is_reported_like_an_unreachable_trv(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """The temperature sensor is gone from 12:02, so the TRV is offline at 12:32."""
    clock.set("2026-11-16 12:00:30")
    house = await _house(hass, schedules, simulated_trvs, phones)

    house.trvs["Wohnzimmer"].unplug_bridge()
    for moment in ("12:01", "12:02", "12:32", "12:33"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert len(house.anna.messages) == 1


async def test_closing_the_window_sends_no_message_and_opening_it_again_does(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Reported at 12:21, closed at 12:30, open again from 12:40: reported at 13:01."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    window = house.windows["Wohnzimmer"]
    await window.open()
    for moment in ("12:01", "12:20", "12:21"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    await clock.advance_to("2026-11-16 12:30:00")
    await window.close()
    await clock.advance_to("2026-11-16 12:40:00")
    assert len(house.anna.messages) == 1

    await window.open()
    for moment in ("12:41", "13:00", "13:01"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert (
        house.anna.messages
        == [Message(TITLE, "Fenster seit über 20 min offen: Wohnzimmer")] * 2
    )


async def test_window_closed_before_the_message_goes_out_is_not_reported(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Closed within the bundling window after 20 min, nothing is sent."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    await house.windows["Wohnzimmer"].open()
    for moment in ("12:01:00", "12:20:00", "12:20:30"):
        await clock.advance_to(f"2026-11-16 {moment}")

    await house.windows["Wohnzimmer"].close()
    await clock.advance_to("2026-11-16 12:30:00")

    assert house.anna.messages == []


async def test_trv_back_sends_no_message_and_dropping_out_again_is_reported_again(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """No "back online" message; another 30 min offline gives another message."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    trv = house.trvs["Wohnzimmer"]
    trv.set_available(False)
    await clock.advance_to("2026-11-16 12:30:00")
    await clock.advance_to("2026-11-16 12:31:00")

    trv.set_available(True)
    await clock.advance_to("2026-11-16 12:40:00")
    assert len(house.anna.messages) == 1

    trv.set_available(False)
    await clock.advance_to("2026-11-16 13:10:00")
    await clock.advance_to("2026-11-16 13:11:00")

    assert len(house.anna.messages) == 2


async def test_alerts_of_several_rooms_within_the_bundling_window_make_one_message(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Two windows and an offline TRV in other rooms, all within a minute."""
    clock.set("2026-11-16 11:50:30")
    house = await _house(
        hass, schedules, simulated_trvs, phones, "Wohnzimmer", "Bad", "Kinderzimmer"
    )
    house.trvs["Kinderzimmer"].set_available(False)
    await clock.advance_to("2026-11-16 12:00:00")
    await house.windows["Wohnzimmer"].open()
    await clock.advance_to("2026-11-16 12:00:40")
    await house.windows["Bad"].open()
    for moment in ("12:01:00", "12:01:40", "12:20:00", "12:20:30", "12:20:40"):
        await clock.advance_to(f"2026-11-16 {moment}")
    assert house.anna.messages == []

    await clock.advance_to("2026-11-16 12:21:00")
    await clock.advance_to("2026-11-16 12:30:00")

    expected = [
        Message(
            TITLE,
            "Fenster seit über 20 min offen: Bad, Wohnzimmer\n"
            "Heizkörperthermostat seit über 30 min nicht erreichbar: "
            "trv_kinderzimmer (Kinderzimmer)",
        )
    ]
    assert house.anna.messages == expected
    assert house.ben.messages == expected


async def test_alerts_further_apart_than_the_bundling_window_make_two_messages(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Windows opened at 12:00 and 12:05 are reported at 12:21 and 12:26."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones, "Wohnzimmer", "Bad")
    await house.windows["Wohnzimmer"].open()
    await clock.advance_to("2026-11-16 12:05:00")
    await house.windows["Bad"].open()
    for moment in ("12:06", "12:20", "12:21", "12:25", "12:26"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert house.anna.messages == [
        Message(TITLE, "Fenster seit über 20 min offen: Wohnzimmer"),
        Message(TITLE, "Fenster seit über 20 min offen: Bad"),
    ]


async def test_nothing_is_sent_in_the_quiet_time_and_what_still_applies_comes_at_7(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Living room window open all night, bath window closed at 23:40, TRV out at 1."""
    clock.set("2026-11-16 21:30")
    house = await _house(
        hass, schedules, simulated_trvs, phones, "Wohnzimmer", "Bad", "Kinderzimmer"
    )
    await clock.advance_to("2026-11-16 21:50:00")
    await house.windows["Wohnzimmer"].open()
    for moment in ("21:51", "22:10", "22:11", "23:00"):
        await clock.advance_to(f"2026-11-16 {moment}:00")
    await house.windows["Bad"].open()
    for moment in ("23:01", "23:20", "23:21", "23:40"):
        await clock.advance_to(f"2026-11-16 {moment}:00")
    await house.windows["Bad"].close()
    await clock.advance_to("2026-11-17 01:00:00")
    house.trvs["Kinderzimmer"].set_available(False)
    for moment in ("01:30:00", "01:31:00", "06:59:59"):
        await clock.advance_to(f"2026-11-17 {moment}")
    assert house.anna.messages == []

    await clock.advance_to("2026-11-17 07:00:00")
    await clock.advance_to("2026-11-17 08:00:00")

    expected = [
        Message(
            TITLE,
            "Fenster seit über 20 min offen: Wohnzimmer\n"
            "Heizkörperthermostat seit über 30 min nicht erreichbar: "
            "trv_kinderzimmer (Kinderzimmer)",
        )
    ]
    assert house.anna.messages == expected
    assert house.ben.messages == expected


async def test_alert_resolved_in_the_quiet_time_is_not_reported_in_the_morning(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """The bridge was out from 23:00 to 05:00; at 07:00 there is nothing to say."""
    clock.set("2026-11-16 23:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    trv = house.trvs["Wohnzimmer"]
    trv.set_available(False)
    await clock.advance_to("2026-11-16 23:30:00")
    await clock.advance_to("2026-11-17 05:00:00")
    trv.set_available(True)

    await clock.advance_to("2026-11-17 07:00:00")
    await clock.advance_to("2026-11-17 08:00:00")

    assert house.anna.messages == []


async def test_quiet_time_follows_the_global_settings(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """With a quiet time 12:00-14:00 the window open since 11:50 comes at 14:00."""
    clock.set("2026-11-16 11:50")
    house = await _house(
        hass,
        schedules,
        simulated_trvs,
        phones,
        quiet_start="12:00:00",
        quiet_end="14:00:00",
    )
    await house.windows["Wohnzimmer"].open()
    for moment in ("11:51:00", "12:10:00", "12:11:00", "13:59:59"):
        await clock.advance_to(f"2026-11-16 {moment}")
    assert house.anna.messages == []

    await clock.advance_to("2026-11-16 14:00:00")

    assert len(house.anna.messages) == 1


async def test_message_follows_the_language_of_home_assistant(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """With Home Assistant in English, the message is in English."""
    clock.set("2026-11-16 11:50:30")
    house = await _house(
        hass, schedules, simulated_trvs, phones, "Wohnzimmer", "Bad", language="en"
    )
    house.trvs["Bad"].set_available(False)
    await clock.advance_to("2026-11-16 12:00:00")
    await house.windows["Wohnzimmer"].open()
    for moment in ("12:01:00", "12:20:00", "12:20:30", "12:21:00"):
        await clock.advance_to(f"2026-11-16 {moment}")

    assert house.anna.messages == [
        Message(
            "Heating",
            "Window open for more than 20 min: Wohnzimmer\n"
            "Radiator thermostat unreachable for more than 30 min: trv_bad (Bad)",
        )
    ]


async def test_changing_the_global_settings_does_not_repeat_a_sent_message(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """The options dialog reloads the integration; the open window stays reported."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    await house.windows["Wohnzimmer"].open()
    for moment in ("12:01", "12:20", "12:21"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    await change_global_settings(hass, house.entry, away_delay=duration(45))
    for moment in ("12:30", "12:31", "13:00"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert len(house.anna.messages) == 1


async def test_open_window_reported_before_a_restart_is_not_reported_again(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Reported at 12:21; after the restart at 12:30 the contact reports open anew."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    window = house.windows["Wohnzimmer"]
    await window.open()
    for moment in ("12:01", "12:20", "12:21"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    await shut_down(hass, house.entry)
    await clock.advance_to("2026-11-16 12:30:00")
    await window.report("unavailable")
    await window.open()
    await start_up(hass, house.entry)
    for moment in ("12:31", "12:50", "12:51", "13:00"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert len(house.anna.messages) == 1


async def test_offline_trv_reported_before_a_restart_is_not_reported_again(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Reported at 12:31; after the restart at 12:40 it is unreachable anew."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    trv = house.trvs["Wohnzimmer"]
    trv.set_available(False)
    await clock.advance_to("2026-11-16 12:30:00")
    await clock.advance_to("2026-11-16 12:31:00")

    await shut_down(hass, house.entry)
    await clock.advance_to("2026-11-16 12:40:00")
    trv.set_available(True)
    trv.set_available(False)
    await start_up(hass, house.entry)
    for moment in ("12:41", "13:10", "13:11", "14:00"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert len(house.anna.messages) == 1


async def test_window_contact_appearing_while_home_assistant_starts_is_no_new_alert(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """The contact of the reported window only shows up after the integration."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    window = house.windows["Wohnzimmer"]
    await window.open()
    for moment in ("12:01", "12:20", "12:21"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    await shut_down(hass, house.entry)
    hass.states.async_remove(window.entity_id)
    await clock.advance_to("2026-11-16 12:30:00")
    hass.set_state(CoreState.starting)
    await start_up(hass, house.entry)
    await window.open()
    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    for moment in ("12:31", "12:50", "12:51", "13:00"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert len(house.anna.messages) == 1


async def test_window_closed_during_a_restart_is_reported_when_open_again(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Closed while Home Assistant was down, open again from 12:40: reported."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    window = house.windows["Wohnzimmer"]
    await window.open()
    for moment in ("12:01", "12:20", "12:21"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    await shut_down(hass, house.entry)
    await window.close()
    await clock.advance_to("2026-11-16 12:30:00")
    await start_up(hass, house.entry)
    await clock.advance_to("2026-11-16 12:40:00")
    await window.open()
    for moment in ("12:41", "13:00", "13:01"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert len(house.anna.messages) == 2


async def test_changing_the_recipients_sends_to_the_new_ones(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    phones: SimulatedPhones,
) -> None:
    """Without Ben among the recipients, only Anna gets the message."""
    clock.set("2026-11-16 12:00")
    house = await _house(hass, schedules, simulated_trvs, phones)
    await change_global_settings(
        hass, house.entry, notify_targets=[house.anna.entity_id]
    )
    await house.windows["Wohnzimmer"].open()
    for moment in ("12:01", "12:20", "12:21"):
        await clock.advance_to(f"2026-11-16 {moment}:00")

    assert len(house.anna.messages) == 1
    assert house.ben.messages == []
