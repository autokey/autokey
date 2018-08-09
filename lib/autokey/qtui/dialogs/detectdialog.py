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
from typing import Tuple

from PyQt5.QtWidgets import QWidget

from autokey.qtui import common as ui_common

logger = ui_common.logger.getChild("DetectDialog")


class DetectDialog(*ui_common.inherits_from_ui_file_with_name("detectdialog")):
    """
    The DetectDialog lets the user select window properties of a chosen window.
    The dialog shows the window title and window class of the chosen window
    and lets the user select one of those two options.
    """

    def __init__(self, parent: QWidget):
        super(DetectDialog, self).__init__(parent)
        self.setupUi(self)
        self.window_title = ""
        self.window_class = ""

    def populate(self, window_info: Tuple[str, str]):
        self.window_title, self.window_class = window_info
        self.detected_title.setText(self.window_title)
        self.detected_class.setText(self.window_class)
        logger.info(
            "Detected window with properties title: {}, window class: {}".format(self.window_title, self.window_class)
        )

    def get_choice(self) -> str:
        # This relies on autoExclusive being set to true in the ui file.
        if self.classButton.isChecked():
            logger.debug("User has chosen the window class: {}".format(self.window_class))
            return self.window_class
        else:
            logger.debug("User has chosen the window title: {}".format(self.window_title))
            return self.window_title
