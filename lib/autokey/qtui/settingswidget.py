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

from .common import inherits_from_ui_file_with_name
from .dialogs import HotkeySettingsDialog, AbbrSettingsDialog, WindowFilterSettingsDialog

from .. import model


class SettingsWidget(*inherits_from_ui_file_with_name("settingswidget")):

    KEY_MAP = HotkeySettingsDialog.KEY_MAP
    REVERSE_KEY_MAP = HotkeySettingsDialog.REVERSE_KEY_MAP

    def __init__(self, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)

        self.abbrDialog = AbbrSettingsDialog(self)
        self.hotkeyDialog = HotkeySettingsDialog(self)
        self.filterDialog = WindowFilterSettingsDialog(self)

    def load(self, item):
        self.currentItem = item

        self.abbrDialog.load(self.currentItem)
        if model.TriggerMode.ABBREVIATION in item.modes:
            self.abbrLabel.setText(item.get_abbreviations())
            self.clearAbbrButton.setEnabled(True)
            self.abbrEnabled = True
        else:
            self.abbrLabel.setText("(None configured)")  # TODO: i18n
            self.clearAbbrButton.setEnabled(False)
            self.abbrEnabled = False

        self.hotkeyDialog.load(self.currentItem)
        if model.TriggerMode.HOTKEY in item.modes:
            self.hotkeyLabel.setText(item.get_hotkey_string())
            self.clearHotkeyButton.setEnabled(True)
            self.hotkeyEnabled = True
        else:
            self.hotkeyLabel.setText("(None configured)")  # TODO: i18n
            self.clearHotkeyButton.setEnabled(False)
            self.hotkeyEnabled = False

        self.filterDialog.load(self.currentItem)
        self.filterEnabled = False
        self.clearFilterButton.setEnabled(False)
        if item.has_filter() or item.inherits_filter():
            self.windowFilterLabel.setText(item.get_filter_regex())

            if not item.inherits_filter():
                self.clearFilterButton.setEnabled(True)
                self.filterEnabled = True

        else:
            self.windowFilterLabel.setText("(None configured)")  # TODO: i18n

    def save(self):
        # Perform hotkey ungrab
        if model.TriggerMode.HOTKEY in self.currentItem.modes:
            self.window().app.hotkey_removed(self.currentItem)

        self.currentItem.set_modes([])
        if self.abbrEnabled:
            self.abbrDialog.save(self.currentItem)
        if self.hotkeyEnabled:
            self.hotkeyDialog.save(self.currentItem)
        if self.filterEnabled:
            self.filterDialog.save(self.currentItem)
        else:
            self.currentItem.set_window_titles(None)

        if self.hotkeyEnabled:
            self.window().app.hotkey_created(self.currentItem)

    def set_dirty(self):
        self.window().set_dirty()

    def validate(self):
        # Start by getting all applicable information
        if self.abbrEnabled:
            abbreviations = self.abbrDialog.get_abbrs()
        else:
            abbreviations = []

        if self.hotkeyEnabled:
            modifiers = self.hotkeyDialog.build_modifiers()
            key = self.hotkeyDialog.key
        else:
            modifiers = []
            key = None

        filterExpression = None
        if self.filterEnabled:
            filterExpression = self.filterDialog.get_filter_text()
        elif self.currentItem.parent is not None:
            r = self.currentItem.parent.get_applicable_regex(True)
            if r is not None:
                filterExpression = r.pattern

        # Validate
        ret = []

        configManager = self.window().app.configManager

        for abbr in abbreviations:
            unique, conflicting = configManager.check_abbreviation_unique(abbr, filterExpression, self.currentItem)
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

        unique, conflicting = configManager.check_hotkey_unique(modifiers, key, filterExpression, self.currentItem)
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

    def on_setAbbrButton_pressed(self):
        self.abbrDialog.exec_()

        if self.abbrDialog.result() == QDialog.Accepted:
            self.set_dirty()
            self.abbrEnabled = True
            self.abbrLabel.setText(self.abbrDialog.get_abbrs_readable())
            self.clearAbbrButton.setEnabled(True)

    def on_clearAbbrButton_pressed(self):
        self.set_dirty()
        self.abbrEnabled = False
        self.clearAbbrButton.setEnabled(False)
        self.abbrLabel.setText("(None configured)")  # TODO: i18n
        self.abbrDialog.reset()

    def on_setHotkeyButton_pressed(self):
        self.hotkeyDialog.exec_()

        if self.hotkeyDialog.result() == QDialog.Accepted:
            self.set_dirty()
            self.hotkeyEnabled = True
            key = self.hotkeyDialog.key
            modifiers = self.hotkeyDialog.build_modifiers()
            self.hotkeyLabel.setText(self.currentItem.get_hotkey_string(key, modifiers))
            self.clearHotkeyButton.setEnabled(True)

    def on_clearHotkeyButton_pressed(self):
        self.set_dirty()
        self.hotkeyEnabled = False
        self.clearHotkeyButton.setEnabled(False)
        self.hotkeyLabel.setText("(None configured)")  # TODO: i18n
        self.hotkeyDialog.reset()

    def on_setFilterButton_pressed(self):
        self.filterDialog.exec_()

        if self.filterDialog.result() == QDialog.Accepted:
            self.set_dirty()
            filterText = self.filterDialog.get_filter_text()
            if filterText != "":
                self.filterEnabled = True
                self.clearFilterButton.setEnabled(True)
                self.windowFilterLabel.setText(filterText)
            else:
                self.filterEnabled = False
                self.clearFilterButton.setEnabled(False)
                if self.currentItem.inherits_filter():
                    text = self.currentItem.parent.get_child_filter()
                else:
                    text = "(None configured)"  # TODO: i18n
                self.windowFilterLabel.setText(text)

    def on_clearFilterButton_pressed(self):
        self.set_dirty()
        self.filterEnabled = False
        self.clearFilterButton.setEnabled(False)
        if self.currentItem.inherits_filter():
            text = self.currentItem.parent.get_child_filter()
        else:
            text = "(None configured)"  # TODO: i18n
        self.windowFilterLabel.setText(text)
        self.filterDialog.reset()
