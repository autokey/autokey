# -*- coding: utf-8 -*-

# Copyright (C) 2009 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from PyKDE4.kdeui import *
from PyKDE4.kdecore import i18n
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, Qt

from autokey.configmanager import *
from autokey import iomediator, interface, model
from dialogs import GlobalHotkeyDialog

import generalsettings, specialhotkeysettings, interfacesettings

class GeneralSettings(QWidget, generalsettings.Ui_Form):
    
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        generalsettings.Ui_Form.__init__(self)
        self.setupUi(self)
        
        self.promptToSaveCheckbox.setChecked(ConfigManager.SETTINGS[PROMPT_TO_SAVE])
        self.showTrayCheckbox.setChecked(ConfigManager.SETTINGS[SHOW_TRAY_ICON])
        self.allowKbNavCheckbox.setChecked(ConfigManager.SETTINGS[MENU_TAKES_FOCUS])
        self.sortByUsageCheckbox.setChecked(ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT])
        self.enableUndoCheckbox.setChecked(ConfigManager.SETTINGS[UNDO_USING_BACKSPACE])
        
    def save(self):
        ConfigManager.SETTINGS[PROMPT_TO_SAVE] = self.promptToSaveCheckbox.isChecked()
        ConfigManager.SETTINGS[SHOW_TRAY_ICON] = self.showTrayCheckbox.isChecked()
        ConfigManager.SETTINGS[MENU_TAKES_FOCUS] = self.allowKbNavCheckbox.isChecked()
        ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT] = self.sortByUsageCheckbox.isChecked()
        ConfigManager.SETTINGS[UNDO_USING_BACKSPACE] = self.enableUndoCheckbox.isChecked()


class SpecialHotkeySettings(QWidget, specialhotkeysettings.Ui_Form):
    
    KEY_MAP = GlobalHotkeyDialog.KEY_MAP
    REVERSE_KEY_MAP = GlobalHotkeyDialog.REVERSE_KEY_MAP    

    def __init__(self, parent, configManager):
        QWidget.__init__(self, parent)
        specialhotkeysettings.Ui_Form.__init__(self)
        self.setupUi(self)
        
        self.configManager = configManager
        
        self.showConfigDlg = GlobalHotkeyDialog(parent)
        self.toggleMonitorDlg = GlobalHotkeyDialog(parent)
        
        self.useConfigHotkey = self.__loadHotkey(configManager.configHotkey, self.configKeyLabel, 
                                                    self.showConfigDlg, self.clearConfigButton)
        self.useServiceHotkey = self.__loadHotkey(configManager.toggleServiceHotkey, self.monitorKeyLabel, 
                                                    self.toggleMonitorDlg, self.clearMonitorButton)
        
    def __loadHotkey(self, item, label, dialog, clearButton):
        dialog.load(item)
        if item.enabled:
            key = str(item.hotKey.encode("utf-8"))
            label.setText(self.build_hotkey_string(key, item.modifiers))
            clearButton.setEnabled(True)
            return True
        else:
            label.setText(i18n("(None configured)"))
            clearButton.setEnabled(False)
            return False

        
    def save(self):
        self.showConfigDlg.save(self.configManager.configHotkey)
        self.configManager.configHotkey.enabled = self.useConfigHotkey
        
        self.toggleMonitorDlg.save(self.configManager.toggleServiceHotkey)
        self.configManager.toggleServiceHotkey.enabled = self.useServiceHotkey
        
        self.configManager.config_altered()
    
    def build_hotkey_string(self, key, modifiers):
        hotkey = ""

        for modifier in modifiers:
            hotkey += modifier
            hotkey += "+"

        if key in self.KEY_MAP:
            keyText = self.KEY_MAP[key]
        else:
            keyText = key
        hotkey += keyText     
        
        return hotkey
        
    # ---- Signal handlers
    
    def on_setConfigButton_pressed(self):    
        self.showConfigDlg.exec_()
        
        if self.showConfigDlg.result() == QDialog.Accepted:
            self.useConfigHotkey = True
            key = self.showConfigDlg.key
            modifiers = self.showConfigDlg.build_modifiers()
            self.configKeyLabel.setText(self.build_hotkey_string(key, modifiers))
            self.clearConfigButton.setEnabled(True)
            
    def on_clearConfigButton_pressed(self):
        self.useConfigHotkey = False
        self.clearConfigButton.setEnabled(False)
        self.configKeyLabel.setText(i18n("(None configured)"))
        self.showConfigDlg.reset()


    def on_setMonitorButton_pressed(self):
        self.toggleMonitorDlg.exec_()
        
        if self.toggleMonitorDlg.result() == QDialog.Accepted:
            self.useServiceHotkey = True
            key = self.toggleMonitorDlg.key
            modifiers = self.toggleMonitorDlg.build_modifiers()
            self.monitorKeyLabel.setText(self.build_hotkey_string(key, modifiers))
            self.clearMonitorButton.setEnabled(True)
            
    def on_clearMonitorButton_pressed(self):
        self.useServiceHotkey = False
        self.clearMonitorButton.setEnabled(False)
        self.monitorKeyLabel.setText(i18n("(None configured)"))
        self.toggleMonitorDlg.reset()


class InterfaceSettings(QWidget, interfacesettings.Ui_Form):

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        interfacesettings.Ui_Form.__init__(self)
        self.setupUi(self)
        
        self.xRecordButton.setChecked(ConfigManager.SETTINGS[INTERFACE_TYPE] == iomediator.X_RECORD_INTERFACE)
        self.xRecordButton.setEnabled(interface.HAS_RECORD)
        self.xEvdevButton.setChecked(ConfigManager.SETTINGS[INTERFACE_TYPE] == iomediator.X_EVDEV_INTERFACE)
        self.atspiButton.setChecked(ConfigManager.SETTINGS[INTERFACE_TYPE] == iomediator.ATSPI_INTERFACE)
        self.atspiButton.setEnabled(interface.HAS_ATSPI)
        
        self.checkBox.setChecked(ConfigManager.SETTINGS[ENABLE_QT4_WORKAROUND])
        
    def save(self):
        if self.xRecordButton.isChecked():
            ConfigManager.SETTINGS[INTERFACE_TYPE] = iomediator.X_RECORD_INTERFACE
        elif self.xEvdevButton.isChecked():
            ConfigManager.SETTINGS[INTERFACE_TYPE] = iomediator.X_EVDEV_INTERFACE
        else:
            ConfigManager.SETTINGS[INTERFACE_TYPE] = iomediator.ATSPI_INTERFACE 
            
        ConfigManager.SETTINGS[ENABLE_QT4_WORKAROUND] = self.checkBox.isChecked()

class SettingsDialog(KPageDialog):
    
    def __init__(self, parent):
        KPageDialog.__init__(self, parent)
        self.app = parent.topLevelWidget().app # Used by GlobalHotkeyDialog
        
        self.genPage = self.addPage(GeneralSettings(self), i18n("General"))
        self.genPage.setIcon(KIcon("preferences-other"))
        
        self.hkPage = self.addPage(SpecialHotkeySettings(self, parent.app.configManager), i18n("Special Hotkeys"))
        self.hkPage.setIcon(KIcon("preferences-desktop-keyboard"))
        
        self.iPage = self.addPage(InterfaceSettings(self), i18n("Interface"))
        self.iPage.setIcon(KIcon("preferences-system"))
        
        self.setCaption(i18n("Advanced Settings"))
        
    def slotButtonClicked(self, button):
        if button == KDialog.Ok:
            self.genPage.widget().save()
            self.hkPage.widget().save()
            self.iPage.widget().save()
        KDialog.slotButtonClicked(self, button)
