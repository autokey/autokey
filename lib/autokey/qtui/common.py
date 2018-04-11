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

import re

from PyQt4.QtCore import QFile
from PyQt4.QtGui import QMessageBox
from PyQt4 import uic

EMPTY_FIELD_REGEX = re.compile(r"^ *$", re.UNICODE)

def validate(expression, message, widget, parent):
    if not expression:
        QMessageBox.critical(parent, message, message)
        if widget is not None:
            widget.setFocus()
    return expression

def _get_ui_qfile(name: str):
    """
    Returns an opened, read-only QFile for the given QtDesigner UI file name. Expects a plain name like "centralwidget".
    The file ending and resource path is added automatically.
    Raises FileNotFoundError, if the given ui file does not exist.
    :param name:
    :return:
    """
    # TODO: configure and use a resource file (resources.qrc) specifying all UI files and enable the next line, remove the workaround
    # file_path = ":/ui/{ui_file_name}.ui".format(ui_file_name=name)
    # WORKAROUND
    import pathlib
    file_path = "{abspath}/resources/ui/{ui_file_name}.ui".format(abspath=pathlib.Path(__file__).resolve().parent, ui_file_name=name)
    # WORKAROUND END
    file = QFile(file_path)
    if not file.exists():
        raise FileNotFoundError("UI file not found: " + file_path)
    file.open(QFile.ReadOnly)
    return file


def load_ui_from_file(name: str):
    """
    Returns a tuple from uic.loadUiType(), loading the ui file with the given name.
    :param name:
    :return:
    """
    ui_file = _get_ui_qfile(name)
    base_type = uic.loadUiType(ui_file)
    ui_file.close()
    return base_type


"""
This renamed function is supposed to be used during class definition to make the intention clear.
Usage example:

class SomeWidget(*inherits_from_ui_file_with_name("SomeWidgetUiFileName")):
    def __init__(self, parent):
        super(SomeWidget, self).__init__(parent)
        self.setupUi(self)


"""
inherits_from_ui_file_with_name = load_ui_from_file
