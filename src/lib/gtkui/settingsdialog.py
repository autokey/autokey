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

import gtk, shutil, os, sys

from autokey.configmanager import *
from autokey import iomediator, interface, model, common
from dialogs import GlobalHotkeyDialog
import configwindow

DESKTOP_FILE = "/usr/share/applications/autokey-gtk.desktop"
AUTOSTART_FILE = os.path.expanduser("~/.config/autostart/autokey-gtk.desktop")

"""ICON_NAME_MAP = {
                _("Default") : common.ICON_FILE,
                _("Grayscale") : common.ICON_FILE_GRAYSCALE
                }

ICON_NAME_LIST = []"""

class SettingsDialog:
    
    KEY_MAP = GlobalHotkeyDialog.KEY_MAP
    REVERSE_KEY_MAP = GlobalHotkeyDialog.REVERSE_KEY_MAP
    
    def __init__(self, parent, configManager):
        builder = configwindow.get_ui("settingsdialog.xml")
        self.ui = builder.get_object("settingsdialog")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        self.configManager = configManager
        
        # General Settings
        self.autoStartCheckbox = builder.get_object("autoStartCheckbox")
        self.promptToSaveCheckbox = builder.get_object("promptToSaveCheckbox")
        self.showTrayCheckbox = builder.get_object("showTrayCheckbox")
        self.allowKbNavCheckbox = builder.get_object("allowKbNavCheckbox")
        self.allowKbNavCheckbox.hide()
        self.sortByUsageCheckbox = builder.get_object("sortByUsageCheckbox")
        self.enableUndoCheckbox = builder.get_object("enableUndoCheckbox")
        
        #self.notifyIconCombo = gtk.combo_box_new_text()
        hbox = builder.get_object("hbox4")
        #hbox.pack_start(self.notifyIconCombo, False)
        hbox.show_all()
        
        #for key, value in ICON_NAME_MAP.items():
        #    self.notifyIconCombo.append_text(key)
        #    ICON_NAME_LIST.append(value)
        #self.notifyIconCombo.set_sensitive(ConfigManager.SETTINGS[SHOW_TRAY_ICON])
        #self.notifyIconCombo.hide()
        builder.get_object("label18").hide()
        #self.notifyIconCombo.set_active(ICON_NAME_LIST.index(ConfigManager.SETTINGS[NOTIFICATION_ICON]))
        
        self.autoStartCheckbox.set_active(os.path.exists(AUTOSTART_FILE))
        self.promptToSaveCheckbox.set_active(ConfigManager.SETTINGS[PROMPT_TO_SAVE])
        self.showTrayCheckbox.set_active(ConfigManager.SETTINGS[SHOW_TRAY_ICON])
        #self.allowKbNavCheckbox.set_active(ConfigManager.SETTINGS[MENU_TAKES_FOCUS])
        self.sortByUsageCheckbox.set_active(ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT])
        self.enableUndoCheckbox.set_active(ConfigManager.SETTINGS[UNDO_USING_BACKSPACE])
        



        # Hotkeys
        self.showConfigDlg = GlobalHotkeyDialog(parent, configManager, self.on_config_response)
        self.toggleMonitorDlg = GlobalHotkeyDialog(parent, configManager, self.on_monitor_response)
        self.showPopupDlg = GlobalHotkeyDialog(parent, configManager, self.on_popup_response)
        self.configKeyLabel = builder.get_object("configKeyLabel")
        self.clearConfigButton = builder.get_object("clearConfigButton")
        self.monitorKeyLabel = builder.get_object("monitorKeyLabel")
        self.clearMonitorButton = builder.get_object("clearMonitorButton")
        self.popupKeyLabel = builder.get_object("popupKeyLabel")
        self.clearPopupButton = builder.get_object("clearPopupButton")        
        
        self.useConfigHotkey = self.__loadHotkey(configManager.configHotkey, self.configKeyLabel, 
                                                    self.showConfigDlg, self.clearConfigButton)
        self.useServiceHotkey = self.__loadHotkey(configManager.toggleServiceHotkey, self.monitorKeyLabel, 
                                                    self.toggleMonitorDlg, self.clearMonitorButton)                                                    
        self.usePopupHotkey = self.__loadHotkey(configManager.showPopupHotkey, self.popupKeyLabel, 
                                                    self.showPopupDlg, self.clearPopupButton)
                                                    
        # Script Engine Settings
        self.userModuleChooserButton = builder.get_object("userModuleChooserButton")
        if configManager.userCodeDir is not None:
            self.userModuleChooserButton.set_current_folder(configManager.userCodeDir)
            if configManager.userCodeDir in sys.path:
                sys.path.remove(configManager.userCodeDir)
        
        # Interface Settings
        self.xRecordButton = builder.get_object("xRecordButton")
        self.xEvdevButton = builder.get_object("xEvdevButton")
        self.atspiButton = builder.get_object("atspiButton")
        self.checkBox = builder.get_object("checkBox")
        
        self.xRecordButton.set_active(ConfigManager.SETTINGS[INTERFACE_TYPE] == iomediator.X_RECORD_INTERFACE)
        self.xRecordButton.set_sensitive(interface.HAS_RECORD)
        self.xEvdevButton.set_active(ConfigManager.SETTINGS[INTERFACE_TYPE] == iomediator.X_EVDEV_INTERFACE)
        self.atspiButton.set_active(ConfigManager.SETTINGS[INTERFACE_TYPE] == iomediator.ATSPI_INTERFACE)
        self.atspiButton.set_sensitive(interface.HAS_ATSPI)
        
        #self.checkBox.set_active(ConfigManager.SETTINGS[ENABLE_QT4_WORKAROUND])

    def on_save(self, widget, data=None):
        if self.autoStartCheckbox.get_active():
            if not os.path.exists(AUTOSTART_FILE):
                shutil.copy(DESKTOP_FILE, AUTOSTART_FILE)
        else:
            if os.path.exists(AUTOSTART_FILE):
                os.remove(AUTOSTART_FILE)
    
        ConfigManager.SETTINGS[PROMPT_TO_SAVE] = self.promptToSaveCheckbox.get_active()
        ConfigManager.SETTINGS[SHOW_TRAY_ICON] = self.showTrayCheckbox.get_active()
        #ConfigManager.SETTINGS[MENU_TAKES_FOCUS] = self.allowKbNavCheckbox.get_active()
        ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT] = self.sortByUsageCheckbox.get_active()
        ConfigManager.SETTINGS[UNDO_USING_BACKSPACE] = self.enableUndoCheckbox.get_active()
        #ConfigManager.SETTINGS[NOTIFICATION_ICON] = ICON_NAME_MAP[self.notifyIconCombo.get_active_text()]
        
        self.configManager.userCodeDir = self.userModuleChooserButton.get_current_folder()
        sys.path.append(self.configManager.userCodeDir)
        
        if self.xRecordButton.get_active():
            ConfigManager.SETTINGS[INTERFACE_TYPE] = iomediator.X_RECORD_INTERFACE
        elif self.xEvdevButton.get_active():
            ConfigManager.SETTINGS[INTERFACE_TYPE] = iomediator.X_EVDEV_INTERFACE
        else:
            ConfigManager.SETTINGS[INTERFACE_TYPE] = iomediator.ATSPI_INTERFACE 
            
        #ConfigManager.SETTINGS[ENABLE_QT4_WORKAROUND] = self.checkBox.get_active()
        
        configHotkey = self.configManager.configHotkey
        toggleHotkey = self.configManager.toggleServiceHotkey
        popupHotkey = self.configManager.showPopupHotkey
        app = self.configManager.app

        if configHotkey.enabled:
            app.hotkey_removed(configHotkey)
        configHotkey.enabled = self.useConfigHotkey
        if self.useConfigHotkey:
            self.showConfigDlg.save(configHotkey)
            app.hotkey_created(configHotkey)

        if toggleHotkey.enabled:
            app.hotkey_removed(toggleHotkey)
        toggleHotkey.enabled = self.useServiceHotkey
        if self.useServiceHotkey:
            self.toggleMonitorDlg.save(toggleHotkey)
            app.hotkey_created(toggleHotkey)
            
        if popupHotkey.enabled:
            app.hotkey_removed(popupHotkey)
        popupHotkey.enabled = self.usePopupHotkey
        if self.usePopupHotkey:
            self.showPopupDlg.save(popupHotkey)
            app.hotkey_created(popupHotkey)
            
        app.update_notifier_visibility()
            
        self.configManager.config_altered(True)
        
        self.hide()
        self.destroy()
        
    def on_cancel(self, widget, data=None):
        self.hide()
        self.destroy()
        
    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)
    
    def __loadHotkey(self, item, label, dialog, clearButton):
        dialog.load(item)
        if item.enabled:
            key = item.hotKey.encode("utf-8")
            label.set_text(item.get_hotkey_string())
            clearButton.set_sensitive(True)
            return True
        else:
            label.set_text(_("(None configured)"))
            clearButton.set_sensitive(False)
            return False
        
    # ---- Signal handlers

    #def on_showTrayCheckbox_toggled(self, widget, data=None):
    #    self.notifyIconCombo.set_sensitive(widget.get_active())
    
    def on_setConfigButton_pressed(self, widget, data=None):
        self.showConfigDlg.run()
         
    def on_config_response(self, res):
        if res == gtk.RESPONSE_OK:
            self.useConfigHotkey = True
            key = self.showConfigDlg.key
            modifiers = self.showConfigDlg.build_modifiers()
            self.configKeyLabel.set_text(self.build_hotkey_string(key, modifiers))
            self.clearConfigButton.set_sensitive(True)
            
    def on_clearConfigButton_pressed(self, widget, data=None):
        self.useConfigHotkey = False
        self.clearConfigButton.set_sensitive(False)
        self.configKeyLabel.set_text(_("(None configured)"))
        self.showConfigDlg.reset()

    def on_setMonitorButton_pressed(self, widget, data=None):
        self.toggleMonitorDlg.run()
        
    def on_monitor_response(self, res):
        if res == gtk.RESPONSE_OK:
            self.useServiceHotkey = True
            key = self.toggleMonitorDlg.key
            modifiers = self.toggleMonitorDlg.build_modifiers()
            self.monitorKeyLabel.set_text(self.build_hotkey_string(key, modifiers))
            self.clearMonitorButton.set_sensitive(True)
            
    def on_clearMonitorButton_pressed(self, widget, data=None):
        self.useServiceHotkey = False
        self.clearMonitorButton.set_sensitive(False)
        self.monitorKeyLabel.set_text(_("(None configured)"))
        self.toggleMonitorDlg.reset()

    def on_setPopupButton_pressed(self, widget, data=None):
        self.showPopupDlg.run()
        
    def on_popup_response(self, res):
        if res == gtk.RESPONSE_OK:
            self.usePopupHotkey = True
            key = self.showPopupDlg.key
            modifiers = self.showPopupDlg.build_modifiers()
            self.popupKeyLabel.set_text(self.build_hotkey_string(key, modifiers))
            self.clearPopupButton.set_sensitive(True)
            
    def on_clearPopupButton_pressed(self, widget, data=None):
        self.usePopupHotkey = False
        self.clearPopupButton.set_sensitive(False)
        self.popupKeyLabel.set_text(_("(None configured)"))
        self.showPopupDlg.reset()
