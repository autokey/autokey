# Copyright (C) 2019 Thomas Hess <thomas.hess@udo.edu>

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

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *

import autokey.service
import autokey.model.key
from autokey.service import PhraseRunner
from autokey.model.phrase import Phrase


def _create_phrase_runner(phrase_content: str) -> PhraseRunner:
    mock_service = MagicMock()
    runner = PhraseRunner(mock_service)
    # Patch "execute" to remove the multithreading decorator. This will serialize the
    # phrase processing code. Without this patch, tests may fail due to asynchronous
    # phrase processing.
    with patch.object(runner, "execute", new=runner.execute._original):
        # Explicitly bind runner.execute._original as the bound method runner.execute,
        # because this is not automatically done in this case.
        setattr(runner, "execute", runner.execute._original.__get__(runner, PhraseRunner))
        runner.execute(_generate_phrase(phrase_content))

    return runner


def _generate_phrase(content: str) -> Phrase:
    """
    Generate a Phrase instance with the given content.
    """
    phrase = Phrase("description", content)
    # A Phrase needs a valid parent, because usage increases the parent’s usage count
    phrase.parent = MagicMock()
    return phrase


def generate_test_cases_for_test_can_undo_expansion():
    # Undo possible
    yield "", True
    yield "abc", True
    yield "<code>", True
    yield "abc<code>12", True
    yield "<code1A>", True
    # Undo impossible
    yield "<left>", False
    yield "<shift>+<left>", False
    yield "<code50>", False
    yield "abc<ALT>12", False
    yield "<Ctrl>", False
    yield "<abc<up>>", False
    for key in autokey.model.key.Key:
        yield key, False


@pytest.mark.parametrize("content, expected", generate_test_cases_for_test_can_undo_expansion())
def test_can_undo_expansion(content: str, expected: bool):
    # Setup
    runner = _create_phrase_runner(content)
    assert_that(
        runner.lastPhrase,
        is_(not_none()),
        "Test setup failed. The PhraseRunner holds no Phrase."
    )
    assert_that(
        runner.lastPhrase.phrase,
        is_(equal_to(content)),
        "Test setup failed. The PhraseRunner holds an unexpected Phrase."
    )
    # Test
    assert_that(
        runner.can_undo(),
        is_(equal_to(expected)),
        "can_undo() returned wrong result"
    )
