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
import os
import sys
from datetime import date

from unittest.mock import MagicMock, patch
import unittest.mock

import pytest
from hamcrest import *

import autokey.service
from autokey.service import PhraseRunner
from autokey.configmanager.configmanager import ConfigManager
import autokey.model
from autokey.scripting import Engine

from autokey.macro import *

def get_autokey_dir():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

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
    # service = autokey.service.Service(engine.configManager.app)
        engine.configManager.config_altered(False)

    return engine, test_folder


# For mocking dates. Usage:
    # @mock.patch('datetime.datetime', FakeDate)
    # def test():
    #     from datetime import datetime
    #     FakeDate.now = classmethod(lambda cls: now(2010, 1, 1))
    #     return date.now()
class FakeDate(date):
    "A manipulable date replacement"
    def __new__(cls, *args, **kwargs):
        return date.__new__(date, *args, **kwargs)


def expandMacro(engine, phrase):
    manager = MacroManager(engine)
    return manager.process_expansion_macros(phrase)

def test_arg_parse():
    engine, folder = create_engine()
    macro = ScriptMacro(engine)
    test = "name='test name' args='long arg with spaces and ='"
    expected = {"name": "test name", "args": "long arg with spaces and ="}
    assert_that(macro._get_args(test), is_(equal_to(expected)),
                "Macro arg can't contain equals")
    test = "name='test name' args='long arg with spaces and \"'"
    expected = {"name": "test name", "args": "long arg with spaces and \""}
    assert_that(macro._get_args(test), is_(equal_to(expected)),
                "Macro arg can't contain opposite quote")
    test = 'name="test name" args="long arg with spaces and \\""'
    expected = {"name": "test name", "args": 'long arg with spaces and "'}
    assert_that(macro._get_args(test), is_(equal_to(expected)),
                "Macro arg can't contain escaped quote quote")

@pytest.mark.skip(reason="For this to work, engine needs to be initialised with a PhraseRunner that isn't a mock. Sadly, that requires an app that isn't a mock.")
def test_script_macro():
    # Makes use of running script from absolute path.
    engine, folder = create_engine()
    with patch("autokey.model.Phrase.persist"), patch("autokey.model.Folder.persist"):
        dummy_folder = autokey.model.Folder("dummy")
        # This is a duplicate of the phrase added by the target script, but in a
        # different folder.
        dummy = engine.create_phrase(dummy_folder, "arg 1", "arg2", temporary=True)
        assert_that(folder.items, not_(has_item(dummy)))

        script = get_autokey_dir() + "/tests/create_single_phrase.py"
        test = "<script name='{}' args='arg 1',arg2>".format(script)

        expandMacro(engine, test)
        assert_that(folder.items, has_item(dummy))

def test_script_macro_spaced_quoted_args():
    pass

def test_cursor_macro():
    engine, folder = create_engine()
    test="one<cursor>two"
    expected="onetwo<left><left><left>"
    assert_that(expandMacro(engine, test), is_(equal_to(expected)),
                "cursor macro returns wrong text")


@unittest.mock.patch('datetime.datetime', FakeDate)
def test_date_macro():
    from datetime import datetime
    FakeDate.now = classmethod(lambda cls: datetime(2019, 1, 1))

    engine, folder = create_engine()
    test="<date format=%d/%m/%y>"
    expected="01/01/19"
    assert_that(expandMacro(engine, test), is_(equal_to(expected)),
                "Date macro fails to expand")

def test_file_macro():
    engine, folder = create_engine()
    path =  get_autokey_dir() + "/tests/dummy_file.txt"
    test="<file name={}>".format(path)
    expected="test result macro expansion\n"
    assert_that(expandMacro(engine, test), is_(equal_to(expected)),
                "file macro does not expand correctly")

def test_macro_expansion():
    engine, folder = create_engine()
    path =  get_autokey_dir() + "/tests/dummy_file.txt"
    contents="middle <file name={}> macro".format(path, path)
    expected="middle test result macro expansion\n macro".format(path, path)
    assert_that(expandMacro(engine, contents), is_(equal_to(expected)),
                "Macros between other parts don't expand properly")
    contents="<file name={}> two macros this time <file name={}>".format(path, path)
    expected="test result macro expansion\n two macros this time test result macro expansion\n".format(path, path)
    assert_that(expandMacro(engine, contents), is_(equal_to(expected)),
                "Two macros per phrase don't expand properly")
    contents="<file name={}> mixed macro <cursor> types".format(path)
    expected="test result macro expansion\n mixed macro  types<left><left><left><left><left><left>"
    assert_that(expandMacro(engine, contents), is_(equal_to(expected)),
                "mixed macros don't expand properly")

# def test_nested_macro_raises_error():
#     contents="<date format=<cursor>>"
#     # TODO
