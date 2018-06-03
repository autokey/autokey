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

from .common import inherits_from_ui_file_with_name, set_url_label

from .. import configmanager as cm

PROBLEM_MSG_PRIMARY = "Some problems were found"
PROBLEM_MSG_SECONDARY = "{}\n\nYour changes have not been saved."


class FolderPage(*inherits_from_ui_file_with_name("folderpage")):

    def __init__(self):
        super(FolderPage, self).__init__()
        self.setupUi(self)

    def load(self, folder):
        self.currentFolder = folder
        self.showInTrayCheckbox.setChecked(folder.showInTrayMenu)
        self.settingsWidget.load(folder)

        if self.is_new_item():
            self.urlLabel.setEnabled(False)
            self.urlLabel.setText("(Unsaved)")  # TODO: i18n
        else:
            set_url_label(self.urlLabel, self.currentFolder.path)

    def save(self):
        self.currentFolder.showInTrayMenu = self.showInTrayCheckbox.isChecked()
        self.settingsWidget.save()
        self.currentFolder.persist()
        set_url_label(self.urlLabel, self.currentFolder.path)

        return not self.currentFolder.path.startswith(cm.CONFIG_DEFAULT_FOLDER)

    def set_item_title(self, title):
        self.currentFolder.title = title

    def rebuild_item_path(self):
        self.currentFolder.rebuild_path()

    def is_new_item(self):
        return self.currentFolder.path is None

    def reset(self):
        self.load(self.currentFolder)

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
    def on_showInTrayCheckbox_stateChanged(self, state):
        self.set_dirty()

    def on_urlLabel_leftClickedUrl(self, url=None):
        if url: subprocess.Popen(["/usr/bin/xdg-open", url])
