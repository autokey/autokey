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

import autokey.common

# Ensure that the version number is up to date in common.py
# Skip this test if the tag contains "CI_test"
@pytest.mark.skipif("CI_test" in subprocess.run(["git", "describe", "--abbrev=0" "--tags"])
def test_version_number_accurate():
    git_tag_version = subprocess.run(["git", "describe", "--abbrev=0",
        "--tags", '--match "v*.*.*"'],
        stdout=subprocess.PIPE).stdout.decode().rstrip()
    assert_that(git_tag_version, is_(equal_to("v"+autokey.common.VERSION)),
    "Ensure the most recent git tag version matches the version number in lib/autokey/common.py")

