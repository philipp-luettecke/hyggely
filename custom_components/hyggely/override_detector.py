"""Override detector: tells echoes and external changes of TRVs apart.

Measured at the tado hardware: an own command shows in the TRV state at once and
has no later echoes; a knob turn arrives with the next minute poll, with only its
end value. So every reported setting that differs from the target of the room and
from the setting the TRV showed before is an external change, without debouncing
or echo windows. A report that keeps the setting, e.g. with a new current
temperature, changes nothing: a TRV waiting for its paced command or keeping a
command it did not take still shows its old setting. One case is unclear: if the
first poll after a command shows exactly the setting from before the command, the
TRV did not take it, and the command is sent once more.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .target_resolver import TrvMode

FIRST_POLL_WITHIN = timedelta(seconds=62)
"""Home Assistant polls a TRV once a minute; measured up to 61 s."""


@dataclass(frozen=True, kw_only=True)
class TrvSetting:
    """Mode and target temperature of a TRV; an off TRV has no temperature."""

    mode: TrvMode
    temperature: float | None = None


class Classification(StrEnum):
    """What a reported TRV setting means for the room."""

    MATCHES = "matches"
    """The TRV has the target of the room: an echo or nothing new."""
    UNCHANGED = "unchanged"
    """The TRV still shows the setting it had before: nothing new."""
    EXTERNAL_CHANGE = "external_change"
    """Someone changed the TRV, e.g. at the knob; becomes an override."""
    NOT_TAKEN = "not_taken"
    """The TRV did not take the command; send it once more."""
    NOT_TAKEN_AGAIN = "not_taken_again"
    """The TRV did not take the repeated command either; leave it."""


@dataclass(frozen=True, kw_only=True)
class _Command:
    before: TrvSetting | None
    sent_at: datetime
    repeated: bool


class OverrideDetector:
    """Classifies the settings the TRVs of one room report."""

    def __init__(self) -> None:
        """Start without commands."""
        self._commands: dict[str, _Command] = {}

    def command_sent(
        self,
        trv: str,
        *,
        before: TrvSetting | None,
        now: datetime,
        repeated: bool = False,
    ) -> None:
        """Note a command to `trv`, which had `before`; `repeated` if not taken."""
        self._commands[trv] = _Command(before=before, sent_at=now, repeated=repeated)

    def classify(
        self,
        trv: str,
        reported: TrvSetting,
        *,
        previous: TrvSetting | None,
        target: TrvSetting,
        now: datetime,
    ) -> Classification:
        """Classify the setting `trv` reports after `previous` against the target."""
        if reported == target:
            return Classification.MATCHES
        if reported == previous:
            return Classification.UNCHANGED
        command = self._commands.pop(trv, None)
        if (
            command is not None
            and reported == command.before
            and now - command.sent_at <= FIRST_POLL_WITHIN
        ):
            if command.repeated:
                return Classification.NOT_TAKEN_AGAIN
            return Classification.NOT_TAKEN
        return Classification.EXTERNAL_CHANGE
