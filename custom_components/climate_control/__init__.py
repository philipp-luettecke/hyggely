"""Smart, family-friendly heating control."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .command_pacer import CommandPacer
from .const import CONF_AREA, CONF_AWAY_DELAY, CONF_PERSONS, DOMAIN, SUBENTRY_TYPE_ROOM
from .presence import Presence
from .repair_issues import async_track_offline_trvs
from .room_controller import RoomController

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CLIMATE, Platform.SENSOR]


@dataclass
class RuntimeData:
    """Live objects of the main entry."""

    presence: Presence
    pacer: CommandPacer
    rooms: dict[str, RoomController] = field(default_factory=dict)


type ClimateControlConfigEntry = ConfigEntry[RuntimeData]


async def async_setup_entry(
    hass: HomeAssistant, entry: ClimateControlConfigEntry
) -> None:
    """Set up the main entry with one room controller per room."""
    presence = Presence(
        hass,
        entry.options[CONF_PERSONS],
        timedelta(**entry.options[CONF_AWAY_DELAY]),
    )
    pacer = CommandPacer(hass, entry)
    entry.runtime_data = RuntimeData(presence=presence, pacer=pacer)
    entry.async_on_unload(pacer.async_stop)
    for subentry in entry.get_subentries_of_type(SUBENTRY_TYPE_ROOM):
        _async_register_room_device(hass, entry, subentry)
        entry.runtime_data.rooms[subentry.subentry_id] = RoomController(
            hass, entry, subentry, presence, pacer=pacer
        )

    entry.async_on_unload(presence.async_stop)
    presence.async_start()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    for controller in entry.runtime_data.rooms.values():
        entry.async_on_unload(controller.async_stop)
        entry.async_on_unload(async_track_offline_trvs(hass, entry, controller))
        await controller.async_start()

    entry.async_on_unload(entry.add_update_listener(_async_reload))


async def async_unload_entry(
    hass: HomeAssistant, entry: ClimateControlConfigEntry
) -> bool:
    """Unload the main entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply changed global settings and added, changed or removed rooms."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_room_device(
    hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry
) -> None:
    """Keep the device of a room named after it and in its area."""
    registry = dr.async_get(hass)
    device = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        config_subentry_id=subentry.subentry_id,
        identifiers={(DOMAIN, subentry.subentry_id)},
        name=subentry.title,
        manufacturer="Climate Control",
        model="Room",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    registry.async_update_device(device.id, area_id=subentry.data[CONF_AREA])
