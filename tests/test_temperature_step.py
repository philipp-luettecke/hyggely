"""Temperatures change in whole degrees, like the knob of the TRV."""

from typing import Any

from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
import probatio

from tests.scenario import Clock, Schedules, living_room
from tests.simulated_trv import SimulatedTrvs

DOMAIN = "climate_control"


def _steps(form: dict[str, Any], *fields: str) -> dict[str, Any]:
    """Return the step of number fields as the dialog in the frontend gets it."""
    serialized = probatio.to_field_list(
        form["data_schema"], custom_serializer=cv.custom_serializer
    )
    return {
        field["name"]: field["selector"]["number"]["step"]
        for field in serialized
        if field["name"] in fields
    }


async def test_room_entity_offers_whole_degrees(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The room entity tells the HA app to change the room in steps of 1 °C."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    assert room.state(hass).attributes["target_temp_step"] == 1.0


async def test_room_dialog_offers_whole_degrees_for_the_levels(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Adding and changing a room set comfort, night and eco in steps of 1 °C."""
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)
    levels = ("comfort_temperature", "night_temperature", "eco_temperature")
    whole_degrees = dict.fromkeys(levels, 1.0)

    new_room = await hass.config_entries.subentries.async_init(
        (room.entry.entry_id, "room"), context={"source": SOURCE_USER}
    )
    changed_room = await hass.config_entries.subentries.async_init(
        (room.entry.entry_id, "room"),
        context={
            "source": SOURCE_RECONFIGURE,
            "subentry_id": room.subentry.subentry_id,
        },
    )

    assert _steps(new_room, *levels) == whole_degrees
    assert _steps(changed_room, *levels) == whole_degrees


async def test_global_settings_offer_whole_degrees_for_the_global_levels(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Setup and options set away, vacation and frost in steps of 1 °C."""
    clock.set("2026-11-16 08:00")
    levels = ("away_temperature", "vacation_temperature", "frost_temperature")
    whole_degrees = dict.fromkeys(levels, 1.0)

    setup = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert _steps(setup, *levels) == whole_degrees
    hass.config_entries.flow.async_abort(setup["flow_id"])

    room = await living_room(hass, schedules, simulated_trvs)
    options = await hass.config_entries.options.async_init(room.entry.entry_id)
    assert _steps(options, *levels) == whole_degrees
