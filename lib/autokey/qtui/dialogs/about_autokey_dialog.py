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

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QSize

import autokey.common
from autokey.qtui import common as ui_common


class AboutAutokeyDialog(*ui_common.inherits_from_ui_file_with_name("about_autokey_dialog")):

    def __init__(self, parent: QWidget = None):
        super(AboutAutokeyDialog, self).__init__(parent)
        self.setupUi(self)
        icon = ui_common.load_icon(ui_common.AutoKeyIcon.AUTOKEY)
        pixmap = icon.pixmap(icon.actualSize(QSize(1024, 1024)))
        self.autokey_icon.setPixmap(pixmap)
        self.autokey_version_label.setText(autokey.common.VERSION)
        self.python_version_label.setText(sys.version.replace("\n", " "))
