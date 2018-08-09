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
        self.recording_finished.connect(self.setButton.setEnabled)
        self._key = ""
        self.key = None  # Use the property setter to emit the key_assigned signal and disable the Ok button.
        self.target_item = None  # type: Item
        self.grabber = None  # type: iomediator.KeyGrabber

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key
        self.key_assigned.emit(key is not None)

    def on_setButton_pressed(self):
        """
        Start recording a key combination when the user clicks on the setButton.
        The button itself is automatically disabled during the recording process.
        """
        self.keyLabel.setText("Press a key or combination...")  # TODO: i18n
        logger.debug("User starts to record a key combination.")
        self.grabber = iomediator.KeyGrabber(self)
        self.grabber.start()

    def load(self, item: Item):
        self.target_item = item
        if model.TriggerMode.HOTKEY in item.modes:
            self.controlButton.setChecked(Key.CONTROL in item.modifiers)
            self.altButton.setChecked(Key.ALT in item.modifiers)
            self.shiftButton.setChecked(Key.SHIFT in item.modifiers)
            self.superButton.setChecked(Key.SUPER in item.modifiers)
            self.hyperButton.setChecked(Key.HYPER in item.modifiers)
            self.metaButton.setChecked(Key.META in item.modifiers)

            key = item.hotKey
            if key in self.KEY_MAP:
                key_text = self.KEY_MAP[key]
            else:
                key_text = key
            self._setKeyLabel(key_text)
            self.key = key_text
            logger.debug("Loaded item {}, key: {}, modifiers: {}".format(item, key_text, item.modifiers))
        else:
            self.reset()

    def save(self, item):
        item.modes.append(model.TriggerMode.HOTKEY)

        # Build modifier list
        modifiers = self.build_modifiers()

        key_text = self.key
        if key_text in self.REVERSE_KEY_MAP:
            key = self.REVERSE_KEY_MAP[key_text]
        else:
            key = key_text

        if key is None:
            raise RuntimeError("Attempt to set hotkey with no key")
        logger.info("Item {} updated with hotkey {} and modifiers {}".format(item, key, modifiers))
        item.set_hotkey(modifiers, key)

    def reset(self):
        self.controlButton.setChecked(False)
        self.altButton.setChecked(False)
        self.shiftButton.setChecked(False)
        self.superButton.setChecked(False)
        self.hyperButton.setChecked(False)
        self.metaButton.setChecked(False)

        self._setKeyLabel("(None)")  # TODO: i18n
        self.key = None

    def set_key(self, key, modifiers: typing.List[Key]=None):
        """This is called when the user successfully finishes recording a key combination."""
        if modifiers is None:
            modifiers = []  # type: typing.List[Key]
        if key in self.KEY_MAP:
            key = self.KEY_MAP[key]
        self._setKeyLabel(key)
        self.key = key
        self.controlButton.setChecked(Key.CONTROL in modifiers)
        self.altButton.setChecked(Key.ALT in modifiers)
        self.shiftButton.setChecked(Key.SHIFT in modifiers)
        self.superButton.setChecked(Key.SUPER in modifiers)
        self.hyperButton.setChecked(Key.HYPER in modifiers)
        self.metaButton.setChecked(Key.META in modifiers)
        self.recording_finished.emit(True)

    def cancel_grab(self):
        """
        This is called when the user cancels a recording.
        Canceling is done by clicking with the left mouse button.
        """
        logger.debug("User canceled hotkey recording.")
        self.recording_finished.emit(True)
        self._setKeyLabel(self.key if self.key is not None else "(None)")

    def build_modifiers(self):
        modifiers = []
        if self.controlButton.isChecked():
            modifiers.append(Key.CONTROL)
        if self.altButton.isChecked():
            modifiers.append(Key.ALT)
        if self.shiftButton.isChecked():
            modifiers.append(Key.SHIFT)
        if self.superButton.isChecked():
            modifiers.append(Key.SUPER)
        if self.hyperButton.isChecked():
            modifiers.append(Key.HYPER)
        if self.metaButton.isChecked():
            modifiers.append(Key.META)

        modifiers.sort()
        return modifiers

    def reject(self):
        self.load(self.target_item)
        super().reject()

    def _setKeyLabel(self, key):
        self.keyLabel.setText("Key: " + key)  # TODO: i18n


class GlobalHotkeyDialog(HotkeySettingsDialog):

    def load(self, item: cm.GlobalHotkey):
        self.target_item = item
        if item.enabled:
            self.controlButton.setChecked(Key.CONTROL in item.modifiers)
            self.altButton.setChecked(Key.ALT in item.modifiers)
            self.shiftButton.setChecked(Key.SHIFT in item.modifiers)
            self.superButton.setChecked(Key.SUPER in item.modifiers)
            self.hyperButton.setChecked(Key.HYPER in item.modifiers)
            self.metaButton.setChecked(Key.META in item.modifiers)

            key = item.hotKey
            if key in self.KEY_MAP:
                key_text = self.KEY_MAP[key]
            else:
                key_text = key
            self._setKeyLabel(key_text)
            self.key = key_text

        else:
            self.reset()

    def save(self, item: cm.GlobalHotkey):
        # Build modifier list
        modifiers = self.build_modifiers()

        key_text = self.key
        if key_text in self.REVERSE_KEY_MAP:
            key = self.REVERSE_KEY_MAP[key_text]
        else:
            key = key_text

        if key is None:
            raise RuntimeError("Attempt to set hotkey with no key")
        item.set_hotkey(modifiers, key)
