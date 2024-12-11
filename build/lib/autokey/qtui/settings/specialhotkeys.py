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

from PyQt5.QtWidgets import QDialog, QWidget, QApplication, QLabel, QPushButton

from autokey.qtui.dialogs import GlobalHotkeyDialog
import autokey.qtui.common as ui_common
if typing.TYPE_CHECKING:
    from autokey.qtapp import Application


logger = __import__("autokey.logger").logger.get_logger(__name__)


class SpecialHotkeySettings(*ui_common.inherits_from_ui_file_with_name("specialhotkeysettings")):
    """
    The SpecialHotkeySettings class is used inside the AutoKey configuration dialog.
    It allows the user to select or clear global hotkeys.
    Currently has two hotkeys:
    - use_service enables/disables the autokey background service
    - use_config shows the autokey config/main window, if hidden.
    """
    KEY_MAP = GlobalHotkeyDialog.KEY_MAP
    REVERSE_KEY_MAP = GlobalHotkeyDialog.REVERSE_KEY_MAP

    def __init__(self, parent: QWidget=None):
        super(SpecialHotkeySettings, self).__init__(parent)
        self.setupUi(self)


        self.show_config_dlg = GlobalHotkeyDialog(parent)
        self.toggle_monitor_dlg = GlobalHotkeyDialog(parent)
        self.use_config_hotkey = False
        self.use_service_hotkey = False
        app = QApplication.instance()  # type: Application
        self.config_manager = app.configManager
        self.use_config_hotkey = self._load_hotkey(self.config_manager.configHotkey, self.config_key_label,
                                                   self.show_config_dlg, self.clear_config_button)
        self.use_service_hotkey = self._load_hotkey(self.config_manager.toggleServiceHotkey, self.monitor_key_label,
                                                    self.toggle_monitor_dlg, self.clear_monitor_button)

    @staticmethod
    def _load_hotkey(item, label: QLabel, dialog: GlobalHotkeyDialog, clear_button: QPushButton):
        dialog.load(item)
        if item.enabled:
            key = item.hotKey
            label.setText(item.get_hotkey_string(key, item.modifiers))
            clear_button.setEnabled(True)
            return True
        else:
            label.setText("(None configured)")
            clear_button.setEnabled(False)
            return False

    def save(self):
        config_hotkey = self.config_manager.configHotkey
        toggle_hotkey = self.config_manager.toggleServiceHotkey
        app = QApplication.instance()  # type: Application
        if config_hotkey.enabled:
            app.hotkey_removed(config_hotkey)
        config_hotkey.enabled = self.use_config_hotkey
        if self.use_config_hotkey:
            self.show_config_dlg.save(config_hotkey)
            app.hotkey_created(config_hotkey)

        if toggle_hotkey.enabled:
            app.hotkey_removed(toggle_hotkey)
        toggle_hotkey.enabled = self.use_service_hotkey
        if self.use_service_hotkey:
            self.toggle_monitor_dlg.save(toggle_hotkey)
            app.hotkey_created(toggle_hotkey)

    # ---- Signal handlers

    def on_set_config_button_pressed(self):
        self.show_config_dlg.exec_()

        if self.show_config_dlg.result() == QDialog.Accepted:
            self.use_config_hotkey = True
            key = self.show_config_dlg.key
            modifiers = self.show_config_dlg.build_modifiers()
            self.config_key_label.setText(self.show_config_dlg.target_item.get_hotkey_string(key, modifiers))
            self.clear_config_button.setEnabled(True)

    def on_clear_config_button_pressed(self):
        self.use_config_hotkey = False
        self.clear_config_button.setEnabled(False)
        self.config_key_label.setText("(None configured)")
        self.show_config_dlg.reset()

    def on_set_monitor_button_pressed(self):
        self.toggle_monitor_dlg.exec_()

        if self.toggle_monitor_dlg.result() == QDialog.Accepted:
            self.use_service_hotkey = True
            key = self.toggle_monitor_dlg.key
            modifiers = self.toggle_monitor_dlg.build_modifiers()
            self.monitor_key_label.setText(self.toggle_monitor_dlg.target_item.get_hotkey_string(key, modifiers))
            self.clear_monitor_button.setEnabled(True)

    def on_clear_monitor_button_pressed(self):
        self.use_service_hotkey = False
        self.clear_monitor_button.setEnabled(False)
        self.monitor_key_label.setText("(None configured)")
        self.toggle_monitor_dlg.reset()
