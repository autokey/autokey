#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, sys, os, re
#from PyKDE4.kdeui import KApplication, KXmlGuiWindow, KStandardAction, KIcon, KTextEdit, KAction, KStandardShortcut
from PyKDE4.kdeui import *
from PyKDE4.kdecore import i18n
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, Qt, QRegExp

__all__ = ["validate", "EMPTY_FIELD_REGEX", "AbbrSettingsDialog", "HotkeySettingsDialog", "WindowFilterSettingsDialog"]

import abbrsettings, hotkeysettings, windowfiltersettings
from autokey import model, iomediator

WORD_CHAR_OPTIONS = {
                     "Default" : model.DEFAULT_WORDCHAR_REGEX,
                     "Space and Enter" : r"[^ \n]"
                     }
WORD_CHAR_OPTIONS_ORDERED = ["Default", "Space and Enter"]

EMPTY_FIELD_REGEX = re.compile(r"^ *$", re.UNICODE)

def validate(expression, message, widget, parent):
    if not expression:
        KMessageBox.error(parent, message)
        if widget is not None:
            widget.setFocus()
    return expression

class AbbrSettings(QWidget, abbrsettings.Ui_Form):
    
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        abbrsettings.Ui_Form.__init__(self)
        self.setupUi(self)
        
        for item in WORD_CHAR_OPTIONS_ORDERED:
            self.wordCharCombo.addItem(item)        
        
    def on_ignoreCaseCheckbox_stateChanged(self, state):
        if not self.ignoreCaseCheckbox.isChecked():
            self.matchCaseCheckbox.setChecked(False)
            
    def on_matchCaseCheckbox_stateChanged(self, state):
        if self.matchCaseCheckbox.isChecked():
            self.ignoreCaseCheckbox.setChecked(True)
            
    def on_immediateCheckbox_stateChanged(self, state):
        if self.immediateCheckbox.isChecked():
            self.omitTriggerCheckbox.setChecked(False)
            self.omitTriggerCheckbox.setEnabled(False)
        else:
            self.omitTriggerCheckbox.setEnabled(True)        


class AbbrSettingsDialog(KDialog):

    def __init__(self, parent):
        KDialog.__init__(self, parent)
        self.widget = AbbrSettings(self)
        self.setMainWidget(self.widget)
        self.setButtons(KDialog.ButtonCodes(KDialog.ButtonCode(KDialog.Ok | KDialog.Cancel)))
        self.setPlainCaption(i18n("Set Abbreviation"))    
        self.setModal(True)
        #self.connect(self, SIGNAL("okClicked()"), self.on_okClicked)
        
    def load(self, item):
        self.targetItem = item
        
        if model.TriggerMode.ABBREVIATION in item.modes:
            self.widget.abbrLineEdit.setText(item.abbreviation)        
        else:
            self.widget.abbrLineEdit.setText("")
        self.widget.removeTypedCheckbox.setChecked(item.backspace)
        
        for desc, regex in WORD_CHAR_OPTIONS.iteritems():
            if item.get_word_chars() == regex:
                self.widget.wordCharCombo.setCurrentIndex(WORD_CHAR_OPTIONS_ORDERED.index(desc))
                break
        
        if isinstance(item, model.Folder):
            self.widget.omitTriggerCheckbox.setVisible(False)
        else:
            self.widget.omitTriggerCheckbox.setVisible(True)
            self.widget.omitTriggerCheckbox.setChecked(item.omitTrigger)
        
        if isinstance(item, model.Phrase):
            self.widget.matchCaseCheckbox.setVisible(True)
            self.widget.matchCaseCheckbox.setChecked(item.matchCase)
        else:
            self.widget.matchCaseCheckbox.setVisible(False)
        
        self.widget.ignoreCaseCheckbox.setChecked(item.ignoreCase)
        self.widget.triggerInsideCheckbox.setChecked(item.triggerInside)
        self.widget.immediateCheckbox.setChecked(item.immediate)
        
    def save(self, item):
        item.modes.append(model.TriggerMode.ABBREVIATION)
        item.abbreviation = self.get_abbr()
        
        item.backspace = self.widget.removeTypedCheckbox.isChecked()
        
        option = str(self.widget.wordCharCombo.currentText())
        item.set_word_chars(WORD_CHAR_OPTIONS[option])
        
        if not isinstance(item, model.Folder):
            item.omitTrigger = self.widget.omitTriggerCheckbox.isChecked()
            
        if isinstance(item, model.Phrase):
            item.matchCase = self.widget.matchCaseCheckbox.isChecked()
            
        item.ignoreCase = self.widget.ignoreCaseCheckbox.isChecked()
        item.triggerInside = self.widget.triggerInsideCheckbox.isChecked()
        item.immediate = self.widget.immediateCheckbox.isChecked()
        
    def reset(self):
        self.widget.abbrLineEdit.setText("")
        self.widget.wordCharCombo.setCurrentIndex(0)
        self.widget.omitTriggerCheckbox.setChecked(False)
        self.widget.removeTypedCheckbox.setChecked(True)
        self.widget.matchCaseCheckbox.setChecked(False)
        self.widget.ignoreCaseCheckbox.setChecked(False)
        self.widget.triggerInsideCheckbox.setChecked(False)
        self.widget.immediateCheckbox.setChecked(False)
        
    def get_abbr(self):
        return unicode(self.widget.abbrLineEdit.text())
        
    def slotButtonClicked(self, button):
        if button == KDialog.Ok:
            if self.__valid():
                KDialog.slotButtonClicked(self, button)
        else:
            KDialog.slotButtonClicked(self, button)
            
    def __valid(self):
        configManager = self.parentWidget().topLevelWidget().app.configManager
        if not validate(configManager.check_abbreviation_unique(self.get_abbr(), self.targetItem),
                             i18n("The abbreviation is already in use.\nAbbreviations must be unique."),
                             self.widget.abbrLineEdit, self): return False        
        
        if not validate(not EMPTY_FIELD_REGEX.match(self.get_abbr()), i18n("Abbreviation can't be empty."),
                            self.widget.abbrLineEdit, self): return False
                            
        return True


class HotkeySettings(QWidget, hotkeysettings.Ui_Form):
    
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        hotkeysettings.Ui_Form.__init__(self)
        self.setupUi(self)    

    # ---- Signal handlers
    
    def on_setButton_pressed(self):
        self.setButton.setEnabled(False)
        self.keyLabel.setText(i18n("Press a key..."))
        self.grabber = iomediator.KeyGrabber(self.parentWidget())
        self.grabber.start()  

class HotkeySettingsDialog(KDialog):
    
    KEY_MAP = {
               ' ' : "<space>",
               '\t' : "<tab>",
               '\b' : "<backspace>",
               '\n' : "<enter>" 
               }
    
    REVERSE_KEY_MAP = {}
    for key, value in KEY_MAP.iteritems():
        REVERSE_KEY_MAP[value] = key

    def __init__(self, parent):
        KDialog.__init__(self, parent)
        self.widget = HotkeySettings(self)
        self.setMainWidget(self.widget)
        self.setButtons(KDialog.ButtonCodes(KDialog.ButtonCode(KDialog.Ok | KDialog.Cancel)))
        self.setPlainCaption(i18n("Set Hotkey"))
        self.setModal(True)
        self.key = None

    def load(self, item):
        self.targetItem = item
        if model.TriggerMode.HOTKEY in item.modes:
            self.widget.controlButton.setChecked(iomediator.Key.CONTROL in item.modifiers)
            self.widget.altButton.setChecked(iomediator.Key.ALT in item.modifiers)
            self.widget.shiftButton.setChecked(iomediator.Key.SHIFT in item.modifiers)
            self.widget.superButton.setChecked(iomediator.Key.SUPER in item.modifiers)

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
            
        item.set_hotkey(modifiers, key)
        
    def reset(self):
        self.widget.controlButton.setChecked(False)
        self.widget.altButton.setChecked(False)
        self.widget.shiftButton.setChecked(False)
        self.widget.superButton.setChecked(False)

        self._setKeyLabel(i18n("(None)"))
        self.key = None
            
    def set_key(self, key):
        if self.KEY_MAP.has_key(key):
            key = self.KEY_MAP[key]
        self._setKeyLabel(key)
        self.key = key
        self.widget.setButton.setEnabled(True)
        
    def build_modifiers(self):
        modifiers = []
        if self.widget.controlButton.isChecked():
            modifiers.append(iomediator.Key.CONTROL) 
        if self.widget.altButton.isChecked():
            modifiers.append(iomediator.Key.ALT)
        if self.widget.shiftButton.isChecked():
            modifiers.append(iomediator.Key.SHIFT)
        if self.widget.superButton.isChecked():
            modifiers.append(iomediator.Key.SUPER)
        
        modifiers.sort()
        return modifiers
        
                
    def slotButtonClicked(self, button):
        if button == KDialog.Ok:
            if self.__valid():
                KDialog.slotButtonClicked(self, button)
        else:
            self.load(self.targetItem)
            KDialog.slotButtonClicked(self, button)
            
    def _setKeyLabel(self, key):
        self.widget.keyLabel.setText(i18n("Key: ") + key)
        
    def __valid(self):
        configManager = self.parentWidget().topLevelWidget().app.configManager
        modifiers = self.build_modifiers()
        
        if not validate(configManager.check_hotkey_unique(modifiers, self.key, self.targetItem),
                            i18n("The hotkey is already in use.\nHotkeys must be unique."), None,
                            self): return False

        if not validate(self.key is not None, i18n("You must specify a key for the Hotkey."),
                            None, self): return False
        
        if not validate(len(modifiers) > 0, i18n("You must select at least one modifier for the Hotkey"),
                            None, self): return False
        
        return True
        
        
class GlobalHotkeyDialog(HotkeySettingsDialog):
    
    def load(self, item):
        self.targetItem = item
        if item.enabled:
            self.widget.controlButton.setChecked(iomediator.Key.CONTROL in item.modifiers)
            self.widget.altButton.setChecked(iomediator.Key.ALT in item.modifiers)
            self.widget.shiftButton.setChecked(iomediator.Key.SHIFT in item.modifiers)
            self.widget.superButton.setChecked(iomediator.Key.SUPER in item.modifiers)

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
            
        item.set_hotkey(modifiers, key)        
        
        
class WindowFilterSettings(QWidget, windowfiltersettings.Ui_Form):
    
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        windowfiltersettings.Ui_Form.__init__(self)
        self.setupUi(self)    


class WindowFilterSettingsDialog(KDialog):

    def __init__(self, parent):
        KDialog.__init__(self, parent)
        self.widget = WindowFilterSettings(self)
        self.setMainWidget(self.widget)
        self.setButtons(KDialog.ButtonCodes(KDialog.ButtonCode(KDialog.Ok | KDialog.Cancel)))
        self.setPlainCaption(i18n("Set Window Filter"))
        self.setModal(True)
        
    def load(self, item):
        if item.uses_default_filter():
            self.reset()
        else:
            self.widget.triggerRegexLineEdit.setText(item.get_filter_regex())
            
    def save(self, item):
        item.set_window_titles(self.get_filter_text())
            
    def reset(self):
        self.widget.triggerRegexLineEdit.setText("")
        
    def get_filter_text(self):
        return unicode(self.widget.triggerRegexLineEdit.text())