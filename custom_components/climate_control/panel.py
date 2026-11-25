"""Heating panel: the sidebar entry and the JavaScript module behind it."""

from __future__ import annotations

import hashlib
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

PANEL_URL_PATH = "climate-control"
WEBCOMPONENT_NAME = "climate-control-panel"
MODULE_DIR = Path(__file__).parent / "frontend"
MODULE_FILE = "heating-panel.js"
STATIC_URL = f"/{DOMAIN}/frontend"
SIDEBAR_ICON = "mdi:radiator"
_SIDEBAR_TITLES = {"de": "Heizung"}
_DEFAULT_SIDEBAR_TITLE = "Heating"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Show the panel in the sidebar of admins, titled in the language of HA.

    The module URL carries a hash of the module, so browsers and the apps
    load a new version right after an update.
    """
    if not _static_path_registered(hass):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(MODULE_DIR), cache_headers=True)]
        )
    version = await hass.async_add_executor_job(_module_hash)
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=WEBCOMPONENT_NAME,
        sidebar_title=_SIDEBAR_TITLES.get(hass.config.language, _DEFAULT_SIDEBAR_TITLE),
        sidebar_icon=SIDEBAR_ICON,
        module_url=f"{STATIC_URL}/{MODULE_FILE}?v={version}",
        require_admin=True,
    )


@callback
def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the panel from the sidebar; its module stays served."""
    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)


def _static_path_registered(hass: HomeAssistant) -> bool:
    """Return whether the module is served already: routes outlive a reload."""
    return any(
        resource.canonical == STATIC_URL
        for resource in hass.http.app.router.resources()
    )


def _module_hash() -> str:
    return hashlib.sha256((MODULE_DIR / MODULE_FILE).read_bytes()).hexdigest()[:12]
