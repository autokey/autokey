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

import sys
from gi.repository import Gtk, GtkSource


import autokey.configmanager.autostart
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants
from autokey import common
from autokey.model.key import Key


from .dialogs import GlobalHotkeyDialog
from .shared import get_ui


ICON_NAME_MAP = {
                _("Light"): common.ICON_FILE_NOTIFICATION,
                _("Dark"): common.ICON_FILE_NOTIFICATION_DARK
                }

ICON_NAME_LIST = []

class SettingsDialog:
    
    KEY_MAP = GlobalHotkeyDialog.KEY_MAP
    REVERSE_KEY_MAP = GlobalHotkeyDialog.REVERSE_KEY_MAP
    
    def __init__(self, parent, configManager):
        builder = get_ui("settingsdialog.xml")
        self.ui = builder.get_object("settingsdialog")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        self.configManager = configManager
        
        # General Settings
        self.autoStartCheckbox = builder.get_object("autoStartCheckbox")
        self.autosaveCheckbox = builder.get_object("autosaveCheckbox")
        self.showTrayCheckbox = builder.get_object("showTrayCheckbox")
        self.disableCapslockCheckbox = builder.get_object("disableCapslockCheckbox")
        self.allowKbNavCheckbox = builder.get_object("allowKbNavCheckbox")
        self.allowKbNavCheckbox.hide()
        self.sortByUsageCheckbox = builder.get_object("sortByUsageCheckbox")
        # Added by Trey Blancher (ectospasm) 2015-09-16
        self.triggerItemByInitial = builder.get_object("triggerItemByInitial")
        self.enableUndoCheckbox = builder.get_object("enableUndoCheckbox")

        self.gtkThemeCombo = Gtk.ComboBoxText.new()
        hboxgtktheme = builder.get_object("hboxgtktheme")
        hboxgtktheme.pack_start(self.gtkThemeCombo, False, True, 0)
        hboxgtktheme.show_all()

        self.themeList = GtkSource.StyleSchemeManager().get_scheme_ids()
        for item in self.themeList:
            self.gtkThemeCombo.append_text(item)

        self.gtkThemeCombo.set_sensitive(cm.ConfigManager.SETTINGS[cm_constants.GTK_THEME])
        self.gtkThemeCombo.set_active(self.themeList.index(cm.ConfigManager.SETTINGS[cm_constants.GTK_THEME]))
        
        self.iconStyleCombo = Gtk.ComboBoxText.new()
        hbox = builder.get_object("hbox4")
        hbox.pack_start(self.iconStyleCombo, False, True, 0)
        hbox.show_all()
        
        for key, value in list(ICON_NAME_MAP.items()):
            self.iconStyleCombo.append_text(key)
            ICON_NAME_LIST.append(value)

        self.iconStyleCombo.set_sensitive(cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON])
        self.iconStyleCombo.set_active(ICON_NAME_LIST.index(cm.ConfigManager.SETTINGS[cm_constants.NOTIFICATION_ICON]))

        self.autoStartCheckbox.set_active(autokey.configmanager.autostart.get_autostart().desktop_file_name is not None)
        self.autosaveCheckbox.set_active(not cm.ConfigManager.SETTINGS[cm_constants.PROMPT_TO_SAVE])
        self.showTrayCheckbox.set_active(cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON])
        self.disableCapslockCheckbox.set_active(cm.ConfigManager.is_modifier_disabled(Key.CAPSLOCK))

        # self.allowKbNavCheckbox.set_active(cm.ConfigManager.SETTINGS[MENU_TAKES_FOCUS])
        # Added by Trey Blancher (ectospasm) 2015-09-16
        self.triggerItemByInitial.set_active(cm.ConfigManager.SETTINGS[cm_constants.TRIGGER_BY_INITIAL])
        self.sortByUsageCheckbox.set_active(cm.ConfigManager.SETTINGS[cm_constants.SORT_BY_USAGE_COUNT])
        self.enableUndoCheckbox.set_active(cm.ConfigManager.SETTINGS[cm_constants.UNDO_USING_BACKSPACE])

        # Hotkeys
        self.showConfigDlg = GlobalHotkeyDialog(parent, configManager, self.on_config_response)
        self.toggleMonitorDlg = GlobalHotkeyDialog(parent, configManager, self.on_monitor_response)
        self.configKeyLabel = builder.get_object("configKeyLabel")
        self.clearConfigButton = builder.get_object("clearConfigButton")
        self.monitorKeyLabel = builder.get_object("monitorKeyLabel")
        self.clearMonitorButton = builder.get_object("clearMonitorButton")    
        
        self.useConfigHotkey = self.__loadHotkey(configManager.configHotkey, self.configKeyLabel, 
                                                 self.showConfigDlg, self.clearConfigButton)
        self.useServiceHotkey = self.__loadHotkey(configManager.toggleServiceHotkey, self.monitorKeyLabel, 
                                                  self.toggleMonitorDlg, self.clearMonitorButton)
                                                    
        # Script Engine Settings
        self.userModuleChooserButton = builder.get_object("userModuleChooserButton")
        if configManager.userCodeDir is not None:
            self.userModuleChooserButton.set_current_folder(configManager.userCodeDir)
            if configManager.userCodeDir in sys.path:
                sys.path.remove(configManager.userCodeDir)

    def on_save(self, widget, data=None):
        if self.autoStartCheckbox.get_active():
            autokey.configmanager.autostart.set_autostart_entry(
                autokey.configmanager.autostart.AutostartSettings("autokey-gtk.desktop", False))
        else:
            autokey.configmanager.autostart.delete_autostart_entry()


        #promptToSaveCheckbox no longer exists? This prevented saving in the Preferences window from what I can tell
        #cm.ConfigManager.SETTINGS[cm_constants.PROMPT_TO_SAVE] = not self.promptToSaveCheckbox.get_active()
        cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON] = self.showTrayCheckbox.get_active()
        cm.ConfigManager.SETTINGS[cm_constants.GTK_THEME] = self.gtkThemeCombo.get_active_text()
        #cm.ConfigManager.SETTINGS[MENU_TAKES_FOCUS] = self.allowKbNavCheckbox.get_active()
        cm.ConfigManager.SETTINGS[cm_constants.SORT_BY_USAGE_COUNT] = self.sortByUsageCheckbox.get_active()
        # Added by Trey Blancher (ectospasm) 2015-09-16
        cm.ConfigManager.SETTINGS[cm_constants.TRIGGER_BY_INITIAL] = self.triggerItemByInitial.get_active()
        cm.ConfigManager.SETTINGS[cm_constants.UNDO_USING_BACKSPACE] = self.enableUndoCheckbox.get_active()
        cm.ConfigManager.SETTINGS[cm_constants.NOTIFICATION_ICON] = ICON_NAME_MAP[self.iconStyleCombo.get_active_text()]
        self._save_disable_capslock_setting()
        self.configManager.userCodeDir = self.userModuleChooserButton.get_current_folder()
        sys.path.append(self.configManager.userCodeDir)
        
        configHotkey = self.configManager.configHotkey
        toggleHotkey = self.configManager.toggleServiceHotkey
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
            
        app.update_notifier_visibility()            
        self.configManager.config_altered(True)
        
        self.hide()
        self.destroy()

    def _save_disable_capslock_setting(self):
        # Only update the modifier key handling if the value changed.
        if self.disableCapslockCheckbox.get_active() and not cm.ConfigManager.is_modifier_disabled(Key.CAPSLOCK):
            cm.ConfigManager.disable_modifier(Key.CAPSLOCK)
        elif not self.disableCapslockCheckbox.get_active() and cm.ConfigManager.is_modifier_disabled(Key.CAPSLOCK):
            cm.ConfigManager.enable_modifier(Key.CAPSLOCK)

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

    def on_showTrayCheckbox_toggled(self, widget, data=None):
        self.iconStyleCombo.set_sensitive(widget.get_active())
    
    def on_setConfigButton_pressed(self, widget, data=None):
        self.showConfigDlg.run()
         
    def on_config_response(self, res):
        if res == Gtk.ResponseType.OK:
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
        if res == Gtk.ResponseType.OK:
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

