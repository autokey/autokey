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

import typing
import string
import random

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *

import autokey.model.folder
from autokey.configmanager.configmanager import ConfigManager
from autokey.service import PhraseRunner
import autokey.service
from autokey.scripting import Engine

# For use in paramerizations.
# Call replace_folder_in_args(folder, args) to use.
folder_param="create_new_folder"

@pytest.fixture
def create_engine() -> typing.Tuple[Engine, autokey.model.folder.Folder]:
    # Make sure to not write to the hard disk
    test_folder = autokey.model.folder.Folder("Test folder")
    test_folder.persist = MagicMock()

    # Mock load_global_config to add the test folder to the known folders. This causes the ConfigManager to skip its
    # first-run logic.
    with patch("autokey.model.phrase.Phrase.persist"), patch("autokey.model.folder.Folder.persist"),\
         patch("autokey.configmanager.configmanager.ConfigManager.load_global_config",
               new=(lambda self: self.folders.append(test_folder))):
        engine = Engine(ConfigManager(MagicMock()), MagicMock(spec=PhraseRunner))
        engine.configManager.config_altered(False)

    return engine, test_folder


def create_random_string(length=10):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in
        range(length)])


def replace_folder_param_in_args(folder, args):
    if isinstance(args, str):
        return args
    args = [folder if x == folder_param else x for x in args]
    return args

def get_item_with_hotkey(engine, hotkey):
    modifiers = sorted(hotkey[0])
    item = engine.configManager.get_item_with_hotkey(modifiers, hotkey[1])
    return item

def assert_both_phrases_with_hotkey_exist(engine, p1, p2, hotkey):
    phrases = [p1, p2]
    for _ in phrases:
        phrase=get_item_with_hotkey(engine, hotkey)
        assert phrase in phrases
        # assert_that(phrase, is_(p1 or p2))
        # Remove hotkey from that phrase, so that the next check should
        # return the other phrase that had that hotkey.
        phrase.unset_hotkey()
        phrases.remove(phrase)

def create_test_hotkey(engine, folder, hotkey, replaceExisting=False,
                       windowFilter=None):
    with patch("autokey.model.phrase.Phrase.persist"):
        return engine.create_phrase(folder,
                create_random_string(),
                "ABC",
                hotkey=hotkey,
                replace_existing_hotkey=replaceExisting,
                window_filter=windowFilter,
                )
