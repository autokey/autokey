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

import autokey.model as model

ABBR_ONLY = [model.TriggerMode.ABBREVIATION]

AbbreviationType = typing.Union[str, typing.List[str]]

# Used as parameter containers to cut down argument count.
# These make reading output of failed test cases much easier, because when pytest prints it, it annotates each value
# (e.g. "True") with it’s intended meaning (e.g. "ignore_case=True")
PhraseData = typing.NamedTuple("PhraseData", [
    ("name", str),
    ("abbreviation", AbbreviationType),
    ("content", str),
    ("trigger_modes", typing.List[model.TriggerMode]),
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
        name: str="phrase",
        abbreviation: AbbreviationType="xp@",
        content: str = "expansion@autokey.com",  # Values taken from original test code
        trigger_modes: typing.List[model.TriggerMode]=None,
        ignore_case: bool=False,
        match_case: bool=False,
        trigger_immediately: bool=False) -> model.Phrase:
    """Save typing by wrapping the Phrase constructor, attribute setters and attributes into a single call."""
    if trigger_modes is None:
        trigger_modes = [model.TriggerMode.ABBREVIATION]
    phrase = model.Phrase(name, content)
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

    def phrase_data(abbreviation: str, phrase_content: str, ignore_case: bool) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation=abbreviation, content=phrase_content,
            trigger_modes=[model.TriggerMode.ABBREVIATION], ignore_case=ignore_case, match_case=False,
            trigger_immediately=False)

    def phrase_result(expansion_result: str, triggered: bool) -> PhraseResult:
        """Local helper function to save typing constant data"""
        return PhraseResult(
            expansion=expansion_result, abbreviation_length=None,
            backspace_count=len(expansion_result), triggered_on_input=triggered)

    yield phrase_data("ab@", "abbr", False), "AB@ ", phrase_result("", False)
    yield phrase_data("AB@", "abbr", False), "ab@ ", phrase_result("", False)
    yield phrase_data("ab@", "abbr", True), "AB@ ", phrase_result("abbr ", True)
    yield phrase_data("AB@", "abbr", True), "ab@ ", phrase_result("abbr ", True)

    # Don’t match case
    yield phrase_data("tri", "ab br", True), "TRI ", phrase_result("ab br ", True)
    yield phrase_data("TRI", "ab br", True), "tri ", phrase_result("ab br ", True)
    yield phrase_data("Tri", "ab br", True), "tri ", phrase_result("ab br ", True)


@pytest.mark.parametrize("phrase_data, trigger_str, phrase_result", generate_test_cases_for_ignore_case())
def test_ignore_case(phrase_data: PhraseData, trigger_str: str, phrase_result: PhraseResult):
    phrase = create_phrase(*phrase_data)

    # Verify trigger behaviour
    assert_that(
        phrase.check_input(trigger_str, ("", "")),
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
            trigger_modes=[model.TriggerMode.ABBREVIATION], ignore_case=True, match_case=True,
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
    if not phrase.check_input(trigger_str, ("", "")):
        pytest.xfail("match_case currently broken. See issue #197")
    # Expansion should always trigger
    assert_that(
        phrase.check_input(trigger_str, ("", "")),
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


def test_trigger_immediate():
    abbreviation = "xp@"  # Values taken from original unit tests
    phrase = create_phrase(abbreviation=abbreviation, content="expansion@autokey.com")
    phrase.immediate = True

    # Trigger on the first assigned abbreviation, don’t care about the actual abbreviation content
    # Test that the abbreviation triggers without the presence of a trigger character
    assert_that(phrase.check_input(phrase.abbreviations[0], ("", "")), is_(equal_to(True)))
    # Don’t trigger when there is a space after the typed abbreviation
    assert_that(phrase.check_input(phrase.abbreviations[0] + " ", ("", "")), is_(equal_to(False)))

    # Now test some results
    result = phrase.build_phrase(phrase.abbreviations[0])
    assert_that(result.string, is_(equal_to("expansion@autokey.com")))
    assert_that(result.backspaces, is_(equal_to(len(abbreviation))))
    assert_that(phrase.calculate_input(abbreviation), is_(equal_to(len(abbreviation))))


def generate_test_cases_for_undo_on_backspace():
    """Yields PhraseData, typed_input, undo_enabled, PhraseResult"""

    def phrase_data(trigger_immediately: bool) -> PhraseData:
        """Local helper function to save typing constant data"""
        return PhraseData(
            name="name", abbreviation="tri", content="ab br",
            trigger_modes=[model.TriggerMode.ABBREVIATION], ignore_case=False, match_case=False,
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

    result = phrase.build_phrase(trigger_str)
    assert_that(result.backspaces, is_(equal_to(phrase_result.backspace_count)))
