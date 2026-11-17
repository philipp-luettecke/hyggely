"""Each room explains its target with a reason sensor: plain text plus stable code."""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.helpers.translation import async_get_translations
import pytest

from tests.scenario import TIME_ZONE, Clock, LivingRoom, Schedules, living_room
from tests.simulated_trv import SimulatedTrvs

DOMAIN = "climate_control"


def _local(moment: str) -> datetime:
    return datetime.fromisoformat(moment).replace(tzinfo=ZoneInfo(TIME_ZONE))


async def _speak(hass: HomeAssistant, language: str) -> None:
    await hass.config.async_update(language=language)
    await hass.async_block_till_done()


async def _call(
    hass: HomeAssistant, room: LivingRoom, service: str, **data: Any
) -> None:
    await hass.services.async_call(
        "climate", service, {"entity_id": room.entity_id(hass), **data}, blocking=True
    )
    await hass.async_block_till_done()


async def test_reason_explains_comfort_until_the_block_ends(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """During the block the reason reads comfort until its end at 09:00."""
    await _speak(hass, "de")
    clock.set("2026-11-16 08:00")

    room = await living_room(hass, schedules, simulated_trvs)

    reason = room.reason(hass)
    assert reason.state == "Komfort bis 09:00"
    assert reason.attributes["reason_code"] == "comfort"
    assert reason.attributes["until"] == _local("2026-11-16 09:00")
    assert reason.name == "Wohnzimmer Grund"


async def test_reason_names_the_date_of_a_block_boundary_beyond_a_day(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """After Monday's block eco holds until next Monday 07:00, shown with its date."""
    await _speak(hass, "de")
    clock.set("2026-11-16 12:00")

    room = await living_room(hass, schedules, simulated_trvs)

    reason = room.reason(hass)
    assert reason.state == "Eco bis 23.11. 07:00"
    assert reason.attributes["reason_code"] == "eco"
    assert reason.attributes["until"] == _local("2026-11-23 07:00")


async def test_reason_follows_the_room_across_block_boundaries(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Eco until the block starts, then comfort until it ends."""
    await _speak(hass, "de")
    clock.set("2026-11-16 06:00")
    room = await living_room(hass, schedules, simulated_trvs)
    assert room.reason(hass).state == "Eco bis 07:00"

    await clock.advance_to("2026-11-16 07:00:00")

    assert room.reason(hass).state == "Komfort bis 09:00"
    assert room.reason(hass).attributes["reason_code"] == "comfort"


async def test_reason_is_in_english_when_home_assistant_speaks_english(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The reason text follows the language of Home Assistant."""
    await _speak(hass, "en")
    clock.set("2026-11-16 08:00")

    room = await living_room(hass, schedules, simulated_trvs)

    assert room.reason(hass).state == "Comfort until 09:00"
    assert room.reason(hass).name == "Wohnzimmer Reason"


async def test_reason_switches_language_with_home_assistant(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Changing the language of Home Assistant translates the reason at once."""
    await _speak(hass, "en")
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await _speak(hass, "de")

    assert room.reason(hass).state == "Komfort bis 09:00"


async def test_reason_explains_an_override_until_it_expires(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A temperature set on the room entity reads as manual heating until 09:00."""
    await _speak(hass, "de")
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await _call(hass, room, "set_temperature", temperature=23)

    assert room.reason(hass).state == "Heizen bis 09:00 (manuell)"
    assert room.reason(hass).attributes["reason_code"] == "override"


async def test_reason_explains_a_room_switched_off(
    hass: HomeAssistant,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A room switched off reads as off until the next block boundary."""
    await _speak(hass, "de")
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await _call(hass, room, "set_hvac_mode", hvac_mode="off")

    assert room.reason(hass).state == "Aus bis 09:00"
    assert room.reason(hass).attributes["reason_code"] == "room_off"


REASON_CODES = [
    "comfort",
    "night",
    "eco",
    "override",
    "room_off",
    "window_open",
    "away",
    "vacation",
    "house_off",
]


@pytest.mark.parametrize("language", ["de", "en"])
async def test_every_reason_code_has_a_text_in_the_language(
    hass: HomeAssistant, language: str
) -> None:
    """Reasons of later inputs are already translated, with and without a time."""
    prefix = f"component.{DOMAIN}.entity.sensor.reason.state"

    texts = await async_get_translations(hass, language, "entity", [DOMAIN])

    assert all(texts.get(f"{prefix}.{code}") for code in REASON_CODES)
    for code in ("comfort", "night", "eco", "override", "room_off", "vacation"):
        assert "{until}" in texts[f"{prefix}.{code}_until"]
    assert "{minutes}" in texts[f"{prefix}.window_open_since"]
