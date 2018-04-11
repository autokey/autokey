#!/usr/bin/env python
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

import re
from PyKDE4.kdeui import KDialog
from PyKDE4.kdecore import i18n
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt


__all__ = ["validate", "EMPTY_FIELD_REGEX", "AbbrSettingsDialog", "HotkeySettingsDialog", "WindowFilterSettingsDialog", "RecordDialog"]

from . import abbrsettings, hotkeysettings, windowfiltersettings, recorddialog, detectdialog
from .. import model, iomediator
from ..iomediator.key import Key
from .common import EMPTY_FIELD_REGEX, validate

WORD_CHAR_OPTIONS = {
                     "All non-word" : model.DEFAULT_WORDCHAR_REGEX,
                     "Space and Enter" : r"[^ \n]",
                     "Tab" : r"[^\t]"
                     }



WORD_CHAR_OPTIONS_ORDERED = abbrsettings.WORD_CHAR_OPTIONS_ORDERED


AbbrSettingsDialog = abbrsettings.AbbrSettingsDialog


HotkeySettingsDialog = hotkeysettings.HotkeySettingsDialog

        
        
class GlobalHotkeyDialog(HotkeySettingsDialog):
    
    def load(self, item):
        self.targetItem = item
        if item.enabled:
            self.widget.controlButton.setChecked(Key.CONTROL in item.modifiers)
            self.widget.altButton.setChecked(Key.ALT in item.modifiers)
            self.widget.shiftButton.setChecked(Key.SHIFT in item.modifiers)
            self.widget.superButton.setChecked(Key.SUPER in item.modifiers)
            self.widget.hyperButton.setChecked(Key.HYPER in item.modifiers)
            self.widget.metaButton.setChecked(Key.META in item.modifiers)

            key = item.hotKey
            if key in self.KEY_MAP:
                keyText = self.KEY_MAP[key]
            else:
                keyText = key
            self._setKeyLabel(keyText)
            self.key = keyText
            
        else:
            self.reset()
        
        
    def save(self, item):
        # Build modifier list
        modifiers = self.build_modifiers()
            
        keyText = self.key
        if keyText in self.REVERSE_KEY_MAP:
            key = self.REVERSE_KEY_MAP[keyText]
        else:
            key = keyText

        assert key is not None, "Attempt to set hotkey with no key"
        item.set_hotkey(modifiers, key)
        
        
from .windowfiltersettings import WindowFilterSettingsDialog
from .detectdialog import DetectDialog
from .recorddialog import RecordDialog

        


