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

import typing

from autokey.model.triggermode import TriggerMode
from autokey.model.abstract_window_filter import AbstractWindowFilter
from autokey.model.key import Key, UNIVERSAL_MODIFIERS, MAPPED_UNIVERSAL_MODIFIERS


class AbstractHotkey(AbstractWindowFilter):

    def __init__(self):
        self.modifiers = []  # type: typing.List[Key]
        self.hotKey = None  # type: typing.Optional[str]

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
        if not modifiers:
            modifiers = []
        modifiers.sort()
        self.modifiers = modifiers
        self.hotKey = key
        if key is not None and TriggerMode.HOTKEY not in self.modes:
            self.modes.append(TriggerMode.HOTKEY)

    def unset_hotkey(self):
        self.modifiers = []
        self.hotKey = None
        if TriggerMode.HOTKEY in self.modes:
            self.modes.remove(TriggerMode.HOTKEY)

    def check_hotkey_has_properties(self, modifiers, key, windowTitle):
        """
        This method is run whenever a key is pressed for all of the scripts in autokey

        :param modifiers: The modifiers that were pressed when the key was pressed
        :param key: The key that was pressed
        :param windowTitle: The title of the window that was active when the key was pressed
        :return Boolean: Whether or not the hotkey matches
        """
        left_mods = []
        right_mods = []
        for modifier in self.modifiers:
            if modifier in UNIVERSAL_MODIFIERS: # if one of the hotkey modifiers is universal. Generate a left and right version of the hotkey. the same way it does below and return if true?
                left_mods.append(MAPPED_UNIVERSAL_MODIFIERS[modifier][0])
                right_mods.append(MAPPED_UNIVERSAL_MODIFIERS[modifier][1])
            else:
                left_mods.append(modifier)
                right_mods.append(modifier)

        #print(modifiers, self.modifiers, left_mods, right_mods)
        if self.hotKey is not None and self._should_trigger_window_title(windowTitle):
            return (self.modifiers == modifiers or left_mods == modifiers or right_mods == modifiers) and (self.hotKey == key)
        else:
            return False

    def get_hotkey_string(self, key=None, modifiers=None):
        if key is None and modifiers is None:
            if TriggerMode.HOTKEY not in self.modes:
                return ""

            key = self.hotKey
            modifiers = self.modifiers

        return AbstractHotkey.build_hotkey_string(modifiers, key)

    @staticmethod
    def build_hotkey_string(modifiers, key):
        ret = ""
        for modifier in modifiers:
            ret += modifier
            ret += "+"
        if key == ' ':
            ret += "<space>"
        else:
            ret += key
        return ret

