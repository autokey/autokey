import pytest

from phrase_expander import CURSOR_MARKER, ExpansionResult, expand_phrase


def test_marker_is_removed_and_offset_is_relative_to_final_text():
    result = expand_phrase("before\n\n  <cursor>after")
    assert result == ExpansionResult("before\n\n  after", len("before\n\n  "))


def test_blank_lines_do_not_change_cursor_position():
    result = expand_phrase("\n\n\n<cursor>body")
    assert result.text == "\n\n\nbody"
    assert result.cursor_offset == 3


def test_marker_at_boundaries():
    assert expand_phrase("<cursor>text") == ExpansionResult("text", 0)
    assert expand_phrase("text<cursor>") == ExpansionResult("text", 4)


def test_missing_marker_places_cursor_at_end():
    assert expand_phrase("plain") == ExpansionResult("plain", 5)


def test_custom_marker():
    assert expand_phrase("a|b", "|") == ExpansionResult("ab", 1)


@pytest.mark.parametrize("phrase", ["x<cursor>y<cursor>", "<cursor><cursor>"])
def test_multiple_markers_are_rejected(phrase):
    with pytest.raises(ValueError, match="more than one"):
        expand_phrase(phrase)


def test_invalid_arguments_are_rejected():
    with pytest.raises(TypeError):
        expand_phrase(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        expand_phrase("x", "")
