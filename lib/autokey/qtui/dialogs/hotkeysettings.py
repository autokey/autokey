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

import typing

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialogButtonBox

import autokey.model.folder
import autokey.model.helpers
import autokey.model.phrase
import autokey.model.script
from autokey.qtui import common as qtui_common
from autokey import UI_common_functions as UI_common

from autokey import iomediator
import autokey.configmanager.configmanager as cm
from autokey.model.key import Key

logger = __import__("autokey.logger").logger.get_logger(__name__)
Item = typing.Union[autokey.model.folder.Folder, autokey.model.script.Script, autokey.model.phrase.Phrase]


class HotkeySettingsDialog(*qtui_common.inherits_from_ui_file_with_name("hotkeysettings")):

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

        self.MODIFIER_BUTTONS = {
            self.mod_control_button: Key.CONTROL,
            self.mod_alt_button: Key.ALT,
            # self.mod_altgr_button: Key.ALT_GR,
            self.mod_shift_button: Key.SHIFT,
            self.mod_super_button: Key.SUPER,
            self.mod_hyper_button: Key.HYPER,
            self.mod_meta_button: Key.META,
        }

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
        self.grabber = iomediator.keygrabber.KeyGrabber(self)
        self.grabber.start()

    def load(self, item: Item):
        UI_common.load_hotkey_settings_dialog(self,
                                              item)

    def populate_hotkey_details(self, item):
        self.activate_modifier_buttons(item.modifiers)

        key = item.hotKey
        key_text = UI_common.get_hotkey_text(self, key)
        self._update_key(key_text)
        logger.debug("Loaded item {}, key: {}, modifiers: {}".format(item, key_text, item.modifiers))

    def activate_modifier_buttons(self, modifiers):
        for button, key in self.MODIFIER_BUTTONS.items():
            button.setChecked(key in modifiers)

    def save(self, item):
        UI_common.save_hotkey_settings_dialog(self, item)

    def reset(self):
        for button in self.MODIFIER_BUTTONS:
            button.setChecked(False)

        self._update_key(None)

    def set_key(self, key, modifiers: typing.List[Key] = None):
        """This is called when the user successfully finishes recording a key combination."""
        if modifiers is None:
            modifiers = []
        if key in self.KEY_MAP:
            key = self.KEY_MAP[key]
        self._update_key(key)
        self.activate_modifier_buttons(modifiers)
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
        for button, key in self.MODIFIER_BUTTONS.items():
            if button.isChecked():
                modifiers.append(key)
        modifiers.sort()
        return modifiers

    def reject(self):
        self.load(self.target_item)
        super().reject()


class GlobalHotkeyDialog(HotkeySettingsDialog):

    def load(self, item: cm.GlobalHotkey):
        self.target_item = item
        UI_common.load_global_hotkey_dialog(self, item)

    def save(self, item: cm.GlobalHotkey):
        UI_common.save_hotkey_settings_dialog(self, item)
