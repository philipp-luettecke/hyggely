"""Human-readable reasons in the language of Home Assistant.

The texts live in the translations under `entity.sensor.reason.state`: `<code>`
without a time, `<code>_until` with the moment the reason ends and
`<code>_since` with the moment it began.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.translation import (
    async_get_cached_translations,
    async_get_translations,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_TEXTS = f"component.{DOMAIN}.entity.sensor.reason.state"
_TIME_FORMAT = "%H:%M"
_DATE_TIME_FORMATS = {"de": "%d.%m. %H:%M"}
_DEFAULT_DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"
_DECIMAL_COMMA_LANGUAGES = {"de"}


async def async_load_reason_texts(hass: HomeAssistant) -> None:
    """Load the texts for the current language; `reason_text` needs them."""
    await async_get_translations(hass, hass.config.language, "entity", [DOMAIN])


@callback
def reason_text(
    hass: HomeAssistant, code: str, params: Mapping[str, Any], now: datetime
) -> str:
    """Return the text for a reason as of `now`; the code if no text is loaded.

    Moments in `params` may be datetimes or ISO strings.
    """
    language = hass.config.language
    texts = async_get_cached_translations(hass, language, "entity", DOMAIN)
    key = code
    placeholders: dict[str, str] = {}
    if (until := _moment(params.get("until"))) is not None:
        key = f"{code}_until"
        placeholders["until"] = _format_moment(until, now, language)
    elif (since := _moment(params.get("since"))) is not None:
        key = f"{code}_since"
        placeholders["since"] = _format_past_moment(since, now, language)
    template = texts.get(f"{_TEXTS}.{key}") or texts.get(f"{_TEXTS}.{code}")
    if template is None:
        return code
    return template.format(**placeholders)


@callback
def target_changed_text(
    hass: HomeAssistant,
    temperature: float,
    code: str,
    params: Mapping[str, Any],
    now: datetime,
) -> str:
    """Return the logbook text for a new target, e.g. `21,5 °C (Komfort bis 09:00)`."""
    number = f"{temperature:g}"
    if hass.config.language in _DECIMAL_COMMA_LANGUAGES:
        number = number.replace(".", ",")
    return f"{number} °C ({reason_text(hass, code, params, now)})"


def next_local_midnight(moment: datetime) -> datetime:
    """Return the local midnight after `moment`; from then on it shows its date."""
    next_day = dt_util.as_local(moment).date() + timedelta(days=1)
    return dt_util.start_of_local_day(next_day)


def _moment(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return dt_util.parse_datetime(value)
    return None


def _format_moment(moment: datetime, now: datetime, language: str) -> str:
    """Show the time alone within the next day, otherwise with the date."""
    local = dt_util.as_local(moment)
    if moment - now < timedelta(days=1):
        return local.strftime(_TIME_FORMAT)
    return _format_with_date(local, language)


def _format_past_moment(moment: datetime, now: datetime, language: str) -> str:
    """Show the time alone on the same local day, otherwise with the date."""
    local = dt_util.as_local(moment)
    if now < next_local_midnight(moment):
        return local.strftime(_TIME_FORMAT)
    return _format_with_date(local, language)


def _format_with_date(local: datetime, language: str) -> str:
    return local.strftime(_DATE_TIME_FORMATS.get(language, _DEFAULT_DATE_TIME_FORMAT))
