# Copyright (C) 2020 BlueDrink9

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

import subprocess

import pytest
from hamcrest import *

import autokey.model as m
import autokey.model.abstract_hotkey as ab_hk

@pytest.mark.parametrize("key, modifiers, expected", [
    ["t", ["<ctrl>"], "<ctrl>+t"],
    ["t", [], "t"],
    ["a", ["<alt>", "<shift>"], "<alt>+<shift>+a"],
    ])
def test_build_hotkey_string(key, modifiers, expected):
    out = ab_hk.AbstractHotkey.build_hotkey_string(modifiers, key)
    assert_that(out, is_(equal_to(expected)))


