# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QComboBox

from autokey import configmanager as cm

import autokey.qtui.common

logger = autokey.qtui.common.logger.getChild("General settings widget")  # type: logging.Logger


class GeneralSettings(*autokey.qtui.common.inherits_from_ui_file_with_name("generalsettings")):
    """This widget implements the "general settings" widget and is used in the settings dialog."""
    GUI_TABLE = (("autokey-qt.desktop", "Qt5"),
                 ("autokey-gtk.desktop", "GTK+")
                 )

    def __init__(self, parent: QWidget=None):
        super(GeneralSettings, self).__init__(parent)
        self.setupUi(self)

        self.prompt_to_save_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm.PROMPT_TO_SAVE])
        self.show_tray_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON])
        # self.allow_kb_nav_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm.MENU_TAKES_FOCUS])
        self.allow_kb_nav_checkbox.setVisible(False)
        self.sort_by_usage_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm.SORT_BY_USAGE_COUNT])
        self.enable_undo_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm.UNDO_USING_BACKSPACE])
        self._fill_autostart_gui_selection_combobox()
        self.autostart_settings = cm.get_autostart()
        self._load_autostart_settings()
        logger.debug("Created widget and loaded current settings: " + self._settings_str())

    def save(self):
        """Called by the parent settings dialog when the user clicks on the Save button.
        Stores the current settings in the ConfigManager."""
        logger.debug("User requested to save settings. New settings: " + self._settings_str())
        cm.ConfigManager.SETTINGS[cm.PROMPT_TO_SAVE] = self.prompt_to_save_checkbox.isChecked()
        cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON] = self.show_tray_checkbox.isChecked()
        # cm.ConfigManager.SETTINGS[cm.MENU_TAKES_FOCUS] = self.allow_kb_nav_checkbox.isChecked()
        cm.ConfigManager.SETTINGS[cm.SORT_BY_USAGE_COUNT] = self.sort_by_usage_checkbox.isChecked()
        cm.ConfigManager.SETTINGS[cm.UNDO_USING_BACKSPACE] = self.enable_undo_checkbox.isChecked()
        self._save_autostart_settings()

    def _settings_str(self):
        """Returns a human readable settings representation for logging purposes."""
        settings = "Prompt to save: {}, " \
            "Show tray icon: {}, " \
            "Allow keyboard navigation: {}, " \
            "Sort by usage count: {}, " \
            "Enable undo using backspace: {}".format(
               self.prompt_to_save_checkbox.isChecked(),
               self.show_tray_checkbox.isChecked(),
               self.allow_kb_nav_checkbox.isChecked(),
               self.sort_by_usage_checkbox.isChecked(),
               self.enable_undo_checkbox.isChecked()
            )
        return settings

    def _fill_autostart_gui_selection_combobox(self):
        combobox = self.autostart_interface_choice_combobox  # type: QComboBox
        for desktop_file, name in GeneralSettings.GUI_TABLE:
            try:
                cm.get_source_desktop_file(desktop_file)
            except FileNotFoundError:
                # Skip unavailable GUIs
                pass
            else:
                combobox.addItem(name, desktop_file)

    def _load_autostart_settings(self):
        combobox = self.autostart_interface_choice_combobox  # type: QComboBox
        self.autostart_groupbox.setChecked(self.autostart_settings.desktop_file_name is not None)
        if self.autostart_settings.desktop_file_name is not None:
            combobox.setCurrentIndex(combobox.findData(self.autostart_settings.desktop_file_name))
        self.autostart_show_main_window_checkbox.setChecked(self.autostart_settings.switch_show_configure)

    def _save_autostart_settings(self):
        combobox = self.autostart_interface_choice_combobox  # type: QComboBox
        desktop_entry = None if not self.autostart_groupbox.isChecked() else combobox.currentData(Qt.UserRole)
        show_main_window = self.autostart_show_main_window_checkbox.isChecked()
        new_settings = cm.AutostartSettings(desktop_entry, show_main_window)
        if new_settings != self.autostart_settings:
            # Only write if settings changed to preserve eventual user-made modifications.
            cm.set_autostart_entry(new_settings)
