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

from .common import inherits_from_ui_file_with_name


class DetectDialog(*inherits_from_ui_file_with_name("detectdialog")):
    """
    The DetectDialog lets the user detect window properties of a chosen window.
    The dialog shows the window title and window class of the chosen window
    and lets the user select one of those two options.
    """

    def __init__(self, parent):
        super(DetectDialog, self).__init__(parent)
        self.setupUi(self)
        self.window_info = None

    def populate(self, window_info):

        self.detected_title.setText(window_info[0])
        self.detected_class.setText(window_info[1])
        self.window_info = window_info

    def get_choice(self):
        # This relies on autoExclusive being set to true in the ui file.
        if self.classButton.isChecked():
            return self.window_info[1]
        else:
            return self.window_info[0]
