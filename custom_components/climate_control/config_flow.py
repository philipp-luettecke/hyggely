"""Config flow for the climate_control main entry."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers import selector
import probatio

from .const import (
    CONF_AREA,
    CONF_AWAY_DELAY,
    CONF_AWAY_TEMPERATURE,
    CONF_COMFORT_TEMPERATURE,
    CONF_ECO_TEMPERATURE,
    CONF_FROST_TEMPERATURE,
    CONF_LEAD_TIME,
    CONF_NAME,
    CONF_NIGHT_TEMPERATURE,
    CONF_NOTIFY_TARGETS,
    CONF_OVERRIDE_EXPIRY_DURATION,
    CONF_OVERRIDE_EXPIRY_POLICY,
    CONF_PERSONS,
    CONF_QUIET_END,
    CONF_QUIET_START,
    CONF_SCHEDULE,
    CONF_TRVS,
    CONF_VACATION_TEMPERATURE,
    CONF_WINDOW_CONTACTS,
    CONF_WINDOW_DELAY,
    DEFAULT_AWAY_DELAY,
    DEFAULT_AWAY_TEMPERATURE,
    DEFAULT_COMFORT_TEMPERATURE,
    DEFAULT_ECO_TEMPERATURE,
    DEFAULT_FROST_TEMPERATURE,
    DEFAULT_LEAD_TIME,
    DEFAULT_NIGHT_TEMPERATURE,
    DEFAULT_OVERRIDE_EXPIRY_DURATION,
    DEFAULT_OVERRIDE_EXPIRY_POLICY,
    DEFAULT_QUIET_END,
    DEFAULT_QUIET_START,
    DEFAULT_VACATION_TEMPERATURE,
    DEFAULT_WINDOW_DELAY,
    DOMAIN,
    OVERRIDE_EXPIRY_GLOBAL,
    OVERRIDE_EXPIRY_POLICIES,
    SUBENTRY_TYPE_ROOM,
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


def _room_schema() -> probatio.Schema:
    return probatio.Schema(
        {
            probatio.Required(CONF_NAME): selector.TextSelector(),
            probatio.Required(CONF_TRVS): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="climate", multiple=True)
            ),
            probatio.Optional(
                CONF_WINDOW_CONTACTS, default=[]
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
            ),
            probatio.Required(CONF_SCHEDULE): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="schedule")
            ),
            probatio.Required(
                CONF_COMFORT_TEMPERATURE, default=DEFAULT_COMFORT_TEMPERATURE
            ): _temperature_selector(),
            probatio.Required(
                CONF_NIGHT_TEMPERATURE, default=DEFAULT_NIGHT_TEMPERATURE
            ): _temperature_selector(),
            probatio.Required(
                CONF_ECO_TEMPERATURE, default=DEFAULT_ECO_TEMPERATURE
            ): _temperature_selector(),
            probatio.Required(
                CONF_LEAD_TIME, default=DEFAULT_LEAD_TIME
            ): selector.DurationSelector(),
            probatio.Required(CONF_AREA): selector.AreaSelector(),
            probatio.Required(
                CONF_OVERRIDE_EXPIRY_POLICY, default=OVERRIDE_EXPIRY_GLOBAL
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[OVERRIDE_EXPIRY_GLOBAL, *OVERRIDE_EXPIRY_POLICIES],
                    translation_key=CONF_OVERRIDE_EXPIRY_POLICY,
                )
            ),
            probatio.Optional(
                CONF_OVERRIDE_EXPIRY_DURATION
            ): selector.DurationSelector(),
        }
    )


def _room_data(user_input: dict[str, Any]) -> dict[str, Any]:
    """Store the room settings; the name is the title of the room."""
    return {key: value for key, value in user_input.items() if key != CONF_NAME}


def _room_errors(user_input: dict[str, Any]) -> dict[str, str]:
    """Return what keeps the room settings from being stored; a room needs a TRV."""
    return {} if user_input[CONF_TRVS] else {CONF_TRVS: "no_trvs"}


class RoomSubentryFlow(ConfigSubentryFlow):
    """Add or change a room of the main entry."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask for the settings of a new room."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not (errors := _room_errors(user_input)):
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=_room_data(user_input)
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                _room_schema(), user_input or {}
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Show the room settings prefilled with the current values."""
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not (errors := _room_errors(user_input)):
                return self.async_update_and_abort(
                    self._get_entry(),
                    subentry,
                    title=user_input[CONF_NAME],
                    data=_room_data(user_input),
                )
        current = user_input or {**subentry.data, CONF_NAME: subentry.title}
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(_room_schema(), current),
            errors=errors,
        )


class ClimateControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create the main entry holding the global settings."""

    VERSION = 1

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Rooms are subentries of the main entry."""
        return {SUBENTRY_TYPE_ROOM: RoomSubentryFlow}

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


class ClimateControlOptionsFlow(OptionsFlow):
    """Change the global settings of the main entry; its update listener reloads."""

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
