"""Panel API, schedule of a room (ticket 18): assign a schedule to a room.

Schedules themselves are read, written and deleted by the panel through the
native `schedule/*` commands.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the commands of the schedule of a room."""
