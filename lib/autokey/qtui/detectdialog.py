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

from PyQt4 import uic

from .common import get_ui_qfile

ui_file = get_ui_qfile("detectdialog")
DetectDialogBase = uic.loadUiType(ui_file)
ui_file.close()


class DetectSettings(*DetectDialogBase):

    def __init__(self, parent):
        super(DetectSettings, self).__init__()
        self.setupUi(self)
