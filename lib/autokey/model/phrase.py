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

import enum
import json
import os
import typing

from autokey.model.key import NAVIGATION_KEYS, Key, KEY_SPLIT_RE
from autokey.model.helpers import JSON_FILE_PATTERN, get_safe_path, TriggerMode
from autokey.model.abstract_abbreviation import AbstractAbbreviation
from autokey.model.abstract_window_filter import AbstractWindowFilter
from autokey.model.abstract_hotkey import AbstractHotkey

logger = __import__("autokey.logger").logger.get_logger(__name__)


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
        self.temporary = False
        self.omitTrigger = False
        self.matchCase = False
        self.parent = None
        self.show_in_tray_menu = False
        self.sendMode = SendMode.CB_CTRL_V
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
            logger.exception("Error while loading json data for " + self.description)
            logger.error("JSON data not loaded (or loaded incomplete)")

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
        # TODO make this a constant elsewhere, and check what it should
        # actually be defined as. This is a guess, since this func is
        # currently unused.
        CURSOR_POSITION_TOKEN = "|"
        if CURSOR_POSITION_TOKEN in expansion.string:
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
