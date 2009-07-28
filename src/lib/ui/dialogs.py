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


class HotkeySettings(QWidget, hotkeysettings.Ui_Form):
    
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        hotkeysettings.Ui_Form.__init__(self)
        self.setupUi(self)    


class HotkeySettingsDialog(KDialog):

    def __init__(self, parent):
        KDialog.__init__(self, parent)
        self.widget = HotkeySettings(self)
        self.setMainWidget(self.widget)
        self.setButtons(KDialog.ButtonCodes(KDialog.ButtonCode(KDialog.Ok | KDialog.Cancel)))
        self.setPlainCaption(i18n("Set Hotkey"))
        self.setModal(True)

    def load(self, item):
        if model.TriggerMode.HOTKEY in item.modes:
            self.widget.controlButton.setChecked(iomediator.Key.CONTROL in item.modifiers)
            self.widget.altButton.setChecked(iomediator.Key.ALT in item.modifiers)
            self.widget.shiftButton.setChecked(iomediator.Key.SHIFT in item.modifiers)
            self.widget.superButton.setChecked(iomediator.Key.SUPER in item.modifiers)

            key = str(item.hotKey.encode("utf-8"))
            if key in self.KEY_MAP:
                keyText = self.KEY_MAP[key]
            else:
                keyText = key
            self.__setKeyLabel(keyText)
            
        else:
            self.widget.controlButton.setChecked(False)
            self.widget.altButton.setChecked(False)
            self.widget.shiftButton.setChecked(False)
            self.widget.superButton.setChecked(False)

            self.__setKeyLabel(i18n("(None)"))
            
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
            self.widget.triggerRegexLineEdit.setText("")
        else:
            self.widget.triggerRegexLineEdit.setText(item.get_filter_regex())
        