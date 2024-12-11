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
from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget

from autokey.qtui import common

if TYPE_CHECKING:
    from autokey.qtapp import Application


logger = __import__("autokey.logger").logger.get_logger(__name__)


class SettingsDialog(*common.inherits_from_ui_file_with_name("settingsdialog")):
    
    def __init__(self, parent: QWidget=None):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)
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
        app = QApplication.instance()  # type: Application
        self.general_settings_page.save()
        self.special_hotkeys_page.save()
        self.script_engine_page.save()
        app.configManager.config_altered(True)
        app.update_notifier_visibility()
        app.notifier.reset_tray_icon()
        super(SettingsDialog, self).accept()
        logger.debug("Save completed, dialog window hidden.")
