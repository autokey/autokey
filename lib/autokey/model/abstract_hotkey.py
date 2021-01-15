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

from autokey.model.helpers import TriggerMode
from autokey.model.abstract_window_filter import AbstractWindowFilter
from autokey.model.key import Key


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
        modifiers.sort()
        self.modifiers = modifiers
        self.hotKey = key
        if key is not None and TriggerMode.HOTKEY not in self.modes:
            self.modes.append(TriggerMode.HOTKEY)

    def unset_hotkey(self):
        self.modifiers = None
        self.hotkey = None
        if TriggerMode.HOTKEY in self.modes:
            self.modes.remove(TriggerMode.HOTKEY)

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
