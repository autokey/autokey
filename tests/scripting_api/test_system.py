# Copyright (C) 2019 BlueDrink9 <https://github.com/BlueDrink9>

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
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *

from autokey.scripting import System

@pytest.mark.parametrize("command, expected, errormsg", [
    ["printf 'tree\\n'", "tree", "newline at end isn't trimmed"],
    ["printf 'tree'", "tree", "Commands without newline aren't returned properly"],
    ["true", "", "Empty command output causes issue."],  # GitHub issue #379
    ["printf ' '", " ", "Whitespace-only command output causes issue"],
    ["printf '\\n'", "", "Newline-only command output causes issue"],
])
def test_system_exec_command(command, expected, errormsg):
    assert_that(System.exec_command(command, getOutput=True), is_(expected), errormsg)


def test_system_exec_command_failure():
    command = "printf 'out'; exit 3"
    with pytest.raises(subprocess.CalledProcessError) as error:
        System.exec_command(command, getOutput=True)
    assert_that(error.value.returncode, is_(3))
    assert_that(error.value.cmd, is_(command))
    assert_that(error.value.output, is_("out"))
