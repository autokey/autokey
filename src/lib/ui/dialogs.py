#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, sys, os
#from PyKDE4.kdeui import KApplication, KXmlGuiWindow, KStandardAction, KIcon, KTextEdit, KAction, KStandardShortcut
from PyKDE4.kdeui import *
from PyKDE4.kdecore import i18n
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, Qt

__all__ = ["AbbrSettingsDialog", "HotkeySettingsDialog", "WindowFilterSettingsDialog"]

import abbrsettings, hotkeysettings, windowfiltersettings
from .. import model, iomediator

WORD_CHAR_OPTIONS = {
                     "Default" : model.DEFAULT_WORDCHAR_REGEX,
                     "Space and Enter" : r"[^ \n]"
                     }
WORD_CHAR_OPTIONS_ORDERED = ["Default", "Space and Enter"]


class AbbrSettings(QWidget, abbrsettings.Ui_Form):
    
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        abbrsettings.Ui_Form.__init__(self)
        self.setupUi(self)
        
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
        
        for item in WORD_CHAR_OPTIONS_ORDERED:
            self.widget.wordCharCombo.addItem(item)
            
        self.setModal(True)
        
    def load(self, item):
        if model.TriggerMode.ABBREVIATION in item.modes:
            self.widget.abbrLineEdit.setText(item.abbreviation.encode("utf-8"))        
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
        item.abbreviation = str(self.widget.abbrLineEdit.text()).decode("utf-8")
        
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
        return self.widget.abbrLineEdit.text()


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

    def __init__(self, parent):
        KDialog.__init__(self, parent)
        self.widget = HotkeySettings(self)
        self.setMainWidget(self.widget)
        self.setButtons(KDialog.ButtonCodes(KDialog.ButtonCode(KDialog.Ok | KDialog.Cancel)))
        self.setPlainCaption(i18n("Set Hotkey"))
        self.setModal(True)
        self.key = None

    def load(self, item):
        if model.TriggerMode.HOTKEY in item.modes:
            self.widget.controlButton.setChecked(iomediator.Key.CONTROL in item.modifiers)
            self.widget.altButton.setChecked(iomediator.Key.ALT in item.modifiers)
            self.widget.shiftButton.setChecked(iomediator.Key.SHIFT in item.modifiers)
            self.widget.superButton.setChecked(iomediator.Key.SUPER in item.modifiers)

            key = str(item.hotKey)
            if key in self.KEY_MAP:
                keyText = self.KEY_MAP[key]
            else:
                keyText = key
            self.__setKeyLabel(keyText)
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

        self.__setKeyLabel(i18n("(None)"))        
            
    def set_key(self, key):
        if self.KEY_MAP.has_key(key):
            key = self.KEY_MAP[key]
        self.__setKeyLabel(key)
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
            
    def __setKeyLabel(self, key):
        self.widget.keyLabel.setText(i18n("Key: ") + key)

        
        
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
            self.widget.triggerRegexLineEdit.setText(item.get_filter_regex().encode("utf-8"))
            
    def save(self, item):
        item.set_window_titles(self.get_filter_text().decode("utf-8"))
            
    def reset(self):
        self.widget.triggerRegexLineEdit.setText("")
        
    def get_filter_text(self):
        return str(self.widget.triggerRegexLineEdit.text())