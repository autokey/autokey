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
from unittest.mock import MagicMock, patch
import typing
import os
import pytest
from hamcrest import *

import autokey.model.folder
import autokey.service
from autokey.service import PhraseRunner
from autokey.configmanager.configmanager import ConfigManager
from autokey.scripting import Engine
from autokey.macro import *

def get_autokey_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

path = get_autokey_dir() + "/tests/dummy_file.txt"

def create_engine() -> typing.Tuple[Engine, autokey.model.folder.Folder]:
    test_folder = autokey.model.folder.Folder("Test folder")
    test_folder.persist = MagicMock()
    with patch("autokey.model.phrase.Phrase.persist"), patch("autokey.model.folder.Folder.persist"),\
         patch("autokey.configmanager.configmanager.ConfigManager.load_global_config",
               new=(lambda self: self.folders.append(test_folder))):
        engine = Engine(ConfigManager(MagicMock()), MagicMock(spec=PhraseRunner))
        engine.configManager.config_altered(False)
    return engine, test_folder

@pytest.mark.parametrize("test_input, expected, error_msg", [
    ("name='test name' args='long arg with spaces and ='", {"name": "test name", "args": "long arg with spaces and ="}, "Macro arg can't contain equals"),
    ("name='test name' args='long arg with spaces and \"'", {"name": "test name", "args": "long arg with spaces and \""}, "Macro arg can't contain opposite quote"),
    ('name="test name" args="long arg with spaces and \\""', {"name": "test name", "args": 'long arg with spaces and "'}, "Macro arg can't contain escaped quote quote"),
    ('name="test name" args="long arg with spaces and >"', {"name": "test name", "args": 'long arg with spaces and >'}, "Macro arg can't contain > when handleg just by get_args"),
])
def test_arg_parse(test_input, expected, error_msg):
    engine, folder = create_engine()
    macro = ScriptMacro(engine)
    assert_that(macro._get_args(test_input), is_(equal_to(expected)), error_msg)

@pytest.mark.parametrize("test, expected, error_msg", [
    (r"<date format=%m\>%y>", "01>19", r"Macro arg can't handle '\>'"),
    (r"<date format=%m\<%y>", "01<19", r"Macro arg can't handle '\<'"),
    (r"<date format=\<%m%y\>>", "<0119>", r"Macro arg can't handle being enclosed in angle brackets '\<arg\>'"),
    (r"before <date format=\<%m%y\>> macro", "before <0119> macro", "Macro arg in angle brackets breaks overall phrase splitting"),
    (r"before <date format=\<%m%y\>> between <date format=\<%m%y\>> macro", "before <0119> between <0119> macro", "Macro arg in angle brackets breaks overall phrase splitting with two macros"),
])
def test_arg_parse_with_escaped_gt_lt_symbols(test, expected, error_msg, mocker):
    from datetime import datetime
    mocker.patch('datetime.datetime', autospec=True)
    datetime.now.return_value = datetime(2019, 1, 1)
    engine, folder = create_engine()
    assert_that(expandMacro(engine, test), is_(equal_to(expected)), error_msg)

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
def test_phrase_with_gt_lt_symbols_and_macro(test, expected, error_msg, mocker):
    from datetime import datetime
    mocker.patch('datetime.datetime', autospec=True)
    datetime.now.return_value = datetime(2019, 1, 1)
    engine, folder = create_engine()
    assert_that(expandMacro(engine, test), is_(equal_to(expected)), error_msg)

def test_script_macro():
    engine, folder = create_engine()
    with patch("autokey.model.phrase.Phrase.persist"), patch("autokey.model.folder.Folder.persist"):
        dummy_folder = autokey.model.folder.Folder("dummy")
        dummy = engine.create_phrase(dummy_folder, "arg 1", "arg2", temporary=True)
        assert_that(folder.items, not_(has_item(dummy)))
        script = get_autokey_dir() + "/tests/create_single_phrase.py"
        test = "<script name='{}' args='arg 1',arg2>".format(script)
        expandMacro(engine, test)
        assert_that(folder.items, has_item(dummy))

def test_cursor_macro():
    engine, folder = create_engine()
    test="one<cursor>two"
    expected="onetwo<left><left><left>"
    assert_that(expandMacro(engine, test), is_(equal_to(expected)), "cursor macro returns wrong text")

@pytest.mark.parametrize("test_input, expected, error_msg", [
    ("<cursor><file name={}> types".format(path), "test result macro expansion\n types" + "<left>"*(28 + 6), "Cursor macro before another macro doesn't expand properly"),
    ("<cursor><file name={}><file name={}> types".format(path, path), "test result macro expansion\ntest result macro expansion\n types" + "<left>"*(28 + 28 + 6), "Cursor macro before another 2 macros doesn't expand properly"),
    ("<file name={}><cursor><file name={}> types".format(path, path), "test result macro expansion\ntest result macro expansion\n types" + "<left>"*(28 + 6), "Cursor macro between another 2 macros doesn't expand properly"),
])
def test_cursor_before_another_macro(test_input, expected, error_msg):
    engine, folder = create_engine()
    assert_that(expandMacro(engine, test_input), is_(equal_to(expected)), error_msg)

def test_date_macro(mocker):
    from datetime import datetime
    mocker.patch('datetime.datetime', autospec=True)
    datetime.now.return_value = datetime(2019, 1, 1)
    engine, folder = create_engine()
    test="<date format=%d/%m/%y>"
    expected="01/01/19"
    assert_that(expandMacro(engine, test), is_(equal_to(expected)), "Date macro fails to expand")

@pytest.mark.parametrize("test_input, expected, error_msg", [
    ("No macro", "No macro", "Error on phrase without macros"),
    ("middle <file name={}> macro".format(path), "middle test result macro expansion\n macro", "Macros between other parts don't expand properly"),
    ("<file name={}> two macros this time <file name={}>".format(path, path), "test result macro expansion\n two macros this time test result macro expansion\n".format(path, path), "Two macros per phrase don't expand properly"),
    ("<file name={}> mixed macro <cursor> types".format(path), "test result macro expansion\n mixed macro  types<left><left><left><left><left><left>", "mixed macros don't expand properly")
])
def test_macro_expansion(test_input, expected, error_msg):
    engine, folder = create_engine()
    assert_that(expandMacro(engine, test_input), is_(equal_to(expected)), error_msg)

def test_system_macro():
    engine, folder = create_engine()
    lang=os.environ['LANG']
    test="one<system command='echo $LANG'>two"
    expected="one{}two".format(lang)
    assert_that(expandMacro(engine, test), is_(equal_to(expected)), "system macro fails")
