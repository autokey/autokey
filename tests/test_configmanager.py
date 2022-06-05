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
import sys
import os

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *
from tests.engine_helpers import *

import autokey.model.folder as akfolder
from autokey.configmanager.configmanager import ConfigManager
from autokey.configmanager.configmanager_constants import CONFIG_DEFAULT_FOLDER
import autokey.configmanager.predefined_user_files
from autokey.service import PhraseRunner
import autokey.service
from autokey.scripting import Engine

# These tests currently use the scripting API to create test phrases.
# If we can do it a better way, we probably should, to reduce dependencies for
# these tests.

def get_autokey_dir():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def test_get_item_with_hotkey(create_engine):
    engine, folder = create_engine
    # --- Setup ---
    modifiers = ["<ctrl>", "<alt>", "<super>", "<shift>"]
    key = "a"
    hotkey=(modifiers, key)
    testHK = create_test_hotkey(engine, folder, hotkey)
    resultHK = engine.configManager.get_item_with_hotkey(modifiers,
                                                         key, None)
    assert_that(resultHK, is_(equal_to(testHK)))

# TODO: check multiple folders, and global/special hotkeys.
# Check for similar tests in test_engine.
def test_item_has_same_hotkey(create_engine):
    engine, folder = create_engine
    modifiers = ["<ctrl>", "<alt>", "<super>", "<shift>"]
    key = "a"
    hotkey=(modifiers, key)
    testHK = create_test_hotkey(engine, folder, hotkey)
    assert ConfigManager.item_has_same_hotkey(testHK, modifiers, key, None)

def test_get_all_folders(create_engine):
    engine, folder = create_engine
    cm = engine.configManager

    first_child = akfolder.Folder("first child")
    first_grandchild = akfolder.Folder("first grandchild")
    second_grandchild = akfolder.Folder("second grandchild")
    first_child.add_folder(first_grandchild)
    first_child.add_folder(second_grandchild)
    cm.folders.append(first_child)

    expected = [folder, first_child, first_grandchild, second_grandchild]
    result = cm.get_all_folders()

    assert_that(result, equal_to(expected))

def test_create_predefined_user_files_my_phrases_folder(create_engine):
    engine, folder = create_engine
    # --- Setup ---
    os.makedirs(CONFIG_DEFAULT_FOLDER, exist_ok=True)
    phrases_folder = autokey.configmanager.predefined_user_files.create_my_phrases_folder()
    scripts_folder = autokey.configmanager.predefined_user_files.create_sample_scripts_folder()
