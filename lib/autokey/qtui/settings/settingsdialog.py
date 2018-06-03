# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>
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
import logging

from PyQt5.QtCore import pyqtSlot

from autokey.configmanager import ConfigManager

from autokey.qtui import common

logger = common.logger.getChild("Settings Dialog")  # type: logging.Logger


class SettingsDialog(*common.inherits_from_ui_file_with_name("settingsdialog")):
    
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)
        self.app = parent.window().app  # autokey.qtapp.Application
        config_manager = self.app.configManager  # type: ConfigManager
        self.special_hotkeys_page.init(config_manager)
        self.script_engine_page.init(config_manager)
        logger.info("Settings dialog window created.")

    @pyqtSlot()  # Avoid the slot being called twice, by both signals clicked() and clicked(bool).
    def on_show_general_settings_button_clicked(self):
        logger.debug("User views general settings")
        self.settings_pages.setCurrentWidget(self.general_settings_page)

    @pyqtSlot()  # Avoid the slot being called twice, by both signals clicked() and clicked(bool).
    def on_show_special_hotkeys_button_clicked(self):
        logger.debug("User views special hotkeys settings")
        self.settings_pages.setCurrentWidget(self.special_hotkeys_page)

    @pyqtSlot()  # Avoid the slot being called twice, by both signals clicked() and clicked(bool).
    def on_show_script_engine_button_clicked(self):
        logger.debug("User views script engine settings")
        self.settings_pages.setCurrentWidget(self.script_engine_page)

    def accept(self):
        logger.info("User requested to save the settings.")
        self.general_settings_page.save()
        self.special_hotkeys_page.save()
        self.script_engine_page.save()
        self.app.configManager.config_altered(True)
        self.app.update_notifier_visibility()
        super(SettingsDialog, self).accept()
        logger.debug("Save completed, dialog window hidden.")
