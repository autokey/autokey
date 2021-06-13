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


from PyQt5.QtWidgets import QDialog

import autokey.model.helpers
import autokey.model.modelTypes
from autokey.qtui.common import inherits_from_ui_file_with_name
from autokey.qtui.dialogs import HotkeySettingsDialog, AbbrSettingsDialog, WindowFilterSettingsDialog



class SettingsWidget(*inherits_from_ui_file_with_name("settingswidget")):
    """
    The SettingsWidget is used to configure model items. It allows display, assigning and clearing of abbreviations,
    hotkeys and window filters.
    """

    KEY_MAP = HotkeySettingsDialog.KEY_MAP
    REVERSE_KEY_MAP = HotkeySettingsDialog.REVERSE_KEY_MAP

    def __init__(self, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)

        self.abbr_settings_dialog = AbbrSettingsDialog(self)
        self.hotkey_settings_dialog = HotkeySettingsDialog(self)
        self.window_filter_dialog = WindowFilterSettingsDialog(self)
        self.current_item = None  # type: autokey.model.modelTypes.Item
        self.abbreviation_enabled = False
        self.hotkey_enabled = False
        self.window_filter_enabled = False

    def load(self, item: autokey.model.modelTypes.Item):
        self.current_item = item
        self._load_abbreviation_data(item)
        self._load_hotkey_data(item)
        self._load_window_filter_data(item)

    def _load_abbreviation_data(self, item: autokey.model.modelTypes.Item):
        self.abbr_settings_dialog.load(item)
        item_has_abbreviation = autokey.model.helpers.TriggerMode.ABBREVIATION in item.modes
        self.abbreviation_label.setText(item.get_abbreviations() if item_has_abbreviation else "(None configured)")
        self.clear_abbreviation_button.setEnabled(item_has_abbreviation)
        self.abbreviation_enabled = item_has_abbreviation

    def _load_hotkey_data(self, item: autokey.model.modelTypes.Item):
        self.hotkey_settings_dialog.load(item)
        item_has_hotkey = autokey.model.helpers.TriggerMode.HOTKEY in item.modes
        self.hotkey_label.setText(item.get_hotkey_string() if item_has_hotkey else "(None configured)")
        self.clear_hotkey_button.setEnabled(item_has_hotkey)
        self.hotkey_enabled = item_has_hotkey

    def _load_window_filter_data(self, item: autokey.model.modelTypes.Item):
        self.window_filter_dialog.load(item)
        item_has_window_filter = item.has_filter() or item.inherits_filter()
        self.window_filter_label.setText(item.get_filter_regex() if item_has_window_filter else "(None configured)")
        self.window_filter_enabled = item_has_window_filter
        self.clear_window_filter_button.setEnabled(item_has_window_filter)

        if item.inherits_filter():
            # Inherited window filters can’t be deleted on specific items.
            self.clear_window_filter_button.setEnabled(False)
            self.window_filter_enabled = False

    def save(self):
        # Perform hotkey ungrab
        if autokey.model.helpers.TriggerMode.HOTKEY in self.current_item.modes:
            self.window().app.hotkey_removed(self.current_item)

        self.current_item.set_modes([])
        if self.abbreviation_enabled:
            self.abbr_settings_dialog.save(self.current_item)
        if self.hotkey_enabled:
            self.hotkey_settings_dialog.save(self.current_item)
        else:
            self.currentItem.unset_hotkey()
        if self.window_filter_enabled:
            self.window_filter_dialog.save(self.current_item)
        else:
            self.current_item.set_window_titles(None)

        if self.hotkey_enabled:
            self.window().app.hotkey_created(self.current_item)

    def set_dirty(self):
        self.window().set_dirty()

    def validate(self):
        # Start by getting all applicable information
        if self.abbreviation_enabled:
            abbreviations = self.abbr_settings_dialog.get_abbrs()
        else:
            abbreviations = []

        if self.hotkey_enabled:
            modifiers = self.hotkey_settings_dialog.build_modifiers()
            key = self.hotkey_settings_dialog.key
        else:
            modifiers = []
            key = None

        filter_expression = None
        if self.window_filter_enabled:
            filter_expression = self.window_filter_dialog.get_filter_text()
        elif self.current_item.parent is not None:
            r = self.current_item.parent.get_applicable_regex(True)
            if r is not None:
                filter_expression = r.pattern

        # Validate
        ret = []

        config_manager = self.window().app.configManager

        for abbr in abbreviations:
            unique, conflicting = config_manager.check_abbreviation_unique(abbr, filter_expression, self.current_item)
            if not unique:
                f = conflicting.get_applicable_regex()
                # TODO: i18n
                if f is None:
                    msg = "The abbreviation {abbreviation} is already in use by the {conflicting_item}.".format(
                            abbreviation=abbr,
                            conflicting_item=str(conflicting)
                            )
                else:
                    msg = "The abbreviation {abbreviation} is already in use by the {conflicting_item} " \
                          "for windows matching '{matching_pattern}'.".format(
                            abbreviation=abbr,
                            conflicting_item=str(conflicting),
                            matching_pattern=f.pattern
                            )
                ret.append(msg)

        unique, conflicting = config_manager.check_hotkey_unique(modifiers, key, filter_expression, self.current_item)
        if not unique:
            f = conflicting.get_applicable_regex()
            # TODO: i18n
            if f is None:
                msg = "The hotkey '{hotkey}' is already in use by the {conflicting_item}.".format(
                        hotkey=conflicting.get_hotkey_string(),
                        conflicting_item=str(conflicting)
                        )
            else:
                msg = "The hotkey '{hotkey}' is already in use by the {conflicting_item} " \
                      "for windows matching '{matching_pattern}.".format(
                        hotkey=conflicting.get_hotkey_string(),
                        conflicting_item=str(conflicting),
                        matching_pattern=f.pattern
                        )
            ret.append(msg)

        return ret

    # ---- Signal handlers

    def on_set_abbreviation_button_pressed(self):
        self.abbr_settings_dialog.exec_()

        if self.abbr_settings_dialog.result() == QDialog.Accepted:
            self.set_dirty()
            self.abbreviation_enabled = True
            self.abbreviation_label.setText(self.abbr_settings_dialog.get_abbrs_readable())
            self.clear_abbreviation_button.setEnabled(True)

    def on_clear_abbreviation_button_pressed(self):
        self.set_dirty()
        self.abbreviation_enabled = False
        self.clear_abbreviation_button.setEnabled(False)
        self.abbreviation_label.setText("(None configured)")  # TODO: i18n
        self.abbr_settings_dialog.reset()

    def on_set_hotkey_button_pressed(self):
        self.hotkey_settings_dialog.exec_()

        if self.hotkey_settings_dialog.result() == QDialog.Accepted:
            self.set_dirty()
            self.hotkey_enabled = True
            key = self.hotkey_settings_dialog.key
            modifiers = self.hotkey_settings_dialog.build_modifiers()
            self.hotkey_label.setText(self.current_item.get_hotkey_string(key, modifiers))
            self.clear_hotkey_button.setEnabled(True)

    def on_clear_hotkey_button_pressed(self):
        self.set_dirty()
        self.hotkey_enabled = False
        self.clear_hotkey_button.setEnabled(False)
        self.hotkey_label.setText("(None configured)")  # TODO: i18n
        self.hotkey_settings_dialog.reset()

    def on_set_window_filter_button_pressed(self):
        self.window_filter_dialog.exec_()

        if self.window_filter_dialog.result() == QDialog.Accepted:
            self.set_dirty()
            filter_text = self.window_filter_dialog.get_filter_text()
            if filter_text:
                self.window_filter_enabled = True
                self.clear_window_filter_button.setEnabled(True)
                self.window_filter_label.setText(filter_text)
            else:
                self.window_filter_enabled = False
                self.clear_window_filter_button.setEnabled(False)
                if self.current_item.inherits_filter():
                    text = self.current_item.parent.get_child_filter()
                else:
                    text = "(None configured)"  # TODO: i18n
                self.window_filter_label.setText(text)

    def on_clear_window_filter_button_pressed(self):
        self.set_dirty()
        self.window_filter_enabled = False
        self.clear_window_filter_button.setEnabled(False)
        if self.current_item.inherits_filter():
            text = self.current_item.parent.get_child_filter()
        else:
            text = "(None configured)"  # TODO: i18n
        self.window_filter_label.setText(text)
        self.window_filter_dialog.reset()
