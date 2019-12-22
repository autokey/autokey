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

import typing
import pathlib

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *

import autokey.service
from autokey.service import PhraseRunner
from autokey.configmanager.configmanager import ConfigManager
import autokey.model
from autokey.scripting import Engine

from autokey.macro import *


def create_engine() -> typing.Tuple[Engine, autokey.model.Folder]:
    # Make sure to not write to the hard disk
    test_folder = autokey.model.Folder("Test folder")
    test_folder.persist = MagicMock()

    # Mock load_global_config to add the test folder to the known folders. This causes the ConfigManager to skip it’s
    # first-run logic.
    with patch("autokey.model.Phrase.persist"), patch("autokey.model.Folder.persist"),\
         patch("autokey.configmanager.configmanager.ConfigManager.load_global_config",
               new=(lambda self: self.folders.append(test_folder))):
        engine = Engine(ConfigManager(MagicMock()), MagicMock(spec=PhraseRunner))
        engine.configManager.config_altered(False)

    return engine, test_folder

def test_arg_parse():
    engine, folder = create_engine()
    macro = ScriptMacro(engine)
    test = "<script name='test name' args='long arg with spaces and ='>"
    expected = {"name": "test name", "args": "long arg with spaces and ="}
    assert_that(macro._get_args(test), is_(equal_to(expected)),
                "Macro arg can't contain equals")
    test = "<script name='test name' args='long arg with spaces and \"'>"
    expected = {"name": "test name", "args": "long arg with spaces and \""}
    assert_that(macro._get_args(test), is_(equal_to(expected)),
                "Macro arg can't contain opposite quote")
    test = '<script name="test name" args="long arg with spaces and \\"">'
    expected = {"name": "test name", "args": 'long arg with spaces and "'}
    assert_that(macro._get_args(test), is_(equal_to(expected)),
                "Macro arg can't contain escaped quote quote")

def test_script_macro():
    pass

def test_script_macro_spaced_quoted_args():
    pass

def test_cursor_macro():
    pass

def test_date_macro():
    macro="<date format=dd>"
    pass

def test_file_macro():
    pass

