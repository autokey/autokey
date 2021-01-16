# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2019-2020 Thomas Hess <thomas.hess@udo.edu>
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

import errno
import glob
import json
import os
import typing

from autokey.configmanager import configmanager_constants as cm_constants
from autokey.model.phrase import Phrase
from autokey.model.script import Script
from autokey.model.helpers import get_safe_path, TriggerMode
from autokey.model.abstract_abbreviation import AbstractAbbreviation
from autokey.model.abstract_window_filter import AbstractWindowFilter
from autokey.model.abstract_hotkey import AbstractHotkey


logger = __import__("autokey.logger").logger.get_logger(__name__)


class Folder(AbstractAbbreviation, AbstractHotkey, AbstractWindowFilter):
    """
    Manages a collection of subfolders/phrases/scripts, which may be associated
    with an abbreviation or hotkey.
    """

    def __init__(self, title: str, show_in_tray_menu: bool=False, path: str=None):
        AbstractAbbreviation.__init__(self)
        AbstractHotkey.__init__(self)
        AbstractWindowFilter.__init__(self)
        self.title = title
        self.folders = []
        self.items = []
        self.modes = []  # type: typing.List[TriggerMode]
        self.usageCount = 0
        self.show_in_tray_menu = show_in_tray_menu
        self.parent = None  # type: typing.Optional[Folder]
        self.path = path
        self.temporary = False

    def build_path(self, base_name=None):
        if base_name is None:
            base_name = self.title

        if self.parent is not None:
            self.path = get_safe_path(self.parent.path, base_name)
        else:
            self.path = get_safe_path(cm_constants.CONFIG_DEFAULT_FOLDER, base_name)

    def persist(self):
        if self.path is None:
            self.build_path()

        if not os.path.exists(self.path):
            os.mkdir(self.path)

        with open(self.path + "/folder.json", 'w') as outFile:
            json.dump(self.get_serializable(), outFile, indent=4)

    def get_serializable(self):
        d = {
            "type": "folder",
            "title": self.title,
            "modes": [mode.value for mode in self.modes],  # Store the enum value for compatibility with old user data.
            "usageCount": self.usageCount,
            "showInTrayMenu": self.show_in_tray_menu,
            "abbreviation": AbstractAbbreviation.get_serializable(self),
            "hotkey": AbstractHotkey.get_serializable(self),
            "filter": AbstractWindowFilter.get_serializable(self),
            }
        return d

    def load(self, parent=None):
        self.parent = parent

        if os.path.exists(self.get_json_path()):
            self.load_from_serialized()
        else:
            self.title = os.path.basename(self.path)

        self.load_children()

    def load_children(self):
        entries = glob.glob(self.path + "/*")
        self.folders = []
        self.items = []

        for entryPath in entries:
            #entryPath = self.path + '/' + entry
            if os.path.isdir(entryPath):
                f = Folder("", path=entryPath)
                f.load(self)
                self.folders.append(f)

            if os.path.isfile(entryPath):
                i = None
                if entryPath.endswith(".txt"):
                    i = Phrase("", "", path=entryPath)
                elif entryPath.endswith(".py"):
                    i = Script("", "", path=entryPath)

                if i is not None:
                    i.load(self)
                    self.items.append(i)

    def load_from_serialized(self):
        try:
            with open(self.path + "/folder.json", 'r') as inFile:
                data = json.load(inFile)
                self.inject_json_data(data)
        except Exception:
            logger.exception("Error while loading json data for " + self.title)
            logger.error("JSON data not loaded (or loaded incomplete)")

    def inject_json_data(self, data):
        self.title = data["title"]

        self.modes = [TriggerMode(item) for item in data["modes"]]
        self.usageCount = data["usageCount"]
        self.show_in_tray_menu = data["showInTrayMenu"]

        AbstractAbbreviation.load_from_serialized(self, data["abbreviation"])
        AbstractHotkey.load_from_serialized(self, data["hotkey"])
        AbstractWindowFilter.load_from_serialized(self, data["filter"])

    def rebuild_path(self):
        if self.path is not None:
            oldName = self.path
            self.path = get_safe_path(os.path.split(oldName)[0], self.title)
            self.update_children()
            os.rename(oldName, self.path)
        else:
            self.build_path()

    def update_children(self):
        for childFolder in self.folders:
            childFolder.build_path(os.path.basename(childFolder.path))
            childFolder.update_children()

        for childItem in self.items:
            childItem.build_path(os.path.basename(childItem.path))

    def remove_data(self):
        if self.path is not None:
            for child in self.items:
                child.remove_data()
            for child in self.folders:
                child.remove_data()
            try:
                # The json file must be removed first. Otherwise the rmdir will fail.
                if os.path.exists(self.get_json_path()):
                    os.remove(self.get_json_path())
                os.rmdir(self.path)
            except OSError as err:
                # There may be user data in the removed directory. Only swallow the error, if it is caused by
                # residing user data. Other errors should propagate.
                if err.errno != errno.ENOTEMPTY:
                    raise

    def get_json_path(self):
        return self.path + "/folder.json"

    def get_tuple(self):
        return "folder", self.title, self.get_abbreviations(), self.get_hotkey_string(), self

    def set_modes(self, modes: typing.List[TriggerMode]):
        self.modes = modes

    def add_folder(self, folder):
        folder.parent = self
        #self.folders[folder.title] = folder
        self.folders.append(folder)

    def remove_folder(self, folder):
        #del self.folders[folder.title]
        self.folders.remove(folder)

    def add_item(self, item):
        """
        Add a new script or phrase to the folder.
        """
        item.parent = self
        #self.phrases[phrase.description] = phrase
        self.items.append(item)

    def remove_item(self, item):
        """
        Removes the given phrase or script from the folder.
        """
        #del self.phrases[phrase.description]
        self.items.remove(item)

    def check_input(self, buffer, window_info):
        if TriggerMode.ABBREVIATION in self.modes:
            return self._should_trigger_abbreviation(buffer) and self._should_trigger_window_title(window_info)
        else:
            return False

    def increment_usage_count(self):
        self.usageCount += 1
        if self.parent is not None:
            self.parent.increment_usage_count()

    def get_backspace_count(self, buffer):
        """
        Given the input buffer, calculate how many backspaces are needed to erase the text
        that triggered this folder.
        """
        if TriggerMode.ABBREVIATION in self.modes and self.backspace:
            if self._should_trigger_abbreviation(buffer):
                abbr = self._get_trigger_abbreviation(buffer)
                stringBefore, typedAbbr, stringAfter = self._partition_input(buffer, abbr)
                return len(abbr) + len(stringAfter)

        if self.parent is not None:
            return self.parent.get_backspace_count(buffer)

        return 0

    def calculate_input(self, buffer):
        """
        Calculate how many keystrokes were used in triggering this folder (if applicable).
        """
        if TriggerMode.ABBREVIATION in self.modes and self.backspace:
            if self._should_trigger_abbreviation(buffer):
                if self.immediate:
                    return len(self._get_trigger_abbreviation(buffer))
                else:
                    return len(self._get_trigger_abbreviation(buffer)) + 1

        if self.parent is not None:
            return self.parent.calculate_input(buffer)

        return 0

    """def __cmp__(self, other):
        if self.usageCount != other.usageCount:
            return cmp(self.usageCount, other.usageCount)
        else:
            return cmp(other.title, self.title)"""

    def __str__(self):
        return "folder '{}'".format(self.title)

    def __repr__(self):
        return str(self)
