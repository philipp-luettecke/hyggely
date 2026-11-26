"""Setting up the main entry with the global settings."""

from homeassistant.config_entries import SOURCE_USER, ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry

DOMAIN = "hyggely"


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
        "presence_delay": {"hours": 0, "minutes": 30, "seconds": 0},
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


CHANGED_SETTINGS = {
    "persons": ["person.anna", "person.ben"],
    "presence_delay": {"hours": 0, "minutes": 45, "seconds": 0},
    "notify_targets": ["notify.anna_phone", "notify.ben_phone"],
    "quiet_start": "21:30:00",
    "quiet_end": "06:30:00",
    "away_temperature": 16.0,
    "vacation_temperature": 14.0,
    "frost_temperature": 6.0,
    "override_expiry_policy": "next_block",
    "override_expiry_duration": {"hours": 2, "minutes": 0, "seconds": 0},
    "window_delay": {"hours": 0, "minutes": 2, "seconds": 0},
}


async def _add_main_entry(hass: HomeAssistant) -> ConfigEntry:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    entry: ConfigEntry = result["result"]
    return entry


async def test_all_global_settings_can_be_changed_in_the_options(
    hass: HomeAssistant,
) -> None:
    """The options dialog changes every global setting and keeps the entry loaded."""
    entry = await _add_main_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], CHANGED_SETTINGS
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert dict(entry.options) == CHANGED_SETTINGS
    assert entry.state is ConfigEntryState.LOADED


async def test_removing_all_persons_and_recipients_in_the_options(
    hass: HomeAssistant,
) -> None:
    """Clearing the persons and recipients leaves none configured."""
    entry = await _add_main_entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], CHANGED_SETTINGS
    )
    await hass.async_block_till_done()

    cleared = {
        key: value
        for key, value in CHANGED_SETTINGS.items()
        if key not in ("persons", "notify_targets")
    }
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], cleared)
    await hass.async_block_till_done()

    assert entry.options["persons"] == []
    assert entry.options["notify_targets"] == []
