# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import typing
from unittest.mock import MagicMock

import pytest
from hamcrest import *

from autokey.model.triggermode import TriggerMode
import autokey.model.phrase
from autokey.interface import WindowInfo

ABBR_ONLY = [TriggerMode.ABBREVIATION]

AbbreviationType = typing.Union[str, typing.List[str]]

# Used as parameter containers to cut down argument count.
# These make reading output of failed test cases much easier, because when pytest prints it, it annotates each value
# (e.g. "True") with it’s intended meaning (e.g. "ignore_case=True")
PhraseData = typing.NamedTuple("PhraseData", [
    ("name", str),
    ("abbreviation", AbbreviationType),
    ("content", str),
    ("trigger_modes", typing.List[TriggerMode]),
    ("ignore_case", bool),
    ("match_case", bool),
    ("trigger_immediately", bool)
])

PhraseResult = typing.NamedTuple("PhraseResult", [
    ("expansion", typing.Optional[str]),
    ("abbreviation_length", typing.Optional[int]),
    ("backspace_count", int),
    ("triggered_on_input", bool)
])


def create_phrase(
        name: str = "phrase",
        abbreviation: AbbreviationType = "xp@",
        content: str = "expansion@autokey.com",  # Values taken from original test code
        trigger_modes: typing.List[TriggerMode] = None,
        ignore_case: bool = False,
        match_case: bool = False,
        trigger_immediately: bool = False) -> autokey.model.phrase.Phrase:
    """Save typing by wrapping the Phrase constructor, attribute setters and attributes into a single call."""
    if trigger_modes is None:
        trigger_modes = [TriggerMode.ABBREVIATION]
    phrase = autokey.model.phrase.Phrase(name, content)
    if isinstance(abbreviation, str):
        phrase.add_abbreviation(abbreviation)
    else:
        for abbr in abbreviation:
            phrase.add_abbreviation(abbr)
    phrase.set_modes(trigger_modes)
    phrase.ignoreCase = ignore_case
    phrase.matchCase = match_case
    phrase.immediate = trigger_immediately
    # Expansion triggers usage count increase in the parent Folder. Prevent crashes because of a missing parent
    phrase.parent = MagicMock() 
    return phrase


def generate_test_cases_for_ignore_case():
    """Yields PhraseData, typed_input, PhraseResult"""

    # Test format is effectively:
    # yield phrase_data("abbreviation that triggers phrase", is_case_insensitive_trigger, match_phrase_case_to_typed_phrase_case), "typed text containing abbreviation", phrase_result("Phrase Content", should_phrase_have_triggered)

    def phrase_data(abbreviation: str, phrase_content: str, ignore_case: bool) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation=abbreviation, content=phrase_content,
            trigger_modes=[TriggerMode.ABBREVIATION], ignore_case=ignore_case, match_case=False,
            trigger_immediately=False)

    def phrase_result(expansion_result: str, triggered: bool) -> PhraseResult:
        """Local helper function to save typing constant data"""
        return PhraseResult(
            expansion=expansion_result, abbreviation_length=None,
            backspace_count=len(expansion_result), triggered_on_input=triggered)

    yield phrase_data("ab@", "abbr", False), "AB@ ", phrase_result("", False)
    yield phrase_data("AB@", "abbr", False), "ab@ ", phrase_result("", False)

    # Don’t match case
    yield phrase_data("ab@", "abbr", True), "AB@ ", phrase_result("abbr ", True)
    yield phrase_data("AB@", "abbr", True), "ab@ ", phrase_result("abbr ", True)

    yield phrase_data("tri", "ab br", True), "TRI ", phrase_result("ab br ", True)
    yield phrase_data("TRI", "ab br", True), "tri ", phrase_result("ab br ", True)
    yield phrase_data("Tri", "ab br", True), "tri ", phrase_result("ab br ", True)


@pytest.mark.parametrize("phrase_data, trigger_str, phrase_result", generate_test_cases_for_ignore_case())
def test_ignore_case(phrase_data: PhraseData, trigger_str: str, phrase_result: PhraseResult):
    phrase = create_phrase(*phrase_data)

    # Verify trigger behaviour
    assert_that(
        phrase.check_input(trigger_str, WindowInfo("", "")),
        is_(equal_to(phrase_result.triggered_on_input)),
        "Phrase expansion should trigger"
    )
    if phrase_result.triggered_on_input:
        # If the phrase should trigger, also verify the expansion correctness
        assert_that(
            phrase.build_phrase(trigger_str).string,
            is_(equal_to(phrase_result.expansion)),
            "Invalid Phrase expansion result string"
        )


def generate_test_cases_for_match_case():
    """Yields PhraseData, typed_input, PhraseResult"""
    # "tri" in test data is short for "trigger", "ab br" is a short phrase that can show all behaviour variants

    def phrase_data(abbreviation: str, phrase_content: str) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation=abbreviation, content=phrase_content,
            trigger_modes=[TriggerMode.ABBREVIATION], ignore_case=True, match_case=True,
            trigger_immediately=False)
    
    def phrase_result(expansion_result: str) -> PhraseResult:
        """Local helper function to save typing constant data"""
        return PhraseResult(
            expansion=expansion_result, abbreviation_length=None,
            backspace_count=len(expansion_result), triggered_on_input=True)
    
    # Match case for lower case content and a lower case abbreviation
    yield phrase_data("tri", "ab br"), "tri ", phrase_result("ab br ")
    yield phrase_data("tri", "ab br"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("tri", "ab br"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("tri", "ab br"), "TRi ", phrase_result("ab br ")  # Case as defined in the Phrase
    # Match case for UPPER CASE content and a lower case abbreviation
    yield phrase_data("tri", "AB BR"), "tri ", phrase_result("ab br ")
    yield phrase_data("tri", "AB BR"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("tri", "AB BR"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("tri", "AB BR"), "TRi ", phrase_result("AB BR ")  # Case as defined in the Phrase
    # Match case for Title Case content and a lower case abbreviation
    yield phrase_data("tri", "Ab Br"), "tri ", phrase_result("ab br ")
    yield phrase_data("tri", "Ab Br"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("tri", "Ab Br"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("tri", "Ab Br"), "TRi ", phrase_result("Ab Br ")  # Case as defined in the Phrase

    # Match case for lower case content and an UPPER CASE abbreviation
    yield phrase_data("TRI", "ab br"), "tri ", phrase_result("ab br ")
    yield phrase_data("TRI", "ab br"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("TRI", "ab br"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("TRI", "ab br"), "TRi ", phrase_result("ab br ")  # Case as defined in the Phrase
    # Match case for UPPER CASE content and an UPPER CASE abbreviation
    yield phrase_data("TRI", "AB BR"), "tri ", phrase_result("ab br ")
    yield phrase_data("TRI", "AB BR"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("TRI", "AB BR"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("TRI", "AB BR"), "TRi ", phrase_result("AB BR ")  # Case as defined in the Phrase
    # Match case for Title Case content and an UPPER CASE abbreviation
    yield phrase_data("TRI", "Ab Br"), "tri ", phrase_result("ab br ")
    yield phrase_data("TRI", "Ab Br"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("TRI", "Ab Br"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("TRI", "Ab Br"), "TRi ", phrase_result("Ab Br ")  # Case as defined in the Phrase

    # Match case for lower case content and a Title Case abbreviation
    yield phrase_data("Tri", "ab br"), "tri ", phrase_result("ab br ")
    yield phrase_data("Tri", "ab br"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("Tri", "ab br"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("Tri", "ab br"), "TRi ", phrase_result("ab br ")  # Case as defined in the Phrase
    # Match case for UPPER CASE content and a Title Case abbreviation
    yield phrase_data("Tri", "AB BR"), "tri ", phrase_result("ab br ")
    yield phrase_data("Tri", "AB BR"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("Tri", "AB BR"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("Tri", "AB BR"), "TRi ", phrase_result("AB BR ")  # Case as defined in the Phrase
    # Match case for Title Case content and a Title Case abbreviation
    yield phrase_data("Tri", "Ab Br"), "tri ", phrase_result("ab br ")
    yield phrase_data("Tri", "Ab Br"), "Tri ", phrase_result("Ab br ")
    yield phrase_data("Tri", "Ab Br"), "TRI ", phrase_result("AB BR ")
    yield phrase_data("Tri", "Ab Br"), "TRi ", phrase_result("Ab Br ")  # Case as defined in the Phrase


@pytest.mark.parametrize("phrase_data, trigger_str, phrase_result", generate_test_cases_for_match_case())
def test_match_case(phrase_data: PhraseData, trigger_str: str, phrase_result: PhraseResult):
    phrase = create_phrase(*phrase_data)
    # Expansion should always trigger
    assert_that(
        phrase.check_input(trigger_str, WindowInfo("", "")),
        is_(equal_to(phrase_result.triggered_on_input)),
        "Phrase expansion should trigger:"
    )
    # Verify that the case is matched correctly
    result = phrase.build_phrase(trigger_str)
    assert_that(
        result.string,
        is_(equal_to(phrase_result.expansion)),
        "Invalid Phrase expansion result string"
    )
    assert_that(
        result.lefts,
        is_(equal_to(0)),
    )


def generate_test_cases_for_trigger_immediately():
    """Yields PhraseData, typed_input, PhraseResult"""

    def phrase_data(abbreviation: str, ignore_case: bool, match_case: bool) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation=abbreviation, content="Phrase Content.",
            trigger_modes=[TriggerMode.ABBREVIATION], ignore_case=ignore_case, match_case=match_case,
            trigger_immediately=True)

    def phrase_result(expansion_result: str, triggered: bool) -> PhraseResult:
        """Local helper function to save typing constant data"""
        return PhraseResult(
            expansion=expansion_result, abbreviation_length=None,
            backspace_count=len(expansion_result), triggered_on_input=triggered)

    # Positive test
    yield phrase_data("ueue", False, False), "ueue", phrase_result("Phrase Content.", True)
    yield phrase_data("Ueue", False, False), "Ueue", phrase_result("Phrase Content.", True)
    yield phrase_data("UeUe", False, False), "UeUe", phrase_result("Phrase Content.", True)
    yield phrase_data("UEUE", False, False), "UEUE", phrase_result("Phrase Content.", True)

    # Tests for issue https://github.com/autokey/autokey/issues/254
    yield phrase_data("ueue", True, False), "a", phrase_result("", False)
    yield phrase_data("ueue", True, True), "b", phrase_result("", False)
    yield phrase_data("UeUe", True, False), "a", phrase_result("", False)
    yield phrase_data("UeUe", True, True), "a", phrase_result("", False)

    yield phrase_data("ueue", True, False), "A", phrase_result("", False)
    yield phrase_data("ueue", True, True), "B", phrase_result("", False)
    yield phrase_data("UeUe", True, False), "A", phrase_result("", False)
    yield phrase_data("UeUe", True, True), "A", phrase_result("", False)
    # Test that the fix for #254 does not break things.
    # lower case
    yield phrase_data("ueue", True, False), "ueue", phrase_result("Phrase Content.", True)
    yield phrase_data("ueue", True, True), "ueue", phrase_result("phrase content.", True)
    yield phrase_data("UeUe", True, False), "ueue", phrase_result("Phrase Content.", True)
    yield phrase_data("UeUe", True, True), "ueue", phrase_result("phrase content.", True)
    # mixed case
    yield phrase_data("ueue", True, False), "UeUe", phrase_result("Phrase Content.", True)
    yield phrase_data("ueue", True, True), "UeUe", phrase_result("Phrase Content.", True)
    yield phrase_data("UeUe", True, False), "UeUe", phrase_result("Phrase Content.", True)
    yield phrase_data("UeUe", True, True), "UeUe", phrase_result("Phrase Content.", True)
    # title case
    yield phrase_data("ueue", True, False), "Ueue", phrase_result("Phrase Content.", True)
    yield phrase_data("ueue", True, True), "Ueue", phrase_result("Phrase content.", True)
    yield phrase_data("UeUe", True, False), "Ueue", phrase_result("Phrase Content.", True)
    yield phrase_data("UeUe", True, True), "Ueue", phrase_result("Phrase content.", True)
    # upper case
    yield phrase_data("ueue", True, False), "UEUE", phrase_result("Phrase Content.", True)
    yield phrase_data("ueue", True, True), "UEUE", phrase_result("PHRASE CONTENT.", True)
    yield phrase_data("UeUe", True, False), "UEUE", phrase_result("Phrase Content.", True)
    yield phrase_data("UeUe", True, True), "UEUE", phrase_result("PHRASE CONTENT.", True)

    # Issue from gitter
    yield phrase_data("---", False, False), "---", phrase_result("Phrase Content.", True)


@pytest.mark.parametrize("phrase_data, trigger_str, phrase_result", generate_test_cases_for_trigger_immediately())
def test_trigger_immediately(phrase_data: PhraseData, trigger_str: str, phrase_result: PhraseResult):
    window_info = WindowInfo("", "")
    phrase = create_phrase(*phrase_data)

    assert_that(
        phrase.check_input(trigger_str, window_info),
        is_(equal_to(phrase_result.triggered_on_input)),
        """
        Unexpected Phrase trigger.
        Does trigger '{}' triggered on input '{}':
        """.format(phrase_data.abbreviation, trigger_str)
    )

    # Generally don’t trigger if the trigger immediately option is on and there is a space after the typed abbreviation.
    assert_that(phrase.check_input(phrase_data.abbreviation + " ", window_info), is_(equal_to(False)))

    if phrase_result.triggered_on_input:
        # Verify the result, if the expansion should trigger
        abbreviation_length = len(phrase_data.abbreviation)
        result = phrase.build_phrase(trigger_str)
        assert_that(result.string, is_(equal_to(phrase_result.expansion)), "Case matching broken.")
        assert_that(result.backspaces, is_(equal_to(abbreviation_length)), "Result length computation broken.")


def generate_test_cases_for_case_insensitive_rpartition():
    """
    Yields tuples to test the custom case insensitive str.rpartition

    input, separator, (left, match, right)
    """
    yield "a", "ue", ("", "", "a")
    yield "a", "a", ("", "a", "")
    yield "ab", "a", ("", "a", "b")
    yield "abc", "b", ("a", "b", "c")
    yield "ab", "b", ("a", "b", "")
    # Upper case match
    yield "a", "Ue", ("", "", "a")
    yield "a", "A", ("", "a", "")
    yield "ab", "A", ("", "a", "b")
    yield "abc", "B", ("a", "b", "c")
    yield "ab", "B", ("a", "b", "")
    # Upper case buffer
    yield "A", "ue", ("", "", "A")
    yield "A", "a", ("", "A", "")
    yield "AB", "a", ("", "A", "B")
    yield "ABC", "b", ("A", "B", "C")
    yield "AB", "b", ("A", "B", "")


@pytest.mark.parametrize("input_str, match, expected", generate_test_cases_for_case_insensitive_rpartition())
def test_case_insensitive_rpartition(input_str: str, match: str, expected:typing.Tuple[str, str, str]):
    assert_that(autokey.model.phrase.Phrase._case_insensitive_rpartition(input_str, match), is_(equal_to(expected)))


def generate_test_cases_for_undo_on_backspace():
    """Yields PhraseData, typed_input, undo_enabled, PhraseResult"""

    def phrase_data(trigger_immediately: bool) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation="tri", content="ab br",
            trigger_modes=[TriggerMode.ABBREVIATION], ignore_case=False, match_case=False,
            trigger_immediately=trigger_immediately)

    def phrase_result(backspace_count: int) -> PhraseResult:
        """Local helper function to save typing constant data"""
        return PhraseResult(
            expansion="ab br ", abbreviation_length=None,
            backspace_count=backspace_count, triggered_on_input=True)

    # Undo disabled: Only one backspace, regardless of the trigger character
    yield phrase_data(False), "tri ", False, phrase_result(1)
    yield phrase_data(False), "tri\t", False, phrase_result(1)
    yield phrase_data(False), "tri\n", False, phrase_result(1)
    yield phrase_data(True), "tri", False, phrase_result(0)  # Now trigger immediately

    # Undo enabled: Remove the trigger character and phrase content
    yield phrase_data(False), "tri ", True, phrase_result(4)
    yield phrase_data(False), "tri\t", True, phrase_result(4)
    yield phrase_data(False), "tri\n", True, phrase_result(4)
    yield phrase_data(True), "tri", True, phrase_result(3)  # Now trigger immediately


@pytest.mark.parametrize("phrase_data, trigger_str, undo_enabled, phrase_result",
                         generate_test_cases_for_undo_on_backspace())
def test_undo_on_backspace(phrase_data: PhraseData, trigger_str: str, undo_enabled: bool, phrase_result: PhraseResult):
    phrase = create_phrase(*phrase_data)
    phrase.backspace = undo_enabled

    # Expansion should always trigger
    assert_that(
        phrase.check_input(trigger_str, WindowInfo("", "")),
        is_(equal_to(phrase_result.triggered_on_input)),
        "Phrase expansion should trigger:"
    )

    result = phrase.build_phrase(trigger_str)
    assert_that(
        result.backspaces,
        is_(equal_to(phrase_result.backspace_count)),
        "Wrong backspace key count"
    )
    assert_that(
        result.lefts,
        is_(equal_to(0)),
    )


def generate_test_cases_for_omit_trigger():
    """Yields PhraseData, trigger_str, omit_trigger, PhraseResults"""
    def phrase_data(trigger_immediately: bool) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation="tri", content="ab br",
            trigger_modes=[TriggerMode.ABBREVIATION], ignore_case=False, match_case=False,
            trigger_immediately=trigger_immediately)

    def phrase_result(expansion: str, backspace_count: int) -> PhraseResult:
        """Local helper function to save typing constant data"""
        return PhraseResult(
            expansion=expansion, abbreviation_length=None,
            backspace_count=backspace_count, triggered_on_input=True)

    yield phrase_data(False), "tri ", False, phrase_result("ab br ", 4)
    yield phrase_data(False), "tri\t", False, phrase_result("ab br\t", 4)
    yield phrase_data(False), "tri\n", False, phrase_result("ab br\n", 4)
    yield phrase_data(False), "tri ", True, phrase_result("ab br", 4)
    yield phrase_data(False), "tri\t", True, phrase_result("ab br", 4)
    yield phrase_data(False), "tri\n", True, phrase_result("ab br", 4)
    # Now trigger immediately
    yield phrase_data(True), "tri", False, phrase_result("ab br", 3)
    yield phrase_data(True), "tri", True, phrase_result("ab br", 3)


@pytest.mark.parametrize("phrase_data, trigger_str, omit_trigger, phrase_result",
                         generate_test_cases_for_omit_trigger())
def test_omit_trigger(phrase_data: PhraseData, trigger_str: str, omit_trigger: bool, phrase_result: PhraseResult):
    """
    omitTrigger set to True causes the trigger character to be not re-typed during Phrase expansion
    """
    phrase = create_phrase(*phrase_data)
    phrase.omitTrigger = omit_trigger

    # Expansion should always trigger
    assert_that(
        phrase.check_input(trigger_str, WindowInfo("", "")),
        is_(equal_to(phrase_result.triggered_on_input)),
        "Phrase expansion should trigger:"
    )

    result = phrase.build_phrase(trigger_str)

    assert_that(
        result.string,
        is_(equal_to(phrase_result.expansion)),
        "Wrong trigger character in expansion result"
    )
    assert_that(
        result.backspaces,
        is_(equal_to(phrase_result.backspace_count)),
        "Wrong backspace character count"
    )
    assert_that(
        result.lefts,
        is_(equal_to(0)),
    )


def generate_test_cases_for_trigger_phrase_inside_word():
    """Yields PhraseData, trigger_str, PhraseResults"""
    def phrase_data(trigger_immediately: bool) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation="tri", content="ab br",
            trigger_modes=[TriggerMode.ABBREVIATION], ignore_case=False, match_case=False,
            trigger_immediately=trigger_immediately)

    def phrase_result(expansion: str, backspace_count: int) -> PhraseResult:
        """Local helper function to save typing constant data"""
        return PhraseResult(
            expansion=expansion, abbreviation_length=None,
            backspace_count=backspace_count, triggered_on_input=True)
    yield phrase_data(False), "tri\n", phrase_result("ab br\n", 4)
    yield phrase_data(False), "abctri ", phrase_result("ab br ", 4)
    yield phrase_data(False), "ZQtri.", phrase_result("ab br.", 4)
    # Now trigger immediately
    yield phrase_data(True), "tri", phrase_result("ab br", 3)
    yield phrase_data(True), "abctri", phrase_result("ab br", 3)
    yield phrase_data(True), "ZQtri", phrase_result("ab br", 3)

@pytest.mark.parametrize("phrase_data, trigger_str, phrase_result",
                         generate_test_cases_for_trigger_phrase_inside_word())
def test_trigger_phrase_inside_word(phrase_data: PhraseData, trigger_str: str, phrase_result: PhraseResult):
    phrase = create_phrase(*phrase_data)
    phrase.triggerInside = True

    # Expansion should always trigger
    assert_that(
        phrase.check_input(trigger_str, WindowInfo("", "")),
        is_(equal_to(phrase_result.triggered_on_input)),
        "Phrase expansion should trigger:"
    )

    result = phrase.build_phrase(trigger_str)
    assert_that(
        result.string,
        is_(equal_to(phrase_result.expansion)),
        "Wrong expansion result"
    )
    assert_that(
        result.backspaces,
        is_(equal_to(phrase_result.backspace_count)),
        "Wrong backspace character count"
    )
    assert_that(
        result.lefts,
        is_(equal_to(0)),
    )


def generate_test_cases_for_count_lefts_for_cursor_macro():
    """Yields PhraseData, trigger_str, expected_lefts, PhraseResults"""

    def phrase_data(content: str, trigger_immediately: bool) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation="tri", content=content,
            trigger_modes=[TriggerMode.ABBREVIATION], ignore_case=False, match_case=False,
            trigger_immediately=trigger_immediately)

    def phrase_result(expansion: str, backspace_count: int) -> PhraseResult:
        """Local helper function to save typing constant data"""
        return PhraseResult(
            expansion=expansion, abbreviation_length=None,
            backspace_count=backspace_count, triggered_on_input=True)

    # Trigger on trigger character
    yield phrase_data("ab<cursor> br", False), "tri ", 4, phrase_result("ab br ", 4)
    yield phrase_data("ab<cursor> br", False), "tri\n", 4, phrase_result("ab br\n", 4)
    yield phrase_data("ab<cursor> br", False), "tri\t", 4, phrase_result("ab br\t", 4)
    yield phrase_data("ab<cursor> br", False), "tri.", 4, phrase_result("ab br.", 4)

    yield phrase_data("<cursor>ab br", False), "tri ", 6, phrase_result("ab br ", 4)
    yield phrase_data("<cursor>ab br", False), "tri\n", 6, phrase_result("ab br\n", 4)
    yield phrase_data("ab br<cursor>", False), "tri\t", 1, phrase_result("ab br\t", 4)
    yield phrase_data("ab b<cursor>r", False), "tri.", 2, phrase_result("ab br.", 4)

    # Trigger immediately
    yield phrase_data("<cursor>ab br", True), "tri", 5, phrase_result("ab br", 3)
    yield phrase_data("a<cursor>b br", True), "tri", 4, phrase_result("ab br", 3)
    yield phrase_data("ab<cursor> br", True), "tri", 3, phrase_result("ab br", 3)
    yield phrase_data("ab b<cursor>r", True), "tri", 1, phrase_result("ab br", 3)
    yield phrase_data("ab br<cursor>", True), "tri", 0, phrase_result("ab br", 3)


@pytest.mark.parametrize("phrase_data, trigger_str, expected_lefts, phrase_result",
                         generate_test_cases_for_count_lefts_for_cursor_macro())
def test_count_lefts_for_cursor_macro(phrase_data: PhraseData, trigger_str: str,
                                      expected_lefts: int, phrase_result: PhraseResult):
    phrase = create_phrase(*phrase_data)
    # Expansion should always trigger
    assert_that(
        phrase.check_input(trigger_str, WindowInfo("", "")),
        is_(equal_to(phrase_result.triggered_on_input)),
        "Phrase expansion should trigger:"
    )
    pytest.xfail("Counting lefts in expansion result seems to be broken legacy code?")
    result = phrase.build_phrase(trigger_str)
    assert_that(
        result.string,
        is_(equal_to(phrase_result.expansion)),
        "Wrong expansion result"
    )
    assert_that(
        result.backspaces,
        is_(equal_to(phrase_result.backspace_count)),
        "Wrong backspace character count"
    )
    assert_that(
        result.lefts,
        is_(equal_to(expected_lefts)),
    )
