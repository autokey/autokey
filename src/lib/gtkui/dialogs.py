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

import logging, sys, os, re
import gtk, gtk.glade

import gettext
import locale

GETTEXT_DOMAIN = 'autokey'

locale.setlocale(locale.LC_ALL, '')
for module in gtk.glade, gettext:
    module.bindtextdomain(GETTEXT_DOMAIN)
    module.textdomain(GETTEXT_DOMAIN)


__all__ = ["validate", "EMPTY_FIELD_REGEX", "AbbrSettingsDialog", "HotkeySettingsDialog", "WindowFilterSettingsDialog", "RecordDialog"]

from autokey import model, iomediator
import configwindow

WORD_CHAR_OPTIONS = {
                     "Default" : model.DEFAULT_WORDCHAR_REGEX,
                     "Space and Enter" : r"[^ \n]"
                     }
WORD_CHAR_OPTIONS_ORDERED = ["Default", "Space and Enter"]

EMPTY_FIELD_REGEX = re.compile(r"^ *$", re.UNICODE)

def validate(expression, message, widget, parent):
    if not expression:
        dlg = gtk.MessageDialog(parent, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
                                 gtk.BUTTONS_OK, message)
        dlg.run()
        dlg.destroy()
        if widget is not None:
            widget.grab_focus()
    return expression


class DialogBase:

    def on_cancel(self, widget, data=None):
        self.load(self.targetItem)
        self.ui.response(gtk.RESPONSE_CANCEL)
        self.hide()
        
    def on_ok(self, widget, data=None):
        if self.valid():
            self.response(gtk.RESPONSE_OK)
            self.hide()
        
    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)
    
    def on_response(self, widget, responseId):
        self.closure(responseId)


class AbbrSettingsDialog(DialogBase):
    
    def __init__(self, parent, configManager, closure):
        builder = configwindow.get_ui("abbrsettings.xml")
        self.ui = builder.get_object("abbrsettings")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        self.configManager = configManager
        self.closure = closure
        
        self.abbrEntry = builder.get_object("abbrEntry")
        self.wordCharCombo = builder.get_object("wordCharCombo")
        self.removeTypedCheckbox = builder.get_object("removeTypedCheckbox")
        self.omitTriggerCheckbox = builder.get_object("omitTriggerCheckbox")
        self.matchCaseCheckbox = builder.get_object("matchCaseCheckbox")
        self.ignoreCaseCheckbox = builder.get_object("ignoreCaseCheckbox")
        self.triggerInsideCheckbox = builder.get_object("triggerInsideCheckbox")
        self.immediateCheckbox = builder.get_object("immediateCheckbox")
        
        #for item in WORD_CHAR_OPTIONS_ORDERED:
        #    self.wordCharCombo.append_text(item)
        
    def load(self, item):
        self.targetItem = item
        
        if model.TriggerMode.ABBREVIATION in item.modes:
            self.abbrEntry.set_text(item.abbreviation.encode("utf-8"))
        else:
            self.abbrEntry.set_text("")
        self.removeTypedCheckbox.set_active(item.backspace)
        
        for desc, regex in WORD_CHAR_OPTIONS.iteritems():
            if item.get_word_chars() == regex:
                self.wordCharCombo.set_active(WORD_CHAR_OPTIONS_ORDERED.index(desc))
                break
        
        if isinstance(item, model.Folder):
            self.omitTriggerCheckbox.hide()
        else:
            self.omitTriggerCheckbox.show()
            self.omitTriggerCheckbox.set_active(item.omitTrigger)
        
        if isinstance(item, model.Phrase):
            self.matchCaseCheckbox.show()
            self.matchCaseCheckbox.set_active(item.matchCase)
        else:
            self.matchCaseCheckbox.hide()
        
        self.ignoreCaseCheckbox.set_active(item.ignoreCase)
        self.triggerInsideCheckbox.set_active(item.triggerInside)
        self.immediateCheckbox.set_active(item.immediate)
        
    def save(self, item):
        item.modes.append(model.TriggerMode.ABBREVIATION)
        item.abbreviation = self.get_abbr()
        
        item.backspace = self.removeTypedCheckbox.get_active()
        
        option = self.wordCharCombo.get_active_text()
        item.set_word_chars(WORD_CHAR_OPTIONS[option])
        
        if not isinstance(item, model.Folder):
            item.omitTrigger = self.omitTriggerCheckbox.get_active()
            
        if isinstance(item, model.Phrase):
            item.matchCase = self.matchCaseCheckbox.get_active()
            
        item.ignoreCase = self.ignoreCaseCheckbox.get_active()
        item.triggerInside = self.triggerInsideCheckbox.get_active()
        item.immediate = self.immediateCheckbox.get_active()
        
    def reset(self):
        self.abbrEntry.set_text("")
        self.wordCharCombo.set_active(0)
        self.omitTriggerCheckbox.set_active(False)
        self.removeTypedCheckbox.set_active(True)
        self.matchCaseCheckbox.set_active(False)
        self.ignoreCaseCheckbox.set_active(False)
        self.triggerInsideCheckbox.set_active(False)
        self.immediateCheckbox.set_active(False)
        
    def get_abbr(self):
        return self.abbrEntry.get_text().decode("utf-8")
            
    def valid(self):
        configManager = self.configManager

        unique, itemName  = configManager.check_abbreviation_unique(self.get_abbr(), self.targetItem)
        if not validate(unique, _("The abbreviation is already in use by '%s'.") % itemName,
                             self.abbrEntry, self.ui): return False
        
        if not validate(not EMPTY_FIELD_REGEX.match(self.get_abbr()), _("The abbreviation can't be empty."),
                            self.abbrEntry, self.ui): return False

        return True
        
    # Signal handlers
    
    def on_ignoreCaseCheckbox_stateChanged(self, widget, data=None):
        if not self.ignoreCaseCheckbox.get_active():
            self.matchCaseCheckbox.set_active(False)
            
    def on_matchCaseCheckbox_stateChanged(self, widget, data=None):
        if self.matchCaseCheckbox.get_active():
            self.ignoreCaseCheckbox.set_active(True)
            
    def on_immediateCheckbox_stateChanged(self, widget, data=None):
        if self.immediateCheckbox.get_active():
            self.omitTriggerCheckbox.set_active(False)
            self.omitTriggerCheckbox.set_sensitive(False)
        else:
            self.omitTriggerCheckbox.set_sensitive(True)        


class HotkeySettingsDialog(DialogBase):
    
    KEY_MAP = {
               ' ' : "<space>",
               }
    
    REVERSE_KEY_MAP = {}
    for key, value in KEY_MAP.iteritems():
        REVERSE_KEY_MAP[value] = key
        
    def __init__(self, parent, configManager, closure):
        builder = configwindow.get_ui("hotkeysettings.xml")
        self.ui = builder.get_object("hotkeysettings")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        self.configManager = configManager
        self.closure = closure
        self.key = None
        
        self.controlButton = builder.get_object("controlButton")
        self.altButton = builder.get_object("altButton")
        self.shiftButton = builder.get_object("shiftButton")
        self.superButton = builder.get_object("superButton")
        self.setButton = builder.get_object("setButton")
        self.keyLabel = builder.get_object("keyLabel")
        
    def load(self, item):
        self.targetItem = item
        self.setButton.set_sensitive(True)
        if model.TriggerMode.HOTKEY in item.modes:
            self.controlButton.set_active(iomediator.Key.CONTROL in item.modifiers)
            self.altButton.set_active(iomediator.Key.ALT in item.modifiers)
            self.shiftButton.set_active(iomediator.Key.SHIFT in item.modifiers)
            self.superButton.set_active(iomediator.Key.SUPER in item.modifiers)

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
        item.modes.append(model.TriggerMode.HOTKEY)
        
        # Build modifier list
        modifiers = self.build_modifiers()
            
        keyText = self.key
        if keyText in self.REVERSE_KEY_MAP:
            key = self.REVERSE_KEY_MAP[keyText]
        else:
            key = keyText

        assert key != None, "Attempt to set hotkey with no key"
        item.set_hotkey(modifiers, key)
        
    def reset(self):
        self.controlButton.set_active(False)
        self.altButton.set_active(False)
        self.shiftButton.set_active(False)
        self.superButton.set_active(False)

        self._setKeyLabel(_("(None)"))
        self.key = None
        self.setButton.set_sensitive(True)
            
    def set_key(self, key):
        if self.KEY_MAP.has_key(key):
            key = self.KEY_MAP[key]
        self._setKeyLabel(key)
        self.key = key
        self.setButton.set_sensitive(True)

    def cancel_grab(self):
        self.setButton.set_sensitive(True)
        self._setKeyLabel(self.key)
        
    def build_modifiers(self):
        modifiers = []
        if self.controlButton.get_active():
            modifiers.append(iomediator.Key.CONTROL) 
        if self.altButton.get_active():
            modifiers.append(iomediator.Key.ALT)
        if self.shiftButton.get_active():
            modifiers.append(iomediator.Key.SHIFT)
        if self.superButton.get_active():
            modifiers.append(iomediator.Key.SUPER)
        
        modifiers.sort()
        return modifiers
        
    def _setKeyLabel(self, key):
        self.keyLabel.set_text(_("Key: ") + key)
        
    def valid(self):
        configManager = self.configManager
        modifiers = self.build_modifiers()

        unique, itemName = configManager.check_hotkey_unique(modifiers, self.key, self.targetItem)
        if not validate(unique, _("The hotkey is already in use by '%s'.") % itemName, None,
                            self.ui): return False

        if not validate(self.key is not None, _("You must specify a key for the hotkey."),
                            None, self.ui): return False
        
        return True
        
    def on_setButton_pressed(self, widget, data=None):
        self.setButton.set_sensitive(False)
        self.keyLabel.set_text(_("Press a key..."))
        self.grabber = iomediator.KeyGrabber(self)
        self.grabber.start()
        

class GlobalHotkeyDialog(HotkeySettingsDialog):
    
    def load(self, item):
        self.targetItem = item
        if item.enabled:
            self.controlButton.set_active(iomediator.Key.CONTROL in item.modifiers)
            self.altButton.set_active(iomediator.Key.ALT in item.modifiers)
            self.shiftButton.set_active(iomediator.Key.SHIFT in item.modifiers)
            self.superButton.set_active(iomediator.Key.SUPER in item.modifiers)

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

        assert key != None, "Attempt to set hotkey with no key"
        item.set_hotkey(modifiers, key)


class WindowFilterSettingsDialog(DialogBase):
    
    def __init__(self, parent):
        builder = configwindow.get_ui("windowfiltersettings.xml")
        self.ui = builder.get_object("windowfiltersettings")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        
        self.triggerRegexEntry = builder.get_object("triggerRegexEntry")
        
    def load(self, item):
        self.targetItem = item
        if item.uses_default_filter():
            self.reset()
        else:
            self.triggerRegexEntry.set_text(item.get_filter_regex())
            
    def save(self, item):
        item.set_window_titles(self.get_filter_text())
            
    def reset(self):
        self.triggerRegexEntry.set_text("")
        
    def get_filter_text(self):
        return self.triggerRegexEntry.get_text().decode("utf-8")
    
    def valid(self):
        return True
        
        
class RecordDialog(DialogBase):
    
    def __init__(self, parent, closure):
        self.closure = closure
        builder = configwindow.get_ui("recorddialog.xml")
        self.ui = builder.get_object("recorddialog")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        
        self.keyboardButton = builder.get_object("keyboardButton")
        self.mouseButton = builder.get_object("mouseButton")
        self.spinButton = builder.get_object("spinButton")
        
    def get_record_keyboard(self):
        return self.keyboardButton.get_active()
        
    def get_record_mouse(self):
        return self.mouseButton.get_active()

    def get_delay(self):
        return self.spinButton.get_value_as_int()
        
    def on_response(self, widget, responseId):
        self.closure(responseId, self.get_record_keyboard(), self.get_record_mouse(), self.get_delay())
        
    def on_cancel(self, widget, data=None):
        self.ui.response(gtk.RESPONSE_CANCEL)
        self.hide()
            
    def valid(self):
        return True

