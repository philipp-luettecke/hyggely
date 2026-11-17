"""Config flow for the climate_control main entry."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithReload,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers import selector
import probatio

from .const import (
    CONF_AWAY_DELAY,
    CONF_AWAY_TEMPERATURE,
    CONF_FROST_TEMPERATURE,
    CONF_NOTIFY_TARGETS,
    CONF_OVERRIDE_EXPIRY_DURATION,
    CONF_OVERRIDE_EXPIRY_POLICY,
    CONF_PERSONS,
    CONF_QUIET_END,
    CONF_QUIET_START,
    CONF_VACATION_TEMPERATURE,
    CONF_WINDOW_DELAY,
    DEFAULT_AWAY_DELAY,
    DEFAULT_AWAY_TEMPERATURE,
    DEFAULT_FROST_TEMPERATURE,
    DEFAULT_OVERRIDE_EXPIRY_DURATION,
    DEFAULT_OVERRIDE_EXPIRY_POLICY,
    DEFAULT_QUIET_END,
    DEFAULT_QUIET_START,
    DEFAULT_VACATION_TEMPERATURE,
    DEFAULT_WINDOW_DELAY,
    DOMAIN,
    OVERRIDE_EXPIRY_POLICIES,
    TEMPERATURE_STEP,
    TRV_MAX_TEMPERATURE,
    TRV_MIN_TEMPERATURE,
)


def _temperature_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=TRV_MIN_TEMPERATURE,
            max=TRV_MAX_TEMPERATURE,
            step=TEMPERATURE_STEP,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _global_settings_schema() -> probatio.Schema:
    return probatio.Schema(
        {
            probatio.Optional(CONF_PERSONS, default=[]): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="person", multiple=True)
            ),
            probatio.Required(
                CONF_AWAY_DELAY, default=DEFAULT_AWAY_DELAY
            ): selector.DurationSelector(),
            probatio.Optional(CONF_NOTIFY_TARGETS, default=[]): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="notify", multiple=True)
            ),
            probatio.Required(
                CONF_QUIET_START, default=DEFAULT_QUIET_START
            ): selector.TimeSelector(),
            probatio.Required(
                CONF_QUIET_END, default=DEFAULT_QUIET_END
            ): selector.TimeSelector(),
            probatio.Required(
                CONF_AWAY_TEMPERATURE, default=DEFAULT_AWAY_TEMPERATURE
            ): _temperature_selector(),
            probatio.Required(
                CONF_VACATION_TEMPERATURE, default=DEFAULT_VACATION_TEMPERATURE
            ): _temperature_selector(),
            probatio.Required(
                CONF_FROST_TEMPERATURE, default=DEFAULT_FROST_TEMPERATURE
            ): _temperature_selector(),
            probatio.Required(
                CONF_OVERRIDE_EXPIRY_POLICY, default=DEFAULT_OVERRIDE_EXPIRY_POLICY
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=OVERRIDE_EXPIRY_POLICIES,
                    translation_key=CONF_OVERRIDE_EXPIRY_POLICY,
                )
            ),
            probatio.Required(
                CONF_OVERRIDE_EXPIRY_DURATION, default=DEFAULT_OVERRIDE_EXPIRY_DURATION
            ): selector.DurationSelector(),
            probatio.Required(
                CONF_WINDOW_DELAY, default=DEFAULT_WINDOW_DELAY
            ): selector.DurationSelector(),
        }
    )


class ClimateControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create the main entry holding the global settings."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the global settings."""
        if user_input is not None:
            return self.async_create_entry(
                title="Climate Control", data={}, options=user_input
            )
        return self.async_show_form(
            step_id="user", data_schema=_global_settings_schema()
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow for the global settings."""
        return ClimateControlOptionsFlow()


class ClimateControlOptionsFlow(OptionsFlowWithReload):
    """Change the global settings of the main entry."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the global settings prefilled with the current values."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                _global_settings_schema(), self.config_entry.options
            ),
        )
