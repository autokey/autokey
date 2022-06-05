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
import subprocess

from PyQt5.QtWidgets import QMessageBox

import autokey.configmanager.configmanager_constants as cm_constants
import autokey.qtui.common as ui_common

from autokey.model.folder import Folder

logger = __import__("autokey.logger").logger.get_logger(__name__)
PROBLEM_MSG_PRIMARY = "Some problems were found"
PROBLEM_MSG_SECONDARY = "{}\n\nYour changes have not been saved."


class FolderPage(*ui_common.inherits_from_ui_file_with_name("folderpage")):

    def __init__(self):
        super(FolderPage, self).__init__()
        self.setupUi(self)
        self.current_folder = None  # type: Folder

    def load(self, folder: Folder):
        self.current_folder = folder
        self.showInTrayCheckbox.setChecked(folder.show_in_tray_menu)
        self.settingsWidget.load(folder)

        if self.is_new_item():
            self.urlLabel.setEnabled(False)
            self.urlLabel.setText("(Unsaved)")  # TODO: i18n
        else:
            ui_common.set_url_label(self.urlLabel, self.current_folder.path)

    def save(self):
        self.current_folder.show_in_tray_menu = self.showInTrayCheckbox.isChecked()
        self.settingsWidget.save()
        self.current_folder.persist()
        ui_common.set_url_label(self.urlLabel, self.current_folder.path)

        return not self.current_folder.path.startswith(cm_constants.CONFIG_DEFAULT_FOLDER)

    def get_current_item(self):
        """Returns the currently held item."""
        return self.current_folder

    def set_item_title(self, title: str):
        self.current_folder.title = title

    def rebuild_item_path(self):
        self.current_folder.rebuild_path()

    def is_new_item(self):
        return self.current_folder.path is None

    def reset(self):
        self.load(self.current_folder)

    def validate(self):
        # Check settings
        errors = self.settingsWidget.validate()

        if errors:
            msg = PROBLEM_MSG_SECONDARY.format('\n'.join([str(e) for e in errors]))
            QMessageBox.critical(self.window(), PROBLEM_MSG_PRIMARY, msg)

        return not bool(errors)

    def set_dirty(self):
        self.window().set_dirty()

    # --- Signal handlers
    def on_showInTrayCheckbox_stateChanged(self, state: bool):
        self.set_dirty()

    @staticmethod
    def on_urlLabel_leftClickedUrl(url: str=None):
        if url:
            subprocess.Popen(["/usr/bin/xdg-open", url])
