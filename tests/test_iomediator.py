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

import pytest
from hamcrest import *

import autokey.iomediator.constants as iomediator_constants
import autokey.model.key


def generate_tests_for_key_split_re():
    """Yields test_input_str, expected_split_list"""
    # Values taken from original test code
    yield "<ctrl>+y", ["", "<ctrl>+", "y"]
    yield "asdf <ctrl>+y asdf ", ["asdf ", "<ctrl>+", "y asdf "]
    yield "<table><ctrl>+y</table>", ["", "<table>", "", "<ctrl>+", "y", "</table>", ""]
    yield "<!<alt_gr>+8CDATA<alt_gr>+8", ["<!", "<alt_gr>+", "8CDATA", "<alt_gr>+", "8"]
    yield "<ctrl>y", ["", "<ctrl>", "y"]
    yield "Test<tab>More text", ["Test", "<tab>", "More text"]


@pytest.mark.parametrize("input_string, expected_split", generate_tests_for_key_split_re())
def test_key_split_re(input_string: str, expected_split: typing.List[str]):
    assert_that(
        autokey.model.key.KEY_SPLIT_RE.split(input_string),
        has_items(*expected_split)
    )
