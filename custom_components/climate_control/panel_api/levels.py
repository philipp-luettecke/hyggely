"""Panel API, levels (ticket 19).

Level temperatures and lead time of a room, global temperatures for away,
vacation and frost protection.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the commands of the levels."""
