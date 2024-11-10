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

import tests.helpers_for_tests as testhelpers
import autokey.model.folder
import autokey.service
from autokey.service import PhraseRunner
from autokey.configmanager.configmanager import ConfigManager
from autokey.scripting import Engine

from autokey.macro import *


path = testhelpers.get_autokey_test_dir() + "/dummy_file.txt"


def create_engine() -> typing.Tuple[Engine, autokey.model.folder.Folder]:
    # Make sure to not write to the hard disk
    test_folder = autokey.model.folder.Folder("Test folder")
    test_folder.persist = MagicMock()

    # Mock load_global_config to add the test folder to the known folders. This causes the ConfigManager to skip it’s
    # first-run logic.
    with patch("autokey.model.phrase.Phrase.persist"), patch("autokey.model.folder.Folder.persist"),\
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
    """A manipulable date replacement"""
    def __new__(cls, *args, **kwargs):
        return date.__new__(date, *args, **kwargs)


def expandMacro(engine, phrase):
    manager = MacroManager(engine)
    return manager.process_expansion_macros(phrase)


@pytest.mark.parametrize("test_input, expected, error_msg", [
    ("name='test name' args='long arg with spaces and ='", {"name": "test name", "args": "long arg with spaces and ="}, "Macro arg can't contain equals"),
    ("name='test name' args='long arg with spaces and \"'",
            {"name": "test name", "args": "long arg with spaces and \""},
                "Macro arg can't contain opposite quote"),
    ('name="test name" args="long arg with spaces and \\""',
            {"name": "test name", "args": 'long arg with spaces and "'},
                "Macro arg can't contain escaped quote quote"),
    ('name="test name" args="long arg with spaces and >"',
            {"name": "test name", "args": 'long arg with spaces and >'},
                "Macro arg can't contain > when handleg just by get_args"),
])
def test_arg_parse(test_input, expected, error_msg):
    engine, folder = create_engine()
    macro = ScriptMacro(engine)
    assert_that(macro._get_args(test_input), is_(equal_to(expected)),
                error_msg)


# Using date for this because it's the easiest macro with args to expand,
# without throwing errors on bad args.
@unittest.mock.patch('datetime.datetime', FakeDate)
@pytest.mark.parametrize("test, expected, error_msg", [
    (r"<date format=%m\>%y>", "01>19",
     r"Macro arg can't handle '\>'"),
    (r"<date format=%m\<%y>", "01<19",
     r"Macro arg can't handle '\<'"),
    (r"<date format=\<%m%y\>>", "<0119>",
     r"Macro arg can't handle being enclosed in angle brackets '\<arg\>'"),
    (r"before <date format=\<%m%y\>> macro",
     "before <0119> macro",
     "Macro arg in angle brackets breaks overall phrase splitting"),
    (r"before <date format=\<%m%y\>> between <date format=\<%m%y\>> macro",
     "before <0119> between <0119> macro",
     "Macro arg in angle brackets breaks overall phrase splitting with two macros"),
])
def test_arg_parse_with_escaped_gt_lt_symbols(test, expected, error_msg):
    from datetime import datetime
    FakeDate.now = classmethod(lambda cls: datetime(2019, 1, 1))
    engine, folder = create_engine()
    assert_that(expandMacro(engine, test), is_(equal_to(expected)),
                error_msg)


@unittest.mock.patch('datetime.datetime', FakeDate)
@pytest.mark.parametrize("test, expected, error_msg", [
    ("Today < is <date format=%m/%y>", "Today < is 01/19", "Phrase with extra < before macro breaks macros"),
    ("Today > is <date format=%m/%y>", "Today > is 01/19", "Phrase with extra > before macro breaks macros"),
    ("Today is <date format=%m/%y>, horray<", "Today is 01/19, horray<", "Phrase with extra < after macro breaks macros"),
    ("Today is <date format=%m/%y>, horray>", "Today is 01/19, horray>", "Phrase with extra > after macro breaks macros"),
    ("Today is <<date format=%m/%y>", "Today is <01/19", "Phrase with extra < right before macro breaks macros"),
    ("Today is <date format=%m/%y><", "Today is 01/19<", "Phrase with extra < right after macro breaks macros"),
    ("Today is <date format=%m/%y>>", "Today is 01/19>", "Phrase with extra > right after macro breaks macros"),
    ("Today <> is <date format=%m/%y>", "Today <> is 01/19", "Phrase with extra <> before macro breaks macros"),
    ("Today <is <date format=%m/%y>,>", "Today <is 01/19,>", "Phrase with extra <> loosely around macro breaks macros"),
    ("Today is <<date format=%m/%y>>", "Today is <01/19>", "Phrase with extra <> right around macro breaks macros"),
])
def test_phrase_with_gt_lt_symbols_and_macro(test, expected, error_msg):
    from datetime import datetime
    FakeDate.now = classmethod(lambda cls: datetime(2019, 1, 1))
    engine, folder = create_engine()
    assert_that(expandMacro(engine, test), is_(equal_to(expected)),
                error_msg)


@pytest.mark.skip(reason="For this to work, engine needs to be initialised with a PhraseRunner that isn't a mock. Sadly, that requires an app that isn't a mock.")
def test_script_macro():
    # Makes use of running script from absolute path.
    engine, folder = create_engine()
    with patch("autokey.model.phrase.Phrase.persist"), patch("autokey.model.folder.Folder.persist"):
        dummy_folder = autokey.model.folder.Folder("dummy")
        # This is a duplicate of the phrase added by the target script, but in a
        # different folder.
        dummy = engine.create_phrase(dummy_folder, "arg 1", "arg2", temporary=True)
        assert_that(folder.items, not_(has_item(dummy)))

        script = testhelpers.get_autokey_test_dir() + "/create_single_phrase.py"
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


@pytest.mark.parametrize("test_input, expected, error_msg", [
    ("<cursor><file name={}> types".format(path),
     "test result macro expansion\n types" + "<left>"*(28 + 6),
     "Cursor macro before another macro doesn't expand properly"),
    ("<cursor><file name={}> types".format(path),
     "test result macro expansion\n types" + "<left>"*(28 + 6),
     "Cursor macro before another macro doesn't expand properly"),
    ("<cursor><file name={}><file name={}> types".format(path, path),
     "test result macro expansion\ntest result macro expansion\n types" + "<left>"*(28 + 28 + 6),
     "Cursor macro before another 2 macros doesn't expand properly"),
    ("<file name={}><cursor><file name={}> types".format(path, path),
     "test result macro expansion\ntest result macro expansion\n types" + "<left>"*(28 + 6),
     "Cursor macro between another 2 macros doesn't expand properly"),
])
def test_cursor_before_another_macro(test_input, expected, error_msg):
    engine, folder = create_engine()
    assert_that(expandMacro(engine, test_input), is_(equal_to(expected)),
                error_msg)


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
    path =  testhelpers.get_autokey_test_dir() + "/dummy_file.txt"
    test="<file name={}>".format(path)
    expected="test result macro expansion\n"
    assert_that(expandMacro(engine, test), is_(equal_to(expected)),
                "file macro does not expand correctly")


@pytest.mark.parametrize("test_input, expected, error_msg", [
    ("No macro", "No macro",
            "Error on phrase without macros"),
    ("middle <file name={}> macro".format(path),
            "middle test result macro expansion\n macro",
            "Macros between other parts don't expand properly"),
    ("<file name={}> two macros this time <file name={}>".format(path, path),
            "test result macro expansion\n two macros this time test result macro expansion\n".format(path, path),
            "Two macros per phrase don't expand properly"),
    ("<file name={}> mixed macro <cursor> types".format(path),
        "test result macro expansion\n mixed macro  types<left><left><left><left><left><left>",
        "mixed macros don't expand properly")
])
def test_macro_expansion(test_input, expected, error_msg):
    engine, folder = create_engine()
    assert_that(expandMacro(engine, test_input), is_(equal_to(expected)), error_msg)


def test_system_macro():
    engine, folder = create_engine()
    lang=os.environ['LANG']
    test="one<system command='echo $LANG'>two"
    expected="one{}two".format(lang)
    assert_that(expandMacro(engine, test), is_(equal_to(expected)),
                "system macro fails")


# def test_nested_macro_raises_error():
#     contents="<date format=<cursor>>"
#     # TODO
