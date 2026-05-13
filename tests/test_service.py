# Copyright (C) 2021 BlueDrink9
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

import inspect
import json
import typing
import sys
import os

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *
from tests.engine_helpers import *
import tests.helpers_for_tests as testhelpers

import autokey.model.folder
import autokey.model.helpers
import autokey.model.script
from autokey.configmanager import configmanager
from autokey.configmanager.configmanager import ConfigManager
from autokey.service import Service
from autokey.service import PhraseRunner
from autokey.service import ScriptRunner
import autokey.service
from autokey.scripting import Engine

confman_module_path = "autokey.configmanager.configmanager"
# These tests currently use the scripting API to create test phrases.
# If we can do it a better way, we probably should, to reduce dependencies for
# these tests.

def mock_configmanager(tmp_path):
    backup = str(tmp_path / "autokey.json~")
    config = str(testhelpers.make_dummy_config(tmp_path))
    with \
            patch(confman_module_path + ".CONFIG_DEFAULT_FOLDER",
                  str(tmp_path)), \
            patch(confman_module_path + ".CONFIG_FILE",
                  config), \
            patch(confman_module_path + ".CONFIG_FILE_BACKUP",
                  backup):
        return ConfigManager(MagicMock())


def test_start(tmp_path):
    cm = mock_configmanager(tmp_path)
    app = MagicMock()
    app.configManager = cm
    s = Service(app)
    s.start()
    s.shutdown()


def create_script(abbreviation, trigger_immediately=False, ignore_case=False):
    script = autokey.model.script.Script("script", "")
    script.add_abbreviation(abbreviation)
    script.set_modes([autokey.model.helpers.TriggerMode.ABBREVIATION])
    script.immediate = trigger_immediately
    script.ignoreCase = ignore_case
    script.parent = MagicMock()
    return script


@pytest.mark.parametrize("buffer, abbreviation, immediate, ignore_case, expected", [
    ("abbr ", "abbr", False, False, ("abbr", " ")),
    ("prefix abbr ", "abbr", False, False, ("abbr", " ")),
    ("abbr", "abbr", True, False, ("abbr", "")),
    ("ABBR", "abbr", True, True, ("ABBR", "")),
])
def test_set_triggered_abbreviation_uses_typed_abbreviation(
        buffer, abbreviation, immediate, ignore_case, expected):
    script = create_script(abbreviation, immediate, ignore_case)
    _, trigger_character = script.process_buffer(buffer)
    engine = MagicMock()

    ScriptRunner._set_triggered_abbreviation({"engine": engine}, script, buffer, trigger_character)

    engine._set_triggered_abbreviation.assert_called_once_with(*expected)
