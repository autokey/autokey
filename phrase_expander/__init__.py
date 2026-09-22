"""Small, backend-independent phrase expansion primitives."""

from .expander import CURSOR_MARKER, ExpansionResult, expand_phrase

__all__ = ["CURSOR_MARKER", "ExpansionResult", "expand_phrase"]
