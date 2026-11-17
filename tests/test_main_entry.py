"""Setting up the main entry with the global settings."""

from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry

DOMAIN = "climate_control"


async def test_main_entry_is_set_up_from_the_ui_with_spec_defaults(
    hass: HomeAssistant,
) -> None:
    """Accepting the prefilled form creates a loaded main entry with spec defaults."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]
    assert entry.state is ConfigEntryState.LOADED
    assert dict(entry.options) == {
        "persons": [],
        "away_delay": {"hours": 0, "minutes": 30, "seconds": 0},
        "notify_targets": [],
        "quiet_start": "22:00:00",
        "quiet_end": "07:00:00",
        "away_temperature": 17.0,
        "vacation_temperature": 15.0,
        "frost_temperature": 7.0,
        "override_expiry_policy": "earliest",
        "override_expiry_duration": {"hours": 3, "minutes": 0, "seconds": 0},
        "window_delay": {"hours": 0, "minutes": 1, "seconds": 0},
    }


async def test_main_entry_can_only_be_added_once(hass: HomeAssistant) -> None:
    """A second attempt to add the integration is refused."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
