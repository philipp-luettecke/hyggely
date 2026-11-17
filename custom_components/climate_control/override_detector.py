"""Override detector: tells echoes and external changes of TRVs apart.

Measured in ticket 01: an own command shows in the TRV state at once and has no
later echoes; a knob turn arrives with the next minute poll, with only its end
value. So every reported setting that differs from the target of the room is an
external change, without debouncing or echo windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .target_resolver import TrvMode


@dataclass(frozen=True, kw_only=True)
class TrvSetting:
    """Mode and target temperature of a TRV; an off TRV has no temperature."""

    mode: TrvMode
    temperature: float | None = None


class Classification(StrEnum):
    """What a reported TRV setting means for the room."""

    MATCHES = "matches"
    """The TRV has the target of the room: an echo or nothing new."""
    EXTERNAL_CHANGE = "external_change"
    """Someone changed the TRV, e.g. at the knob; becomes an override."""


class OverrideDetector:
    """Classifies the settings the TRVs of one room report."""

    def classify(self, reported: TrvSetting, *, target: TrvSetting) -> Classification:
        """Classify the setting a TRV reports against the target of the room."""
        if reported == target:
            return Classification.MATCHES
        return Classification.EXTERNAL_CHANGE
