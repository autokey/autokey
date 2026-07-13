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


from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QSizePolicy

import autokey.model.helpers
import autokey.model.modelTypes
from autokey.iomediator.keygrabber import InlineKeyGrabber
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

        # Double-click shortcuts: skip the modal "Set..." dialogs and edit
        # the value in place.
        self._inline_hotkey_grabber = None
        self._inline_hotkey_preview = None  # type: typing.Optional[typing.Tuple[str, list]]
        self.hotkey_label.installEventFilter(self)
        self.window_filter_label.installEventFilter(self)

        # QStackedWidget/QLineEdit both report a much taller sizeHint than a
        # single line of text needs, and this row otherwise grabs a
        # disproportionate share of any extra vertical space the layout has
        # -- pin it to one line's worth of height regardless of which page
        # is showing.
        self.hotkey_value_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        single_line_height = max(self.hotkey_label.sizeHint().height(), self.hotkey_edit.sizeHint().height())
        self.hotkey_value_stack.setFixedHeight(single_line_height)

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
            self.current_item.unset_hotkey()
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

        filter_expression = self._current_filter_expression()

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

    def _current_filter_expression(self):
        if self.window_filter_enabled:
            return self.window_filter_dialog.get_filter_text()
        elif self.current_item.parent is not None:
            r = self.current_item.parent.get_applicable_regex(True)
            if r is not None:
                return r.pattern
        return None

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

    # ---- Double-click shortcuts (bypass the modal "Set..." dialogs) ----

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonDblClick:
            if obj is self.hotkey_label:
                self._start_inline_hotkey_edit()
                return True
            if obj is self.window_filter_label:
                self._start_inline_window_filter_detect()
                return True
        return super().eventFilter(obj, event)

    def _start_inline_hotkey_edit(self):
        self._inline_hotkey_preview = None
        self.hotkey_edit.setText("Press a key or combination…")  # TODO: i18n
        # Left enabled even with nothing previewed yet: _save_inline_hotkey()
        # no-ops without a preview, and a disabled button can't take Qt focus
        # -- which Tab needs to be able to hand focus to it.
        self.hotkey_save_button.setEnabled(True)
        self.hotkey_value_stack.setCurrentWidget(self.hotkey_edit_page)
        self._inline_hotkey_grabber = InlineKeyGrabber(self)
        self._inline_hotkey_grabber.start()

    def inline_hotkey_preview(self, raw_key, modifiers):
        """Called from the grabber (background thread) on every keypress."""
        display_key = self.KEY_MAP.get(raw_key, raw_key)
        self._inline_hotkey_preview = (display_key, modifiers)
        self.hotkey_edit.setText(self.current_item.get_hotkey_string(display_key, modifiers))

    def inline_hotkey_cancelled(self):
        """Called from the grabber on Escape, Backspace, or a stray click."""
        self._inline_hotkey_grabber = None
        self._inline_hotkey_preview = None
        self.hotkey_value_stack.setCurrentWidget(self.hotkey_label)

    def inline_hotkey_confirmed(self):
        """Called from the grabber when Enter/Return ends the capture (the
        grabber has already stopped itself by this point)."""
        self._inline_hotkey_grabber = None
        self._save_inline_hotkey()

    def inline_hotkey_tab_pressed(self):
        """Called from the grabber when Tab ends the capture. Unlike
        Escape/Backspace/Enter, this neither cancels nor saves -- it just
        releases the keyboard grab (already done by the caller) and hands
        focus to the Save button, like normal Tab-navigation would."""
        self._inline_hotkey_grabber = None
        self.hotkey_save_button.setFocus()

    def on_hotkey_save_button_pressed(self):
        """Mouse-driven equivalent of pressing Enter. Auto-wired by Qt
        Designer's connectSlotsByName from hotkey_save_button's clicked
        signal, matching this file's other on_..._pressed handlers."""
        if self._inline_hotkey_grabber is not None:
            self._inline_hotkey_grabber.stop()
            self._inline_hotkey_grabber = None
        self._save_inline_hotkey()

    def _save_inline_hotkey(self):
        if self._inline_hotkey_preview is None:
            self.hotkey_value_stack.setCurrentWidget(self.hotkey_label)
            return

        display_key, modifiers = self._inline_hotkey_preview
        self.hotkey_settings_dialog.set_key(display_key, modifiers)
        key = self.hotkey_settings_dialog.key
        modifiers = self.hotkey_settings_dialog.build_modifiers()

        filter_expression = self._current_filter_expression()
        config_manager = self.window().app.configManager
        unique, conflicting = config_manager.check_hotkey_unique(modifiers, key, filter_expression, self.current_item)
        if not unique and not self._confirm_hotkey_conflict(conflicting, key, modifiers):
            # Leave the box open with the same preview so the user can
            # either change it or explicitly cancel (Escape/Backspace).
            return

        self.set_dirty()
        self.hotkey_enabled = True
        self.hotkey_label.setText(self.current_item.get_hotkey_string(key, modifiers))
        self.clear_hotkey_button.setEnabled(True)
        self._inline_hotkey_preview = None
        self.hotkey_value_stack.setCurrentWidget(self.hotkey_label)

    def _confirm_hotkey_conflict(self, conflicting, key, modifiers) -> bool:
        """Same message wording as validate()'s conflict check. Returns True
        if the user chooses to assign the hotkey anyway."""
        hotkey_string = self.current_item.get_hotkey_string(key, modifiers)
        f = conflicting.get_applicable_regex()
        if f is None:
            msg = "The hotkey '{hotkey}' is already in use by {conflicting_item}.\n\nAssign it anyway?".format(
                hotkey=hotkey_string, conflicting_item=str(conflicting))
        else:
            msg = "The hotkey '{hotkey}' is already in use by {conflicting_item} " \
                  "for windows matching '{matching_pattern}'.\n\nAssign it anyway?".format(
                hotkey=hotkey_string, conflicting_item=str(conflicting), matching_pattern=f.pattern)
        result = QMessageBox.question(
            self.window(), "Hotkey conflict", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  # TODO: i18n
        return result == QMessageBox.Yes

    def _start_inline_window_filter_detect(self):
        self.window_filter_dialog.detection_finished.connect(self._on_inline_window_filter_detected)
        # There's no dialog visible yet to hint that a click is expected --
        # the crosshair cursor is the only cue until the user clicks a
        # target window and the scope dialog appears.
        QApplication.setOverrideCursor(Qt.CrossCursor)
        self.window_filter_dialog.on_detect_window_properties_button_pressed()

    def _on_inline_window_filter_detected(self, accepted: bool):
        self.window_filter_dialog.detection_finished.disconnect(self._on_inline_window_filter_detected)
        QApplication.restoreOverrideCursor()
        if not accepted:
            return
        self.set_dirty()
        filter_text = self.window_filter_dialog.get_filter_text()
        if filter_text:
            self.window_filter_enabled = True
            self.clear_window_filter_button.setEnabled(True)
            self.window_filter_label.setText(filter_text)
