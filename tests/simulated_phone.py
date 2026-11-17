"""Simulated phones for scenario tests: notify entities that keep their messages.

Like the Companion App, each phone is a `notify` entity on its own device that
supports a title; `notify.send_message` reaches it as in a real installation.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pytest_homeassistant.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    mock_integration,
    mock_platform,
)

PHONE_DOMAIN = "simulated_phone"


class _SimulatedPhoneConfigFlow(ConfigFlow, domain=PHONE_DOMAIN):
    """Owner of the config entries that carry the simulated phones."""

    VERSION = 1


@dataclass(frozen=True)
class Message:
    """A notification as the phone shows it."""

    title: str | None
    message: str


class SimulatedPhone(NotifyEntity):
    """A phone with the Companion App, reached through its notify entity."""

    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, object_id: str) -> None:
        """Create the phone as `notify.<object_id>`."""
        self.entity_id = f"notify.{object_id}"
        self._attr_unique_id = object_id
        self._attr_name = object_id
        self._attr_device_info = DeviceInfo(
            identifiers={(PHONE_DOMAIN, object_id)}, name=object_id
        )
        self.messages: list[Message] = []

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Show the notification."""
        self.messages.append(Message(title, message))


class SimulatedPhones:
    """Factory that adds simulated phones to the test Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Register the simulated phone integration."""
        self._hass = hass
        self._phones_by_entry: dict[str, SimulatedPhone] = {}

        async def setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
            await hass.config_entries.async_forward_entry_setups(
                entry, [Platform.NOTIFY]
            )

        async def setup_notify(
            hass: HomeAssistant,
            entry: ConfigEntry,
            async_add_entities: AddConfigEntryEntitiesCallback,
        ) -> None:
            async_add_entities([self._phones_by_entry[entry.entry_id]])

        mock_integration(hass, MockModule(PHONE_DOMAIN, async_setup_entry=setup_entry))
        mock_platform(hass, f"{PHONE_DOMAIN}.config_flow")
        mock_platform(
            hass,
            f"{PHONE_DOMAIN}.{Platform.NOTIFY}",
            MockPlatform(async_setup_entry=setup_notify),
        )

    async def add(self, object_id: str) -> SimulatedPhone:
        """Add a phone as `notify.<object_id>`."""
        phone = SimulatedPhone(object_id)
        entry = MockConfigEntry(domain=PHONE_DOMAIN, title=object_id)
        entry.add_to_hass(self._hass)
        self._phones_by_entry[entry.entry_id] = phone
        assert await self._hass.config_entries.async_setup(entry.entry_id)
        await self._hass.async_block_till_done()
        return phone
