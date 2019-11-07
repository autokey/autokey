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
import typing

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialogButtonBox

from autokey.qtui import common as ui_common

from autokey import iomediator, model, configmanager as cm
from autokey.iomediator.key import Key

logger = ui_common.logger.getChild("Hotkey Settings Dialog")  # type: logging.Logger
Item = typing.Union[model.Folder, model.Script, model.Phrase]


class HotkeySettingsDialog(*ui_common.inherits_from_ui_file_with_name("hotkeysettings")):

    KEY_MAP = {
        ' ': "<space>",
    }

    REVERSE_KEY_MAP = {value: key for key, value in KEY_MAP.items()}
    DEFAULT_RECORDED_KEY_LABEL_CONTENT = "(None)"

    """
    This signal is emitted whenever the key is assigned/deleted. This happens when the user records a key or cancels
    a key recording.
    """
    key_assigned = pyqtSignal(bool, name="key_assigned")
    recording_finished = pyqtSignal(bool, name="recording_finished")

    def __init__(self, parent):
        super(HotkeySettingsDialog, self).__init__(parent)
        self.setupUi(self)
        # Enable the Ok button iff a correct key combination is assigned. This guides the user and obsoletes an error
        # message that was shown when the user did something invalid.
        self.key_assigned.connect(self.buttonBox.button(QDialogButtonBox.Ok).setEnabled)
        self.recording_finished.connect(self.record_combination_button.setEnabled)
        self.key = ""
        self._update_key(None)  # Use _update_key to emit the key_assigned signal and disable the Ok button.
        self.target_item = None  # type: Item
        self.grabber = None  # type: iomediator.KeyGrabber

    def _update_key(self, key):
        self.key = key
        if key is None:
            self.recorded_key_label.setText("Key: {}".format(self.DEFAULT_RECORDED_KEY_LABEL_CONTENT))  # TODO: i18n
            self.key_assigned.emit(False)
        else:
            self.recorded_key_label.setText("Key: {}".format(key))  # TODO: i18n
            self.key_assigned.emit(True)

    def on_record_combination_button_pressed(self):
        """
        Start recording a key combination when the user clicks on the record_combination_button.
        The button itself is automatically disabled during the recording process.
        """
        self.recorded_key_label.setText("Press a key or combination...")  # TODO: i18n
        logger.debug("User starts to record a key combination.")
        self.grabber = iomediator.KeyGrabber(self)
        self.grabber.start()

    def load(self, item: Item):
        self.target_item = item
        if model.TriggerMode.HOTKEY in item.modes:
            self.mod_control_button.setChecked(Key.CONTROL in item.modifiers)
            self.mod_alt_button.setChecked(Key.ALT in item.modifiers)
            self.mod_shift_button.setChecked(Key.SHIFT in item.modifiers)
            self.mod_super_button.setChecked(Key.SUPER in item.modifiers)
            self.mod_hyper_button.setChecked(Key.HYPER in item.modifiers)
            self.mod_meta_button.setChecked(Key.META in item.modifiers)

            key = item.hotKey
            if key in self.KEY_MAP:
                key_text = self.KEY_MAP[key]
            else:
                key_text = key
            self._update_key(key_text)
            logger.debug("Loaded item {}, key: {}, modifiers: {}".format(item, key_text, item.modifiers))
        else:
            self.reset()

    def save(self, item):
        item.modes.append(model.TriggerMode.HOTKEY)

        # Build modifier list
        modifiers = self.build_modifiers()

        if self.key in self.REVERSE_KEY_MAP:
            key = self.REVERSE_KEY_MAP[self.key]
        else:
            key = self.key

        if key is None:
            raise RuntimeError("Attempt to set hotkey with no key")
        logger.info("Item {} updated with hotkey {} and modifiers {}".format(item, key, modifiers))
        item.set_hotkey(modifiers, key)

    def reset(self):
        self.mod_control_button.setChecked(False)
        self.mod_alt_button.setChecked(False)
        self.mod_shift_button.setChecked(False)
        self.mod_super_button.setChecked(False)
        self.mod_hyper_button.setChecked(False)
        self.mod_meta_button.setChecked(False)

        self._update_key(None)

    def set_key(self, key, modifiers: typing.List[Key] = None):
        """This is called when the user successfully finishes recording a key combination."""
        if modifiers is None:
            modifiers = []  # type: typing.List[Key]
        if key in self.KEY_MAP:
            key = self.KEY_MAP[key]
        self._update_key(key)
        self.mod_control_button.setChecked(Key.CONTROL in modifiers)
        self.mod_alt_button.setChecked(Key.ALT in modifiers)
        self.mod_shift_button.setChecked(Key.SHIFT in modifiers)
        self.mod_super_button.setChecked(Key.SUPER in modifiers)
        self.mod_hyper_button.setChecked(Key.HYPER in modifiers)
        self.mod_meta_button.setChecked(Key.META in modifiers)
        self.recording_finished.emit(True)

    def cancel_grab(self):
        """
        This is called when the user cancels a recording.
        Canceling is done by clicking with the left mouse button.
        """
        logger.debug("User canceled hotkey recording.")
        self.recording_finished.emit(True)

    def build_modifiers(self):
        modifiers = []
        if self.mod_control_button.isChecked():
            modifiers.append(Key.CONTROL)
        if self.mod_alt_button.isChecked():
            modifiers.append(Key.ALT)
        if self.mod_shift_button.isChecked():
            modifiers.append(Key.SHIFT)
        if self.mod_super_button.isChecked():
            modifiers.append(Key.SUPER)
        if self.mod_hyper_button.isChecked():
            modifiers.append(Key.HYPER)
        if self.mod_meta_button.isChecked():
            modifiers.append(Key.META)

        modifiers.sort()
        return modifiers

    def reject(self):
        self.load(self.target_item)
        super().reject()


class GlobalHotkeyDialog(HotkeySettingsDialog):

    def load(self, item: cm.GlobalHotkey):
        self.target_item = item
        if item.enabled:
            self.mod_control_button.setChecked(Key.CONTROL in item.modifiers)
            self.mod_alt_button.setChecked(Key.ALT in item.modifiers)
            self.mod_shift_button.setChecked(Key.SHIFT in item.modifiers)
            self.mod_super_button.setChecked(Key.SUPER in item.modifiers)
            self.mod_hyper_button.setChecked(Key.HYPER in item.modifiers)
            self.mod_meta_button.setChecked(Key.META in item.modifiers)

            key = item.hotKey
            if key in self.KEY_MAP:
                key_text = self.KEY_MAP[key]
            else:
                key_text = key
            self._update_key(key_text)

        else:
            self.reset()

    def save(self, item: cm.GlobalHotkey):
        # Build modifier list
        modifiers = self.build_modifiers()

        if self.key in self.REVERSE_KEY_MAP:
            key = self.REVERSE_KEY_MAP[self.key]
        else:
            key = self.key

        if key is None:
            raise RuntimeError("Attempt to set hotkey with no key")
        item.set_hotkey(modifiers, key)
