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
