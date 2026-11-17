"""Human-readable reasons in the language of Home Assistant.

The texts live in the translations under `entity.sensor.reason.state`: `<code>`
without a time, `<code>_until` with the moment the reason ends and
`<code>_since` with the minutes since it began.
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
        placeholders["minutes"] = str(minutes_since(since, now))
    template = texts.get(f"{_TEXTS}.{key}") or texts.get(f"{_TEXTS}.{code}")
    if template is None:
        return code
    return template.format(**placeholders)


def minutes_since(since: datetime, now: datetime) -> int:
    """Return the whole minutes elapsed from `since` to `now`."""
    return (now - since) // timedelta(minutes=1)


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
    return local.strftime(_DATE_TIME_FORMATS.get(language, _DEFAULT_DATE_TIME_FORMAT))
