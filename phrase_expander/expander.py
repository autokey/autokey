"""Expand phrases without simulating cursor movement.

The important invariant is that cursor placement is calculated from the final
payload, not by emitting Home/Up/Left events.  The latter depends on the
editor's wrapping, indentation and blank-line handling and was the source of
the overshoot reported for AutoKey's ``<cursor>`` macro.
"""

from dataclasses import dataclass

CURSOR_MARKER = "<cursor>"


@dataclass(frozen=True)
class ExpansionResult:
    """The text to insert and the zero-based insertion cursor offset."""

    text: str
    cursor_offset: int

    def __post_init__(self) -> None:
        if not 0 <= self.cursor_offset <= len(self.text):
            raise ValueError("cursor_offset must point inside text")


def expand_phrase(phrase: str, marker: str = CURSOR_MARKER) -> ExpansionResult:
    """Remove *marker* and return its exact position in the resulting text.

    A phrase may contain at most one cursor marker.  A missing marker is valid
    and places the cursor at the end, matching ordinary phrase insertion.
    ``str.replace`` is deliberately avoided so the position is computed from
    the same single pass that constructs the payload.
    """

    if not isinstance(phrase, str):
        raise TypeError("phrase must be a string")
    if not isinstance(marker, str) or not marker:
        raise ValueError("marker must be a non-empty string")

    first = phrase.find(marker)
    if first < 0:
        return ExpansionResult(phrase, len(phrase))
    second = phrase.find(marker, first + len(marker))
    if second >= 0:
        raise ValueError("phrase contains more than one cursor marker")

    text = phrase[:first] + phrase[first + len(marker):]
    return ExpansionResult(text, first)
