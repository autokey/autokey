# Copyright (C) 2021 BlueDrink9
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This file contains pytest fixtures that are automatically available to all tests.
# https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
#
# This means autouse fixtures declared here will be used for every test in this
# module.

import pytest
from unittest.mock import MagicMock, patch

# When testing, do not touch the user's config.
# All tests should be run on a freshly-generated default config in a pytest tmpdir.
@pytest.fixture(autouse=True)
def mock_settings_env_vars(tmpdir):
    with \
         patch("autokey.common.CONFIG_DIR", str(tmpdir)), \
         patch("autokey.configmanager.configmanager_constants.CONFIG_DEFAULT_FOLDER", str(tmpdir) + "/config.json"), \
            patch("autokey.configmanager.configmanager_constants.CONFIG_DEFAULT_FOLDER", str(tmpdir)):
        yield

