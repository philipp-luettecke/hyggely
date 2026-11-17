"""Notifications: windows left open and offline TRVs, once, bundled, not at night."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from tests.scenario import (
    Clock,
    Schedules,
    WindowContact,
    add_main_entry,
    add_room,
    block,
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
            trv=trvs[name].entity_id,
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
