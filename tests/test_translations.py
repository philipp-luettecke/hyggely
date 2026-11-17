"""UI texts of the main entry exist in German and English."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.helpers.translation import async_get_translations
import pytest

DOMAIN = "climate_control"

SETTINGS = [
    "persons",
    "away_delay",
    "notify_targets",
    "quiet_start",
    "quiet_end",
    "away_temperature",
    "vacation_temperature",
    "frost_temperature",
    "override_expiry_policy",
    "override_expiry_duration",
    "window_delay",
]


@pytest.mark.parametrize(
    ("language", "title", "persons_label"),
    [
        ("en", "Heating control", "Persons"),
        ("de", "Heizungssteuerung", "Personen"),
    ],
)
async def test_setup_dialog_is_labelled_in_the_language(
    hass: HomeAssistant, language: str, title: str, persons_label: str
) -> None:
    """The setup dialog shows a title and a label for every global setting."""
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    prefix = f"component.{DOMAIN}.config.step.user"

    texts = await async_get_translations(hass, language, "config", [DOMAIN])

    assert texts[f"{prefix}.title"] == title
    assert texts[f"{prefix}.data.persons"] == persons_label
    assert all(texts.get(f"{prefix}.data.{key}") for key in SETTINGS)


@pytest.mark.parametrize(
    ("language", "persons_label"), [("en", "Persons"), ("de", "Personen")]
)
async def test_options_dialog_is_labelled_in_the_language(
    hass: HomeAssistant, language: str, persons_label: str
) -> None:
    """The options dialog shows a label for every global setting."""
    prefix = f"component.{DOMAIN}.options.step.init"

    texts = await async_get_translations(hass, language, "options", [DOMAIN])

    assert texts[f"{prefix}.data.persons"] == persons_label
    assert all(texts.get(f"{prefix}.data.{key}") for key in SETTINGS)


ROOM_SETTINGS = [
    "name",
    "trvs",
    "window_contacts",
    "schedule",
    "comfort_temperature",
    "night_temperature",
    "eco_temperature",
    "lead_time",
    "area",
    "override_expiry_policy",
    "override_expiry_duration",
]


@pytest.mark.parametrize(
    ("language", "entry_type", "trv_label"),
    [("en", "Room", "Radiator thermostats"), ("de", "Raum", "Heizkörperthermostate")],
)
async def test_room_dialogs_are_labelled_in_the_language(
    hass: HomeAssistant, language: str, entry_type: str, trv_label: str
) -> None:
    """Adding and changing a room show a label for every room setting."""
    prefix = f"component.{DOMAIN}.config_subentries.room"

    texts = await async_get_translations(hass, language, "config_subentries", [DOMAIN])

    assert texts[f"{prefix}.entry_type"] == entry_type
    assert texts[f"{prefix}.initiate_flow.user"]
    assert texts[f"{prefix}.error.no_trvs"]
    for step in ("user", "reconfigure"):
        assert texts[f"{prefix}.step.{step}.data.trvs"] == trv_label
        assert all(
            texts.get(f"{prefix}.step.{step}.data.{key}") for key in ROOM_SETTINGS
        )


@pytest.mark.parametrize(
    ("language", "earliest_label"),
    [
        ("en", "Earlier of next block boundary and duration"),
        ("de", "Früheres von nächstem Schaltpunkt und Dauer"),
    ],
)
async def test_override_expiry_policies_are_labelled_in_the_language(
    hass: HomeAssistant, language: str, earliest_label: str
) -> None:
    """Every override expiry policy has a readable label."""
    prefix = f"component.{DOMAIN}.selector.override_expiry_policy.options"

    texts = await async_get_translations(hass, language, "selector", [DOMAIN])

    assert texts[f"{prefix}.earliest"] == earliest_label
    assert texts[f"{prefix}.next_block"]
    assert texts[f"{prefix}.duration"]
    assert texts[f"{prefix}.global"]


@pytest.mark.parametrize(
    ("language", "title"),
    [
        ("en", "Radiator thermostat {trv} unreachable"),
        ("de", "Heizkörperthermostat {trv} nicht erreichbar"),
    ],
)
async def test_offline_trv_repair_issue_is_worded_in_the_language(
    hass: HomeAssistant, language: str, title: str
) -> None:
    """The repair issue of an offline TRV has a title and a description."""
    prefix = f"component.{DOMAIN}.issues.trv_offline"

    texts = await async_get_translations(hass, language, "issues", [DOMAIN])

    assert texts[f"{prefix}.title"] == title
    assert "{room}" in texts[f"{prefix}.description"]


@pytest.mark.parametrize(
    ("language", "house", "away", "on", "off"),
    [("en", "House", "Away", "Yes", "No"), ("de", "Haus", "Abwesend", "Ja", "Nein")],
)
async def test_away_entity_of_the_house_is_labelled_in_the_language(
    hass: HomeAssistant, language: str, house: str, away: str, on: str, off: str
) -> None:
    """The house device and its away entity have a name and readable states."""
    devices = await async_get_translations(hass, language, "device", [DOMAIN])
    entities = await async_get_translations(hass, language, "entity", [DOMAIN])
    prefix = f"component.{DOMAIN}.entity.binary_sensor.away"

    assert devices[f"component.{DOMAIN}.device.house.name"] == house
    assert entities[f"{prefix}.name"] == away
    assert entities[f"{prefix}.state.on"] == on
    assert entities[f"{prefix}.state.off"] == off


@pytest.mark.parametrize(
    ("language", "house_mode", "auto", "vacation_end"),
    [
        ("en", "House mode", "Automatic", "Vacation end"),
        ("de", "Hausbetriebsart", "Automatik", "Urlaubsende"),
    ],
)
async def test_house_mode_and_vacation_end_are_labelled_in_the_language(
    hass: HomeAssistant, language: str, house_mode: str, auto: str, vacation_end: str
) -> None:
    """House mode with its three options, vacation end and the refusal of vacation."""
    entities = await async_get_translations(hass, language, "entity", [DOMAIN])
    errors = await async_get_translations(hass, language, "exceptions", [DOMAIN])
    prefix = f"component.{DOMAIN}.entity"

    assert entities[f"{prefix}.select.house_mode.name"] == house_mode
    assert entities[f"{prefix}.select.house_mode.state.auto"] == auto
    assert entities[f"{prefix}.select.house_mode.state.vacation"]
    assert entities[f"{prefix}.select.house_mode.state.off"]
    assert entities[f"{prefix}.datetime.vacation_end.name"] == vacation_end
    assert errors[f"component.{DOMAIN}.exceptions.vacation_end_not_ahead.message"]
