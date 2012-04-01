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
#import gtk, Gtk.glade
from gi.repository import Gtk

#import gettext
import locale

GETTEXT_DOMAIN = 'autokey'

locale.setlocale(locale.LC_ALL, '')
#for module in Gtk.glade, gettext:
#    module.bindtextdomain(GETTEXT_DOMAIN)
#    module.textdomain(GETTEXT_DOMAIN)


__all__ = ["validate", "EMPTY_FIELD_REGEX", "AbbrSettingsDialog", "HotkeySettingsDialog", "WindowFilterSettingsDialog", "RecordDialog"]

from autokey import model, iomediator
import configwindow

WORD_CHAR_OPTIONS = {
                     "All non-word" : model.DEFAULT_WORDCHAR_REGEX,
                     "Space and Enter" : r"[^ \n]",
                     "Tab" : r"[^\t]"
                     }
WORD_CHAR_OPTIONS_ORDERED = ["All non-word", "Space and Enter", "Tab"]

EMPTY_FIELD_REGEX = re.compile(r"^ *$", re.UNICODE)

def validate(expression, message, widget, parent):
    if not expression:
        dlg = Gtk.MessageDialog(parent, Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING,
                                 Gtk.ButtonsType.OK, message)
        dlg.run()
        dlg.destroy()
        if widget is not None:
            widget.grab_focus()
    return expression


class DialogBase:

    def __init__(self):    
        self.connect("close", self.on_close)
        self.connect("delete_event", self.on_close)        

    def on_close(self, widget, data=None):
        self.hide()
        return True    

    def on_cancel(self, widget, data=None):
        self.load(self.targetItem)
        self.ui.response(Gtk.ResponseType.CANCEL)
        self.hide()
        
    def on_ok(self, widget, data=None):
        if self.valid():
            self.response(Gtk.ResponseType.OK)
            self.hide()
        
    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)
    
    def on_response(self, widget, responseId):
        self.closure(responseId)
        if responseId < 0:
            self.hide()
            self.emit_stop_by_name('response')


class AbbrSettingsDialog(DialogBase):
    
    def __init__(self, parent, configManager, closure):
        builder = configwindow.get_ui("abbrsettings.xml")
        self.ui = builder.get_object("abbrsettings")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        self.configManager = configManager
        self.closure = closure
        
        self.abbrList = builder.get_object("abbrList")
        self.addButton = builder.get_object("addButton")
        self.removeButton = builder.get_object("removeButton")
        
        self.wordCharCombo = builder.get_object("wordCharCombo")
        self.removeTypedCheckbox = builder.get_object("removeTypedCheckbox")
        self.omitTriggerCheckbox = builder.get_object("omitTriggerCheckbox")
        self.matchCaseCheckbox = builder.get_object("matchCaseCheckbox")
        self.ignoreCaseCheckbox = builder.get_object("ignoreCaseCheckbox")
        self.triggerInsideCheckbox = builder.get_object("triggerInsideCheckbox")
        self.immediateCheckbox = builder.get_object("immediateCheckbox")
        
        DialogBase.__init__(self)
        
        # set up list view
        store = Gtk.ListStore(str)
        self.abbrList.set_model(store)
        
        column1 = Gtk.TreeViewColumn(_("Abbreviations"))
        textRenderer = Gtk.CellRendererText()
        textRenderer.set_property("editable", True)
        textRenderer.connect("edited", self.on_cell_modified)
        textRenderer.connect("editing-canceled", self.on_cell_editing_cancelled)
        column1.pack_end(textRenderer, True)
        column1.add_attribute(textRenderer, "text", 0)
        column1.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.abbrList.append_column(column1)
        
        for item in WORD_CHAR_OPTIONS_ORDERED:
            self.wordCharCombo.append_text(item)
        
    def load(self, item):
        self.targetItem = item
        self.abbrList.get_model().clear()
        
        if model.TriggerMode.ABBREVIATION in item.modes:
            for abbr in item.abbreviations:
                self.abbrList.get_model().append((abbr.encode("utf-8"),))
            self.removeButton.set_sensitive(True)
            firstIter = self.abbrList.get_model().get_iter_first()  
            self.abbrList.get_selection().select_iter(firstIter)
        else:
            self.removeButton.set_sensitive(False)
            
            
        self.removeTypedCheckbox.set_active(item.backspace)
        
        self.__resetWordCharCombo()

        wordCharRegex = item.get_word_chars()
        if wordCharRegex in WORD_CHAR_OPTIONS.values():
            # Default wordchar regex used
            for desc, regex in WORD_CHAR_OPTIONS.iteritems():
                if item.get_word_chars() == regex:
                    self.wordCharCombo.set_active(WORD_CHAR_OPTIONS_ORDERED.index(desc))
                    break
        else:
            # Custom wordchar regex used
            self.wordCharCombo.append_text(model.extract_wordchars(wordCharRegex).encode("utf-8"))
            self.wordCharCombo.set_active(len(WORD_CHAR_OPTIONS))
        
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
        item.clear_abbreviations()
        item.abbreviations = self.get_abbrs()
        
        item.backspace = self.removeTypedCheckbox.get_active()
        
        option = self.wordCharCombo.get_active_text()
        if option in WORD_CHAR_OPTIONS:
            item.set_word_chars(WORD_CHAR_OPTIONS[option])
        else:
            item.set_word_chars(model.make_wordchar_re(option))
        
        if not isinstance(item, model.Folder):
            item.omitTrigger = self.omitTriggerCheckbox.get_active()
            
        if isinstance(item, model.Phrase):
            item.matchCase = self.matchCaseCheckbox.get_active()
            
        item.ignoreCase = self.ignoreCaseCheckbox.get_active()
        item.triggerInside = self.triggerInsideCheckbox.get_active()
        item.immediate = self.immediateCheckbox.get_active()
        
    def reset(self):
        self.abbrList.get_model().clear()
        self.__resetWordCharCombo()
        self.removeButton.set_sensitive(False)
        self.wordCharCombo.set_active(0)
        self.omitTriggerCheckbox.set_active(False)
        self.removeTypedCheckbox.set_active(True)
        self.matchCaseCheckbox.set_active(False)
        self.ignoreCaseCheckbox.set_active(False)
        self.triggerInsideCheckbox.set_active(False)
        self.immediateCheckbox.set_active(False)
        
    def __resetWordCharCombo(self):
        self.wordCharCombo.remove_all()
        for item in WORD_CHAR_OPTIONS_ORDERED:
            self.wordCharCombo.append_text(item)
        self.wordCharCombo.set_active(0)
        
    def get_abbrs(self):
        ret = []
        model = self.abbrList.get_model()
        i = iter(model)
        
        try:
            while True:
                text = model.get_value(i.next().iter, 0)
                ret.append(text.decode("utf-8"))
        except StopIteration:
            pass
            
        return list(set(ret))
        
    def get_abbrs_readable(self):
        abbrs = self.get_abbrs()
        if len(abbrs) == 1:
            return abbrs[0].encode("utf-8")
        else:
            return "[%s]" % ','.join([a.encode("utf-8") for a in abbrs])
            
    def valid(self):
        if not validate(len(self.get_abbrs()) > 0, _("You must specify at least one abbreviation"),
                            self.addButton, self.ui): return False

        return True
    
    def reset_focus(self):
        self.addButton.grab_focus()
        
    # Signal handlers
    
    def on_cell_editing_cancelled(self, renderer, data=None):
        model, curIter = self.abbrList.get_selection().get_selected()
        oldText = model.get_value(curIter, 0) or ""
        self.on_cell_modified(renderer, None, oldText)    
    
    def on_cell_modified(self, renderer, path, newText, data=None):
        model, curIter = self.abbrList.get_selection().get_selected()
        oldText = model.get_value(curIter, 0) or ""
        if EMPTY_FIELD_REGEX.match(newText) and EMPTY_FIELD_REGEX.match(oldText):
            self.on_removeButton_clicked(renderer)
        else:
            model.set(curIter, 0, newText)      
    
    def on_addButton_clicked(self, widget, data=None):
        model = self.abbrList.get_model()
        newIter = model.append()
        self.abbrList.set_cursor(model.get_path(newIter), self.abbrList.get_column(0), True)
        self.removeButton.set_sensitive(True)
        
    def on_removeButton_clicked(self, widget, data=None):
        model, curIter = self.abbrList.get_selection().get_selected()
        model.remove(curIter)
        if model.get_iter_first() is None:
            self.removeButton.set_sensitive(False)
        else:
            self.abbrList.get_selection().select_iter(model.get_iter_first())
        
        
    def on_abbrList_cursorchanged(self, widget, data=None):
        pass
    
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
            self.wordCharCombo.set_sensitive(False)
        else:
            self.omitTriggerCheckbox.set_sensitive(True)
            self.wordCharCombo.set_sensitive(True)       


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
        self.hyperButton = builder.get_object("hyperButton")
        self.setButton = builder.get_object("setButton")
        self.keyLabel = builder.get_object("keyLabel")
        
        DialogBase.__init__(self)
        
    def load(self, item):
        self.targetItem = item
        self.setButton.set_sensitive(True)
        if model.TriggerMode.HOTKEY in item.modes:
            self.controlButton.set_active(iomediator.Key.CONTROL in item.modifiers)
            self.altButton.set_active(iomediator.Key.ALT in item.modifiers)
            self.shiftButton.set_active(iomediator.Key.SHIFT in item.modifiers)
            self.superButton.set_active(iomediator.Key.SUPER in item.modifiers)
            self.hyperButton.set_active(iomediator.Key.HYPER in item.modifiers)

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
        self.hyperButton.set_active(False)

        self._setKeyLabel(_("(None)"))
        self.key = None
        self.setButton.set_sensitive(True)
            
    def set_key(self, key, modifiers=[]):
        if self.KEY_MAP.has_key(key):
            key = self.KEY_MAP[key]
        self._setKeyLabel(key)
        self.key = key
        self.controlButton.set_active(iomediator.Key.CONTROL in modifiers)
        self.altButton.set_active(iomediator.Key.ALT in modifiers)
        self.shiftButton.set_active(iomediator.Key.SHIFT in modifiers)
        self.superButton.set_active(iomediator.Key.SUPER in modifiers)
        self.hyperButton.set_active(iomediator.Key.HYPER in modifiers)
        
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
        if self.hyperButton.get_active():
            modifiers.append(iomediator.Key.HYPER)
        
        modifiers.sort()
        return modifiers
        
    def _setKeyLabel(self, key):
        self.keyLabel.set_text(_("Key: ") + key)
        
    def valid(self):
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
            self.hyperButton.set_active(iomediator.Key.HYPER in item.modifiers)

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
        
        
    def valid(self):
        configManager = self.configManager
        modifiers = self.build_modifiers()
        pattern = self.targetItem.get_applicable_regex().pattern

        unique, conflicting = configManager.check_hotkey_unique(modifiers, self.key, pattern, self.targetItem)
        if not validate(unique, _("The hotkey is already in use for %s.") % conflicting, None,
                            self.ui): return False

        if not validate(self.key is not None, _("You must specify a key for the hotkey."),
                            None, self.ui): return False
        
        return True        


class WindowFilterSettingsDialog(DialogBase):
    
    def __init__(self, parent):
        builder = configwindow.get_ui("windowfiltersettings.xml")
        self.ui = builder.get_object("windowfiltersettings")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        
        self.triggerRegexEntry = builder.get_object("triggerRegexEntry")
        self.recursiveButton = builder.get_object("recursiveButton")
        
        DialogBase.__init__(self)
        
    def load(self, item):
        self.targetItem = item
        
        if not isinstance(item, model.Folder):
            self.recursiveButton.hide()
        else:
            self.recursiveButton.show()
        
        if not item.has_filter():
            self.reset()
        else:
            self.triggerRegexEntry.set_text(item.get_filter_regex())
            self.recursiveButton.set_active(item.isRecursive)
            
            
    def save(self, item):
        item.set_window_titles(self.get_filter_text())
        item.set_filter_recursive(self.get_is_recursive())
            
    def reset(self):
        self.triggerRegexEntry.set_text("")
        self.recursiveButton.set_active(False)
        
    def get_filter_text(self):
        return self.triggerRegexEntry.get_text().decode("utf-8")
        
    def get_is_recursive(self):
        return self.recursiveButton.get_active()
        
    
    def valid(self):
        return True
    
    def reset_focus(self):
        self.triggerRegexEntry.grab_focus()        
        
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
        
        DialogBase.__init__(self)
        
    def get_record_keyboard(self):
        return self.keyboardButton.get_active()
        
    def get_record_mouse(self):
        return self.mouseButton.get_active()

    def get_delay(self):
        return self.spinButton.get_value_as_int()
        
    def on_response(self, widget, responseId):
        self.closure(responseId, self.get_record_keyboard(), self.get_record_mouse(), self.get_delay())
        
    def on_cancel(self, widget, data=None):
        self.ui.response(Gtk.ResponseType.CANCEL)
        self.hide()
            
    def valid(self):
        return True

