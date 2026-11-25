"""Panel API, house (ticket 20).

House mode, vacation with its end, away with the configured persons.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the commands of the house."""
