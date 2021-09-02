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
import unittest
from hamcrest import *

import autokey.iomediator.constants as iomediator_constants
from autokey.iomediator.iomediator import IoMediator
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


class MockInterface():
    def __init__(self):
        self.received = []
        self.modifiers = []

    def get_result(self):
        return "|".join(self.received)
    def get_modifiers(self):
        return self.modifiers

    def send_modified_key(self, string, mods):
        self.received.append("+".join(mods))
        self.modifiers.append(mods)
        self.received.append(string)

    def send_key(self, key):
        self.received.append(key)

    def send_string(self, s):
        self.received.append(s)





@pytest.mark.parametrize("inpt, failmsg", [
    ["hello this string is a test", "iomediator doesn't send a normal string properly"],
    ["", "iomediator doesn't send a blank string properly"],
    ["---", "iomediator doesn't send all dashes properly"],
    ["- -", "iomediator doesn't send this properly"],
])
def test_send_string(inpt: str, failmsg):
    interface = unittest.mock.Mock(wraps=MockInterface())
    IoMediator._send_string(inpt, interface)
    assert_that(
        interface.get_result(),
        is_(equal_to(inpt)),
        failmsg
    )


@pytest.mark.parametrize("inpt, result, mods, failmsg", [
    ["i want <ctrl>+a", "i want |<ctrl>|a", [["<ctrl>"]], "iomediator doesn't send a modified string properly"],
    ["i want <ctrl>+a and <alt>+<super>+t", "i want |<ctrl>|a| and |<alt>+<super>|t", [["<ctrl>"], ["<alt>", "<super>"]], "iomediator doesn't send a modified string properly"],
])
def test_send_string_modified(inpt: str, result: typing.List[str], mods: typing.List[str], failmsg):
    interface = unittest.mock.Mock(wraps=MockInterface())
    IoMediator._send_string(inpt, interface)
    assert_that(
        interface.get_result(),
        is_(equal_to(result)),
        failmsg
    )
    assert_that(
        interface.get_modifiers(),
        is_(equal_to(mods)),
        failmsg
    )
