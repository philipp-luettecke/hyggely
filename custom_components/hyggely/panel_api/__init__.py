"""Panel API: websocket commands of the heating panel, for admins only.

Each ticket keeps its commands in its own module with an
`async_register_commands(hass)`; this package only calls them.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback

from . import house, levels, rooms, schedules


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register all commands of the panel API."""
    for module in (rooms, schedules, levels, house):
        module.async_register_commands(hass)
