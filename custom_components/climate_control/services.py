"""Services of the integration for automations and scripts."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util
import probatio

from .const import DOMAIN

SERVICE_START_VACATION = "start_vacation"
ATTR_END = "end"


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the services of the integration."""

    async def start_vacation(call: ServiceCall) -> None:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="not_loaded"
            )
        await entries[0].runtime_data.house_mode.async_start_vacation(
            dt_util.as_utc(call.data[ATTR_END])
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_VACATION,
        start_vacation,
        schema=probatio.Schema({probatio.Required(ATTR_END): cv.datetime}),
    )
