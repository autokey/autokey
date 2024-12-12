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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QComboBox


import autokey.configmanager.autostart
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants

from autokey.model.key import Key


import autokey.qtui.common as ui_common
import autokey.common as common

logger = __import__("autokey.logger").logger.get_logger(__name__)


class GeneralSettings(*ui_common.inherits_from_ui_file_with_name("generalsettings")):
    """This widget implements the "general settings" widget and is used in the settings dialog."""
    GUI_TABLE = (
        ("autokey-qt.desktop", "Qt5"),
        ("autokey-gtk.desktop", "GTK+")
    )

    ICON_TABLE = (
        (0, common.ICON_FILE_NOTIFICATION),
        (1, common.ICON_FILE_NOTIFICATION_DARK)
    )

    def __init__(self, parent: QWidget=None):
        super(GeneralSettings, self).__init__(parent)
        self.setupUi(self)

        self.autosave_checkbox.setChecked(not cm.ConfigManager.SETTINGS[cm_constants.PROMPT_TO_SAVE])
        self.show_tray_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON])
        # self.allow_kb_nav_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm.MENU_TAKES_FOCUS])
        self.allow_kb_nav_checkbox.setVisible(False)

        self.sort_by_usage_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm_constants.SORT_BY_USAGE_COUNT])
        self.enable_undo_checkbox.setChecked(cm.ConfigManager.SETTINGS[cm_constants.UNDO_USING_BACKSPACE])
        self.disable_capslock_checkbox.setChecked(cm.ConfigManager.is_modifier_disabled(Key.CAPSLOCK))

        self._fill_notification_icon_combobox_user_data()
        self._load_system_tray_icon_theme()
        self._fill_autostart_gui_selection_combobox()
        self.autostart_settings = autokey.configmanager.autostart.get_autostart()
        self._load_autostart_settings()
        logger.debug("Created widget and loaded current settings: " + self._settings_str())

    def save(self):
        """Called by the parent settings dialog when the user clicks on the Save button.
        Stores the current settings in the ConfigManager."""
        logger.debug("User requested to save settings. New settings: " + self._settings_str())

        cm.ConfigManager.SETTINGS[cm_constants.PROMPT_TO_SAVE] = not self.autosave_checkbox.isChecked()
        cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON] = self.show_tray_checkbox.isChecked()
        # cm.ConfigManager.SETTINGS[cm_constants.MENU_TAKES_FOCUS] = self.allow_kb_nav_checkbox.isChecked()
        cm.ConfigManager.SETTINGS[cm_constants.SORT_BY_USAGE_COUNT] = self.sort_by_usage_checkbox.isChecked()
        cm.ConfigManager.SETTINGS[cm_constants.UNDO_USING_BACKSPACE] = self.enable_undo_checkbox.isChecked()
        cm.ConfigManager.SETTINGS[cm_constants.NOTIFICATION_ICON] = \
            self.system_tray_icon_theme_combobox.currentData(Qt.UserRole)
        self._save_disable_capslock_setting()

        self._save_autostart_settings()
        # TODO: After saving the notification icon, apply it to the currently running instance.

    def _save_disable_capslock_setting(self):
        # Only update the modifier key handling if the value changed.
        if self.disable_capslock_checkbox.isChecked() and not cm.ConfigManager.is_modifier_disabled(Key.CAPSLOCK):
            cm.ConfigManager.disable_modifier(Key.CAPSLOCK)
        elif not self.disable_capslock_checkbox.isChecked() and cm.ConfigManager.is_modifier_disabled(Key.CAPSLOCK):
            cm.ConfigManager.enable_modifier(Key.CAPSLOCK)

    def _settings_str(self):
        """Returns a human readable settings representation for logging purposes."""
        settings = "Automatically save changes: {}, " \
            "Show tray icon: {}, " \
            "Allow keyboard navigation: {}, " \
            "Sort by usage count: {}, " \
            "Enable undo using backspace: {}, " \
            "Tray icon theme: {}, " \
            "Disable Capslock: {}".format(
               self.autosave_checkbox.isChecked(),
               self.show_tray_checkbox.isChecked(),
               self.allow_kb_nav_checkbox.isChecked(),
               self.sort_by_usage_checkbox.isChecked(),
               self.enable_undo_checkbox.isChecked(),
               self.system_tray_icon_theme_combobox.currentData(Qt.UserRole),
               self.disable_capslock_checkbox.isChecked()
            )
        return settings

    def _fill_autostart_gui_selection_combobox(self):
        combobox = self.autostart_interface_choice_combobox  # type: QComboBox
        for desktop_file, name in GeneralSettings.GUI_TABLE:
            try:
                autokey.configmanager.autostart.get_source_desktop_file(desktop_file)
            except FileNotFoundError:
                # Skip unavailable GUIs
                pass
            else:
                combobox.addItem(name, desktop_file)

    def _fill_notification_icon_combobox_user_data(self):
        combo_box = self.system_tray_icon_theme_combobox  # type: QComboBox
        for index, icon_name in GeneralSettings.ICON_TABLE:
            combo_box.setItemData(index, icon_name, Qt.UserRole)

    def _load_system_tray_icon_theme(self):
        combo_box = self.system_tray_icon_theme_combobox  # type: QComboBox
        data = cm.ConfigManager.SETTINGS[cm_constants.NOTIFICATION_ICON]
        combo_box_index = combo_box.findData(data, Qt.UserRole)
        if combo_box_index == -1:
            # Invalid data in user configuration. TODO: should this be a warning or error?
            # Just revert to theme at index 0 (light)
            combo_box_index = 0
        combo_box.setCurrentIndex(combo_box_index)

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
        new_settings = autokey.configmanager.autostart.AutostartSettings(desktop_entry, show_main_window)
        if new_settings != self.autostart_settings:
            # Only write if settings changed to preserve eventual user-made modifications.
            autokey.configmanager.autostart.set_autostart_entry(new_settings)
