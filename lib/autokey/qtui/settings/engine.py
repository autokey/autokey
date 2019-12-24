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

import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QWidget, QApplication

from autokey.qtui import common
logger = __import__("autokey.logger").logger.get_logger(__name__)


class EngineSettings(*common.inherits_from_ui_file_with_name("enginesettings")):
    """
    The EngineSettings class is used inside the AutoKey configuration dialog. It allows the user to select and add a
    custom Python module search path entry.
    """
    def __init__(self, parent: QWidget=None):
        super(EngineSettings, self).__init__(parent)
        self.setupUi(self)

        # Save the path label text stored in the Qt UI file.
        # It is used to reset the label to this value if a custom module path is currently set and the user deletes it.
        # Do not hard-code it to prevent possible inconsistencies.
        self.initial_folder_label_text = self.folder_label.text()

        self.config_manager = QApplication.instance().configManager
        self.path = self.config_manager.userCodeDir
        self.clear_button.setEnabled(self.path is not None)

        if self.config_manager.userCodeDir is not None:
            self.folder_label.setText(self.config_manager.userCodeDir)
        logger.debug("EngineSettings widget initialised, custom module search path is set to: {}".format(self.path))

    def save(self):
        """This function is called by the parent dialog window when the user selects to save the settings."""
        if self.path is None:  # Delete requested, so remove the current path from sys.path, if present
            if self.config_manager.userCodeDir is not None:
                sys.path.remove(self.config_manager.userCodeDir)
                self.config_manager.userCodeDir = None
                logger.info("Removed custom module search path from configuration and sys.path.")

        else:
            if self.path != self.config_manager.userCodeDir:
                if self.config_manager.userCodeDir is not None:
                    sys.path.remove(self.config_manager.userCodeDir)
                sys.path.append(self.path)
                self.config_manager.userCodeDir = self.path
                logger.info("Saved custom module search path and added it to sys.path: {}".format(self.path))

    @pyqtSlot()
    def on_browse_button_pressed(self):
        """
        PyQt slot called when the user hits the "Browse" button.
        Display a directory selection dialog and store the returned path.
        """
        path = QFileDialog.getExistingDirectory(self.parentWidget(), "Choose a directory containing Python modules")

        if path:  # Non-empty means the user chose a path and clicked on OK
            self.path = path
            self.clear_button.setEnabled(True)
            self.folder_label.setText(path)
            logger.debug("User selects a custom module search path: {}".format(self.path))

    @pyqtSlot()
    def on_clear_button_pressed(self):
        """
        PyQt slot called when the user hits the "Clear" button.
        Removes any set custom module search path.
        """
        self.path = None
        self.clear_button.setEnabled(False)
        self.folder_label.setText(self.initial_folder_label_text)
        logger.debug("User selects to clear the custom module search path.")
