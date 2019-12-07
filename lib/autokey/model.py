# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
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
import re
import os
import os.path
import glob
import logging
import json
import typing
import enum

from autokey import configmanager as cm
from autokey.iomediator.key import Key, NAVIGATION_KEYS
from autokey.iomediator.constants import KEY_SPLIT_RE
from autokey.scripting_Store import Store

_logger = logging.getLogger("model")

DEFAULT_WORDCHAR_REGEX = '[\w]'

JSON_FILE_PATTERN = "{}/.{}.json"
SPACES_RE = re.compile(r"^ | $")


def make_wordchar_re(word_chars: str):
    return "[^{word_chars}]".format(word_chars=word_chars)


def extract_wordchars(regex):
    return regex[2:-1]


def get_safe_path(base_path, name, ext=""):
    name = SPACES_RE.sub('_', name)
    safe_name = ''.join((char for char in name if char.isalnum() or char in "_ -."))

    if safe_name == '':
        path = base_path + '/1' + ext
        jsonPath = base_path + "/.1.json"
        n = 2
    else:
        path = base_path + '/' + safe_name + ext
        jsonPath = base_path + '/.' + safe_name + ".json"
        n = 1

    while os.path.exists(path) or os.path.exists(jsonPath):
        path = base_path + '/' + safe_name + str(n) + ext
        jsonPath = base_path + '/.' + safe_name + str(n) + ".json"
        n += 1

    return path


@enum.unique
class TriggerMode(enum.Enum):
    """
    Enumeration class for phrase match modes.

    NONE: Don't trigger this phrase (phrase will only be shown in its folder).
    ABBREVIATION: Trigger this phrase using an abbreviation.
    PREDICTIVE: Trigger this phrase using predictive mode.
    """
    NONE = 0
    ABBREVIATION = 1
    PREDICTIVE = 2
    HOTKEY = 3


class SendMode(enum.Enum):
    """
    Enumeration class for phrase send modes

    KEYBOARD: Send using key events
    CB_CTRL_V: Send via clipboard and paste with Ctrl+v
    CB_CTRL_SHIFT_V: Send via clipboard and paste with Ctrl+Shift+v
    SELECTION: Send via X selection and paste with middle mouse button
    """
    KEYBOARD = "kb"
    CB_CTRL_V = Key.CONTROL + "+v"
    CB_CTRL_SHIFT_V = Key.CONTROL + "+" + Key.SHIFT + "+v"
    CB_SHIFT_INSERT = Key.SHIFT + "+" + Key.INSERT
    SELECTION = None


SEND_MODES = {
    "Keyboard": SendMode.KEYBOARD,
    "Clipboard (Ctrl+V)": SendMode.CB_CTRL_V,
    "Clipboard (Ctrl+Shift+V)": SendMode.CB_CTRL_SHIFT_V,
    "Clipboard (Shift+Insert)": SendMode.CB_SHIFT_INSERT,
    "Mouse Selection": SendMode.SELECTION
}  # type: typing.Dict[str, SendMode]


class AbstractAbbreviation:
    """
    Abstract class encapsulating the common functionality of an abbreviation list
    """

    def __init__(self):
        self.abbreviations = []  # type: typing.List[str]
        self.backspace = True
        self.ignoreCase = False
        self.immediate = False
        self.triggerInside = False
        self.set_word_chars(DEFAULT_WORDCHAR_REGEX)

    def get_serializable(self):
        d = {
            "abbreviations": self.abbreviations,
            "backspace": self.backspace,
            "ignoreCase": self.ignoreCase,
            "immediate": self.immediate,
            "triggerInside": self.triggerInside,
            "wordChars": self.get_word_chars()
            }
        return d

    def load_from_serialized(self, data: dict):
        if "abbreviations" not in data: # check for pre v0.80.4
            self.abbreviations = [data["abbreviation"]]  # type: typing.List[str]
        else:
            self.abbreviations = data["abbreviations"]  # type: typing.List[str]

        self.backspace = data["backspace"]
        self.ignoreCase = data["ignoreCase"]
        self.immediate = data["immediate"]
        self.triggerInside = data["triggerInside"]
        self.set_word_chars(data["wordChars"])

    def copy_abbreviation(self, abbr  # type: Item
                          ):
        self.abbreviations = abbr.abbreviations
        self.backspace = abbr.backspace
        self.ignoreCase = abbr.ignoreCase
        self.immediate = abbr.immediate
        self.triggerInside = abbr.triggerInside
        self.set_word_chars(abbr.get_word_chars())

    def set_word_chars(self, regex):
        self.wordChars = re.compile(regex, re.UNICODE)

    def get_word_chars(self):
        return self.wordChars.pattern

    def add_abbreviation(self, abbr):
        self.abbreviations.append(abbr)

    def clear_abbreviations(self):
        self.abbreviations = []

    def get_abbreviations(self):
        if TriggerMode.ABBREVIATION not in self.modes:
            return ""
        elif len(self.abbreviations) == 1:
            return self.abbreviations[0]
        else:
            return "[" + ",".join(self.abbreviations) + "]"

    def _should_trigger_abbreviation(self, buffer):
        """
        Checks whether, based on the settings for the abbreviation and the given input,
        the abbreviation should trigger.

        @param buffer Input buffer to be checked (as string)
        """
        return any(self.__checkInput(buffer, abbr) for abbr in self.abbreviations)

    def _get_trigger_abbreviation(self, buffer):
        for abbr in self.abbreviations:
            if self.__checkInput(buffer, abbr):
                return abbr

        return None

    def __checkInput(self, buffer, abbr):
        stringBefore, typedAbbr, stringAfter = self._partition_input(buffer, abbr)
        if len(typedAbbr) > 0:
            # Check trigger character condition
            if not self.immediate:
                # If not immediate expansion, check last character
                if len(stringAfter) == 1:
                    # Have a character after abbr
                    if self.wordChars.match(stringAfter):
                        # last character(s) is a word char, can't send expansion
                        return False
                    elif len(stringAfter) > 1:
                        # Abbr not at/near end of buffer any more, can't send
                        return False
                else:
                    # Nothing after abbr yet, can't expand yet
                    return False

            else:
                # immediate option enabled, check abbr is at end of buffer
                if len(stringAfter) > 0:
                    return False

            # Check chars ahead of abbr
            # length of stringBefore should always be > 0
            if len(stringBefore) > 0 and not re.match('(^\s)', stringBefore[-1]) and not self.triggerInside:
                # check if last char before the typed abbreviation is a word char
                # if triggerInside is not set, can't trigger when inside a word
                return False

            return True

        return False

    def _partition_input(self, current_string: str, abbr: typing.Optional[str]) -> typing.Tuple[str, str, str]:
        """
        Partition the input into text before, typed abbreviation (if it exists), and text after
        """
        if abbr:
            if self.ignoreCase:
                string_before, typed_abbreviation, string_after = self._case_insensitive_rpartition(
                    current_string, abbr
                )
                abbr_start_index = len(string_before)
                abbr_end_index = abbr_start_index + len(typed_abbreviation)
                typed_abbreviation = current_string[abbr_start_index:abbr_end_index]
            else:
                string_before, typed_abbreviation, string_after = current_string.rpartition(abbr)

            return string_before, typed_abbreviation, string_after
        else:
            # abbr is None. This happens if the phrase was typed/pasted using a hotkey and is about to be un-done.
            # In this case, there is no trigger character (thus empty before and after text). The complete string
            # should be undone.
            return "", current_string, ""

    @staticmethod
    def _case_insensitive_rpartition(input_string: str, separator: str) -> typing.Tuple[str, str, str]:
        """Same as str.rpartition(), except that the partitioning is done case insensitive."""
        lowered_input_string = input_string.lower()
        lowered_separator = separator.lower()
        try:
            split_index = lowered_input_string.rindex(lowered_separator)
        except ValueError:
            # Did not find the separator in the input_string.
            # Follow https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str
            # str.rpartition documentation and return the tuple ("", "", unmodified_input) in this case
            return "", "", input_string
        else:
            split_index_2 = split_index+len(separator)
            return input_string[:split_index], input_string[split_index: split_index_2], input_string[split_index_2:]


class AbstractWindowFilter:

    def __init__(self):
        self.windowInfoRegex = None
        self.isRecursive = False

    def get_serializable(self):
        if self.windowInfoRegex is not None:
            return {"regex": self.windowInfoRegex.pattern, "isRecursive": self.isRecursive}
        else:
            return {"regex": None, "isRecursive": False}

    def load_from_serialized(self, data):
        if isinstance(data, dict): # check needed for data from versions < 0.80.4
            self.set_window_titles(data["regex"])
            self.isRecursive = data["isRecursive"]
        else:
            self.set_window_titles(data)

    def copy_window_filter(self, window_filter):
        self.windowInfoRegex = window_filter.windowInfoRegex
        self.isRecursive = window_filter.isRecursive

    def set_window_titles(self, regex):
        if regex is not None:
            self.windowInfoRegex = re.compile(regex, re.UNICODE)
        else:
            self.windowInfoRegex = regex

    def set_filter_recursive(self, recurse):
        self.isRecursive = recurse

    def has_filter(self) -> bool:
        return self.windowInfoRegex is not None

    def inherits_filter(self) -> bool:
        if self.parent is not None:
            return self.parent.get_applicable_regex(True) is not None

        return False

    def get_child_filter(self):
        if self.isRecursive and self.windowInfoRegex is not None:
            return self.get_filter_regex()
        elif self.parent is not None:
            return self.parent.get_child_filter()
        else:
            return ""

    def get_filter_regex(self):
        """
        Used by the GUI to obtain human-readable version of the filter
        """
        if self.windowInfoRegex is not None:
            if self.isRecursive:
                return self.windowInfoRegex.pattern
            else:
                return self.windowInfoRegex.pattern
        elif self.parent is not None:
            return self.parent.get_child_filter()
        else:
            return ""

    def filter_matches(self, otherFilter):
        if otherFilter is None or self.get_applicable_regex() is None:
            return True

        return otherFilter == self.get_applicable_regex().pattern

    def get_applicable_regex(self, forChild=False):
        if self.windowInfoRegex is not None:
            if (forChild and self.isRecursive) or not forChild:
                return self.windowInfoRegex
        elif self.parent is not None:
            return self.parent.get_applicable_regex(True)

        return None

    def _should_trigger_window_title(self, window_info):
        r = self.get_applicable_regex()  # type: typing.Pattern
        if r is not None:
            return bool(r.match(window_info.wm_title)) or bool(r.match(window_info.wm_class))
        else:
            return True


class AbstractHotkey(AbstractWindowFilter):

    def __init__(self):
        self.modifiers = []
        self.hotKey = None

    def get_serializable(self):
        d = {
            "modifiers": self.modifiers,
            "hotKey": self.hotKey
            }
        return d

    def load_from_serialized(self, data):
        self.set_hotkey(data["modifiers"], data["hotKey"])

    def copy_hotkey(self, theHotkey):
        [self.modifiers.append(modifier) for modifier in theHotkey.modifiers]
        self.hotKey = theHotkey.hotKey

    def set_hotkey(self, modifiers, key):
        modifiers.sort()
        self.modifiers = modifiers
        self.hotKey = key

    def check_hotkey(self, modifiers, key, windowTitle):
        if self.hotKey is not None and self._should_trigger_window_title(windowTitle):
            return (self.modifiers == modifiers) and (self.hotKey == key)
        else:
            return False

    def get_hotkey_string(self, key=None, modifiers=None):
        if key is None and modifiers is None:
            if TriggerMode.HOTKEY not in self.modes:
                return ""

            key = self.hotKey
            modifiers = self.modifiers

        ret = ""

        for modifier in modifiers:
            ret += modifier
            ret += "+"

        if key == ' ':
            ret += "<space>"
        else:
            ret += key

        return ret


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
        self.items = []  # type: typing.List[Item]
        self.modes = []  # type: typing.List[TriggerMode]
        self.usageCount = 0
        self.show_in_tray_menu = show_in_tray_menu
        self.parent = None  # type: typing.Optional[Folder]
        self.path = path

    def build_path(self, base_name=None):
        if base_name is None:
            base_name = self.title

        if self.parent is not None:
            self.path = get_safe_path(self.parent.path, base_name)
        else:
            self.path = get_safe_path(cm.CONFIG_DEFAULT_FOLDER, base_name)

    def persist(self):
        if self.path is None:
            self.build_path()

        if not os.path.exists(self.path):
            os.mkdir(self.path)

        with open(self.path + "/.folder.json", 'w') as outFile:
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
            with open(self.path + "/.folder.json", 'r') as inFile:
                data = json.load(inFile)
                self.inject_json_data(data)
        except Exception:
            _logger.exception("Error while loading json data for " + self.title)
            _logger.error("JSON data not loaded (or loaded incomplete)")

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
        return self.path + "/.folder.json"

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


class Phrase(AbstractAbbreviation, AbstractHotkey, AbstractWindowFilter):
    """
    Encapsulates all data and behaviour for a phrase.
    """

    def __init__(self, description, phrase, path=None):
        AbstractAbbreviation.__init__(self)
        AbstractHotkey.__init__(self)
        AbstractWindowFilter.__init__(self)
        self.description = description
        self.phrase = phrase
        self.modes = []  # type: typing.List[TriggerMode]
        self.usageCount = 0
        self.prompt = False
        self.omitTrigger = False
        self.matchCase = False
        self.parent = None
        self.show_in_tray_menu = False
        self.sendMode = SendMode.KEYBOARD
        self.path = path

    def build_path(self, base_name=None):
        if base_name is None:
            base_name = self.description
        else:
            base_name = base_name[:-4]
        self.path = get_safe_path(self.parent.path, base_name, ".txt")

    def get_json_path(self):
        directory, base_name = os.path.split(self.path[:-4])
        return JSON_FILE_PATTERN.format(directory, base_name)

    def persist(self):
        if self.path is None:
            self.build_path()

        with open(self.get_json_path(), 'w') as json_file:
            json.dump(self.get_serializable(), json_file, indent=4)

        with open(self.path, "w") as out_file:
            out_file.write(self.phrase)

    def get_serializable(self):
        d = {
            "type": "phrase",
            "description": self.description,
            "modes": [mode.value for mode in self.modes],  # Store the enum value for compatibility with old user data.
            "usageCount": self.usageCount,
            "prompt": self.prompt,
            "omitTrigger": self.omitTrigger,
            "matchCase": self.matchCase,
            "showInTrayMenu": self.show_in_tray_menu,
            "abbreviation": AbstractAbbreviation.get_serializable(self),
            "hotkey": AbstractHotkey.get_serializable(self),
            "filter": AbstractWindowFilter.get_serializable(self),
            "sendMode": self.sendMode.value
            }
        return d

    def load(self, parent):
        self.parent = parent

        with open(self.path, "r") as inFile:
            self.phrase = inFile.read()

        if os.path.exists(self.get_json_path()):
            self.load_from_serialized()
        else:
            self.description = os.path.basename(self.path)[:-4]

    def load_from_serialized(self):
        try:
            with open(self.get_json_path(), "r") as json_file:
                data = json.load(json_file)
                self.inject_json_data(data)
        except Exception:
            _logger.exception("Error while loading json data for " + self.description)
            _logger.error("JSON data not loaded (or loaded incomplete)")

    def inject_json_data(self, data: dict):
        self.description = data["description"]
        self.modes = [TriggerMode(item) for item in data["modes"]]
        self.usageCount = data["usageCount"]
        self.prompt = data["prompt"]
        self.omitTrigger = data["omitTrigger"]
        self.matchCase = data["matchCase"]
        self.show_in_tray_menu = data["showInTrayMenu"]
        self.sendMode = SendMode(data.get("sendMode", SendMode.KEYBOARD))
        AbstractAbbreviation.load_from_serialized(self, data["abbreviation"])
        AbstractHotkey.load_from_serialized(self, data["hotkey"])
        AbstractWindowFilter.load_from_serialized(self, data["filter"])

    def rebuild_path(self):
        if self.path is not None:
            old_name = self.path
            old_json = self.get_json_path()
            self.build_path()
            os.rename(old_name, self.path)
            os.rename(old_json, self.get_json_path())
        else:
            self.build_path()

    def remove_data(self):
        if self.path is not None:
            if os.path.exists(self.path):
                os.remove(self.path)
            if os.path.exists(self.get_json_path()):
                os.remove(self.get_json_path())

    def copy(self, source_phrase):
        self.description = source_phrase.description
        self.phrase = source_phrase.phrase

        # TODO - re-enable me if restoring predictive functionality
        #if TriggerMode.PREDICTIVE in source_phrase.modes:
        #    self.modes.append(TriggerMode.PREDICTIVE)

        self.prompt = source_phrase.prompt
        self.omitTrigger = source_phrase.omitTrigger
        self.matchCase = source_phrase.matchCase
        self.parent = source_phrase.parent
        self.show_in_tray_menu = source_phrase.show_in_tray_menu
        self.copy_abbreviation(source_phrase)
        self.copy_hotkey(source_phrase)
        self.copy_window_filter(source_phrase)

    def get_tuple(self):
        return "text-plain", self.description, self.get_abbreviations(), self.get_hotkey_string(), self

    def set_modes(self, modes: typing.List[TriggerMode]):
        self.modes = modes

    def check_input(self, buffer, window_info):
        if TriggerMode.ABBREVIATION in self.modes:
            return self._should_trigger_abbreviation(buffer) and self._should_trigger_window_title(window_info)
        else:
            return False

    def build_phrase(self, buffer):
        self.usageCount += 1
        self.parent.increment_usage_count()
        expansion = Expansion(self.phrase)
        trigger_found = False

        if TriggerMode.ABBREVIATION in self.modes:
            if self._should_trigger_abbreviation(buffer):
                abbr = self._get_trigger_abbreviation(buffer)

                stringBefore, typedAbbr, stringAfter = self._partition_input(buffer, abbr)
                trigger_found = True
                if self.backspace:
                    # determine how many backspaces to send
                    expansion.backspaces = len(abbr) + len(stringAfter)
                else:
                    expansion.backspaces = len(stringAfter)

                if not self.omitTrigger:
                    expansion.string += stringAfter

                if self.matchCase:
                    if typedAbbr.istitle():
                        expansion.string = expansion.string.capitalize()
                    elif typedAbbr.isupper():
                        expansion.string = expansion.string.upper()
                    elif typedAbbr.islower():
                        expansion.string = expansion.string.lower()

        # TODO - re-enable me if restoring predictive functionality
        #if TriggerMode.PREDICTIVE in self.modes:
        #    if self._should_trigger_predictive(buffer):
        #        expansion.string = expansion.string[ConfigManager.SETTINGS[PREDICTIVE_LENGTH]:]
        #        trigger_found = True

        if not trigger_found:
            # Phrase could have been triggered from menu - check parents for backspace count
            expansion.backspaces = self.parent.get_backspace_count(buffer)

        #self.__parsePositionTokens(expansion)
        return expansion

    def calculate_input(self, buffer):
        """
        Calculate how many keystrokes were used in triggering this phrase.
        """
        # TODO: This function is unused?
        if TriggerMode.ABBREVIATION in self.modes:
            if self._should_trigger_abbreviation(buffer):
                if self.immediate:
                    return len(self._get_trigger_abbreviation(buffer))
                else:
                    return len(self._get_trigger_abbreviation(buffer)) + 1

        # TODO - re-enable me if restoring predictive functionality
        #if TriggerMode.PREDICTIVE in self.modes:
        #    if self._should_trigger_predictive(buffer):
        #        return ConfigManager.SETTINGS[PREDICTIVE_LENGTH]

        if TriggerMode.HOTKEY in self.modes:
            if buffer == '':
                return len(self.modifiers) + 1

        return self.parent.calculate_input(buffer)

    def get_trigger_chars(self, buffer):
        abbr = self._get_trigger_abbreviation(buffer)
        stringBefore, typedAbbr, stringAfter = self._partition_input(buffer, abbr)
        return typedAbbr + stringAfter

    def should_prompt(self, buffer):
        """
        Get a value indicating whether the user should be prompted to select the phrase.
        Always returns true if the phrase has been triggered using predictive mode.
        """
        # TODO - re-enable me if restoring predictive functionality
        #if TriggerMode.PREDICTIVE in self.modes:
        #    if self._should_trigger_predictive(buffer):
        #        return True

        return self.prompt

    def get_description(self, buffer):
        # TODO - re-enable me if restoring predictive functionality
        #if self._should_trigger_predictive(buffer):
        #    length = ConfigManager.SETTINGS[PREDICTIVE_LENGTH]
        #    endPoint = length + 30
        #    if len(self.phrase) > endPoint:
        #        description = "... " + self.phrase[length:endPoint] + "..."
        #    else:
        #        description = "... " + self.phrase[length:]
        #    description = description.replace('\n', ' ')
        #    return description
        #else:
        return self.description

    # TODO - re-enable me if restoring predictive functionality
    """def _should_trigger_predictive(self, buffer):
        if len(buffer) >= ConfigManager.SETTINGS[PREDICTIVE_LENGTH]:
            typed = buffer[-ConfigManager.SETTINGS[PREDICTIVE_LENGTH]:]
            return self.phrase.startswith(typed)
        else:
            return False"""

    def parsePositionTokens(self, expansion):
        # Check the string for cursor positioning token and apply lefts and ups as appropriate
        if CURSOR_POSITION_TOKEN in expansion.string:  # TODO: Undefined local variable?
            firstpart, secondpart = expansion.string.split(CURSOR_POSITION_TOKEN)
            foundNavigationKey = False

            for key in NAVIGATION_KEYS:
                if key in expansion.string:
                    expansion.lefts = 0
                    foundNavigationKey = True
                    break

            if not foundNavigationKey:
                for section in KEY_SPLIT_RE.split(secondpart):
                    if not Key.is_key(section) or section in [' ', '\n']:
                        expansion.lefts += len(section)

            expansion.string = firstpart + secondpart

    def __str__(self):
        return "phrase '{}'".format(self.description)

    def __repr__(self):
        return "Phrase('" + self.description + "')"


class Expansion:

    def __init__(self, string):
        self.string = string
        self.lefts = 0
        self.backspaces = 0


class Script(AbstractAbbreviation, AbstractHotkey, AbstractWindowFilter):
    """
    Encapsulates all data and behaviour for a script.
    """

    def __init__(self, description: str, source_code: str, path=None):
        AbstractAbbreviation.__init__(self)
        AbstractHotkey.__init__(self)
        AbstractWindowFilter.__init__(self)
        self.description = description
        self.code = source_code
        self.store = Store()
        self.modes = []  # type: typing.List[TriggerMode]
        self.usageCount = 0
        self.prompt = False
        self.omitTrigger = False
        self.parent = None
        self.show_in_tray_menu = False
        self.path = path

    def build_path(self, base_name=None):
        if base_name is None:
            base_name = self.description
        else:
            base_name = base_name[:-3]
        self.path = get_safe_path(self.parent.path, base_name, ".py")

    def get_json_path(self):
        directory, base_name = os.path.split(self.path[:-3])
        return JSON_FILE_PATTERN.format(directory, base_name)

    def persist(self):
        if self.path is None:
            self.build_path()

        self._persist_metadata()

        with open(self.path, "w") as out_file:
            out_file.write(self.code)

    def get_serializable(self):
        d = {
            "type": "script",
            "description": self.description,
            "store": self.store,
            "modes": [mode.value for mode in self.modes],  # Store the enum value for compatibility with old user data.
            "usageCount": self.usageCount,
            "prompt": self.prompt,
            "omitTrigger": self.omitTrigger,
            "showInTrayMenu": self.show_in_tray_menu,
            "abbreviation": AbstractAbbreviation.get_serializable(self),
            "hotkey": AbstractHotkey.get_serializable(self),
            "filter": AbstractWindowFilter.get_serializable(self)
            }
        return d

    def _persist_metadata(self):
        """
        Write all script meta-data, including the persistent script Store.
        The Store instance might contain arbitrary user data, like function objects, OpenCL contexts, or whatever other
        non-serializable objects, both as keys or values.
        Try to serialize the data, and if it fails, fall back to checking the store and removing all non-serializable
        data.
        """
        serializable_data = self.get_serializable()
        try:
            self._try_persist_metadata(serializable_data)
        except TypeError:
            # The user added non-serializable data to the store, so skip all non-serializable keys or values.
            cleaned_data = Script._remove_non_serializable_store_entries(serializable_data["store"])
            self._try_persist_metadata(cleaned_data)

    def _try_persist_metadata(self, serializable_data: dict):
        with open(self.get_json_path(), "w") as json_file:
                json.dump(serializable_data, json_file, indent=4)

    @staticmethod
    def _remove_non_serializable_store_entries(store: Store) -> dict:
        """
        Copy all serializable data into a new dict, and skip the rest.
        This makes sure to keep the items during runtime, even if the user edits and saves the script.
        """
        cleaned_store_data = {}
        for key, value in store.items():
            if Script._is_serializable(key) and Script._is_serializable(value):
                cleaned_store_data[key] = value
            else:
                _logger.info("Skip non-serializable item in the local script store. Key: '{}', Value: '{}'. "
                             "This item cannot be saved and therefore will be lost when autokey quits.".format(
                                key, value
                ))
        return cleaned_store_data

    @staticmethod
    def _is_serializable(data):
        try:
            json.dumps(data)
        except (TypeError, ValueError):
            # TypeError occurs with non-serializable types (type, function, etc.)
            # ValueError occurs when circular references are found. Example: `l=[]; l.append(l)`
            return False
        else:
            return True

    def load(self, parent: Folder):
        self.parent = parent

        with open(self.path, "r", encoding="UTF-8") as in_file:
            self.code = in_file.read()

        if os.path.exists(self.get_json_path()):
            self.load_from_serialized()
        else:
            self.description = os.path.basename(self.path)[:-3]

    def load_from_serialized(self, **kwargs):
        try:
            with open(self.get_json_path(), "r") as jsonFile:
                data = json.load(jsonFile)
                self.inject_json_data(data)
        except Exception:
            _logger.exception("Error while loading json data for " + self.description)
            _logger.error("JSON data not loaded (or loaded incomplete)")

    def inject_json_data(self, data: dict):
        self.description = data["description"]
        self.store = Store(data["store"])
        self.modes = [TriggerMode(item) for item in data["modes"]]
        self.usageCount = data["usageCount"]
        self.prompt = data["prompt"]
        self.omitTrigger = data["omitTrigger"]
        self.show_in_tray_menu = data["showInTrayMenu"]
        AbstractAbbreviation.load_from_serialized(self, data["abbreviation"])
        AbstractHotkey.load_from_serialized(self, data["hotkey"])
        AbstractWindowFilter.load_from_serialized(self, data["filter"])

    def rebuild_path(self):
        if self.path is not None:
            oldName = self.path
            oldJson = self.get_json_path()
            self.build_path()
            os.rename(oldName, self.path)
            os.rename(oldJson, self.get_json_path())
        else:
            self.build_path()

    def remove_data(self):
        if self.path is not None:
            if os.path.exists(self.path):
                os.remove(self.path)
            if os.path.exists(self.get_json_path()):
                os.remove(self.get_json_path())

    def copy(self, source_script):
        self.description = source_script.description
        self.code = source_script.code

        self.prompt = source_script.prompt
        self.omitTrigger = source_script.omitTrigger
        self.parent = source_script.parent
        self.show_in_tray_menu = source_script.show_in_tray_menu
        self.copy_abbreviation(source_script)
        self.copy_hotkey(source_script)
        self.copy_window_filter(source_script)

    def get_tuple(self):
        return "text-x-python", self.description, self.get_abbreviations(), self.get_hotkey_string(), self

    def set_modes(self, modes: typing.List[TriggerMode]):
        self.modes = modes

    def check_input(self, buffer, window_info):
        if TriggerMode.ABBREVIATION in self.modes:
            return self._should_trigger_abbreviation(buffer) and self._should_trigger_window_title(window_info)
        else:
            return False

    def process_buffer(self, buffer):
        self.usageCount += 1
        self.parent.increment_usage_count()
        trigger_found = False
        backspaces = 0
        string = ""

        if TriggerMode.ABBREVIATION in self.modes:
            if self._should_trigger_abbreviation(buffer):
                abbr = self._get_trigger_abbreviation(buffer)
                stringBefore, typedAbbr, stringAfter = self._partition_input(buffer, abbr)
                trigger_found = True
                if self.backspace:
                    # determine how many backspaces to send
                    backspaces = len(abbr) + len(stringAfter)
                else:
                    backspaces = len(stringAfter)

                if not self.omitTrigger:
                    string += stringAfter

        if not trigger_found:
            # Phrase could have been triggered from menu - check parents for backspace count
            backspaces = self.parent.get_backspace_count(buffer)

        return backspaces, string

    def should_prompt(self, buffer):
        return self.prompt

    def get_description(self, buffer):
        return self.description

    def __str__(self):
        return "script '{}'".format(self.description)

    def __repr__(self):
        return "Script('" + self.description + "')"


Item = typing.Union[Folder, Phrase, Script]
