"""The heating panel appears in the sidebar for admins and is served as a module."""

from typing import Any

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant.typing import (
    ClientSessionGenerator,
    MockHAClientWebSocket,
    WebSocketGenerator,
)

from tests.scenario import Clock, Schedules, living_room, shut_down
from tests.simulated_trv import SimulatedTrvs

PANEL = "hyggely"


async def _panels(client: MockHAClientWebSocket) -> dict[str, Any]:
    await client.send_json_auto_id({"type": "get_panels"})
    response = await client.receive_json()
    assert response["success"], response
    panels: dict[str, Any] = response["result"]
    return panels


@pytest.mark.parametrize(("language", "title"), [("de", "Heizung"), ("en", "Heating")])
async def test_sidebar_shows_heating_to_admins(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
    language: str,
    title: str,
) -> None:
    """Once the integration is set up, admins find the heating panel in the sidebar."""
    admin = await hass_ws_client(hass)
    await hass.config.async_update(language=language)
    clock.set("2026-11-16 08:00")
    await living_room(hass, schedules, simulated_trvs)

    panels = await _panels(admin)

    assert panels[PANEL]["title"] == title
    assert panels[PANEL]["icon"] == "mdi:radiator"
    assert panels[PANEL]["require_admin"] is True


async def test_sidebar_hides_heating_from_other_users(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """A user without admin rights does not see the heating panel."""
    user = await hass_ws_client(hass, hass_read_only_access_token)
    clock.set("2026-11-16 08:00")
    await living_room(hass, schedules, simulated_trvs)

    panels = await _panels(user)

    assert PANEL not in panels


async def test_heating_panel_is_served_as_a_javascript_module(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_client: ClientSessionGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """The module the panel loads defines the web component the panel names."""
    admin = await hass_ws_client(hass)
    http = await hass_client()
    clock.set("2026-11-16 08:00")
    await living_room(hass, schedules, simulated_trvs)
    custom = (await _panels(admin))[PANEL]["config"]["_panel_custom"]

    response = await http.get(custom["module_url"])

    assert response.status == 200
    assert f'customElements.define("{custom["name"]}"' in await response.text()


async def test_sidebar_loses_heating_when_the_integration_stops(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    clock: Clock,
    schedules: Schedules,
    simulated_trvs: SimulatedTrvs,
) -> None:
    """Unloading the integration removes the panel from the sidebar."""
    admin = await hass_ws_client(hass)
    clock.set("2026-11-16 08:00")
    room = await living_room(hass, schedules, simulated_trvs)

    await shut_down(hass, room.entry)

    assert PANEL not in await _panels(admin)
