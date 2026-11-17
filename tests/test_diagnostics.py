"""The admin downloads diagnostics: settings, room snapshots and recent decisions."""

from collections.abc import Awaitable, Callable
import json
from typing import Any

from homeassistant.auth.models import User
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant.typing import ClientSessionGenerator

from tests.scenario import Clock, Schedules, change_global_settings, living_room
from tests.simulated_trv import SimulatedTrvs

PERSONS_AND_RECIPIENTS = {
    "persons": ["person.anna", "person.ben"],
    "notify_targets": ["notify.anna_phone", "notify.ben_phone"],
}


type DownloadDiagnostics = Callable[[ConfigEntry], Awaitable[dict[str, Any]]]


@pytest.fixture
def download_diagnostics(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, hass_admin_user: User
) -> DownloadDiagnostics:
    """Download as the admin with a token issued at the current test time."""

    async def download(entry: ConfigEntry) -> dict[str, Any]:
        refresh_token = await hass.auth.async_create_refresh_token(
            hass_admin_user, "https://example.com/app"
        )
        access_token = hass.auth.async_create_access_token(refresh_token)
        diagnostics: dict[str, Any] = await get_diagnostics_for_config_entry(
            hass, lambda: hass_client(access_token), entry
        )
        return diagnostics

    return download


async def test_diagnostics_hold_settings_snapshots_and_decisions_but_no_persons(
    hass: HomeAssistant,
    download_diagnostics: DownloadDiagnostics,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Diagnostics after a block start, with persons and recipients left out."""
    clock.set("2026-11-16 06:00")
    room = await living_room(hass, schedules, simulated_trvs)
    await change_global_settings(hass, room.entry, **PERSONS_AND_RECIPIENTS)
    await clock.advance_to("2026-11-16 07:00:00")

    diagnostics = await download_diagnostics(room.entry)

    assert "anna" not in json.dumps(diagnostics)
    assert diagnostics["settings"]["persons"] == "**REDACTED**"
    assert diagnostics["settings"]["notify_targets"] == "**REDACTED**"
    assert diagnostics["settings"]["frost_temperature"] == 7.0
    [living] = diagnostics["rooms"]
    assert living["name"] == "Wohnzimmer"
    assert living["settings"]["trvs"] == [room.trv.entity_id]
    assert living["settings"]["comfort_temperature"] == 21.0
    assert living["snapshot"]["now"] == "2026-11-16T06:00:00+00:00"
    assert living["snapshot"]["schedule"] == {
        "level": "comfort",
        "next_block_boundary": "2026-11-16T08:00:00+00:00",
    }
    assert living["snapshot"]["room_mode"] == "auto"
    assert [
        (decision["decided_at"], decision["target_temperature"], decision["reason"])
        for decision in living["decisions"]
    ] == [
        (
            "2026-11-16T05:00:00+00:00",
            17.0,
            {"code": "eco", "params": {"until": "2026-11-16T06:00:00+00:00"}},
        ),
        (
            "2026-11-16T06:00:00+00:00",
            21.0,
            {"code": "comfort", "params": {"until": "2026-11-16T08:00:00+00:00"}},
        ),
    ]
