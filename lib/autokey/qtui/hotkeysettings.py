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

from .. import iomediator


class HotkeySettings(*inherits_from_ui_file_with_name("hotkeysettings")):

    def __init__(self, parent):
        super(HotkeySettings, self).__init__(parent)
        self.setupUi(self)

    # ---- Signal handlers

    def on_setButton_pressed(self):
        self.setButton.setEnabled(False)
        self.keyLabel.setText("Press a key or combination...")  # TODO: i18n
        self.grabber = iomediator.KeyGrabber(self.parentWidget())
        self.grabber.start()
