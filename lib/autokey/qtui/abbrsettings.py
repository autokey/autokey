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

"""
This module contains the abbreviation settings dialog and used components.
This dialog allows the user to set and configure abbreviations to trigger scripts and phrases.

"""

from PyQt4 import QtCore
from PyQt4.QtGui import QListWidgetItem


from .common import inherits_from_ui_file_with_name, EMPTY_FIELD_REGEX


WORD_CHAR_OPTIONS_ORDERED = ["All non-word", "Space and Enter", "Tab"]


class AbbrListItem(QListWidgetItem):
    """
    This is a list item used in the abbreviation QListWidget list.
    It simply holds a string value i.e. the user defined abbreviation string.
    """

    def __init__(self, text):
        QListWidgetItem.__init__(self, text)
        self.setFlags(self.flags() | QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEditable))

    def setData(self, role, value):
        if value == "":
            self.listWidget().itemChanged.emit(self)
        else:
            QListWidgetItem.setData(self, role, value)


class AbbrSettings(*inherits_from_ui_file_with_name("abbrsettings")):

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi()
        for item in WORD_CHAR_OPTIONS_ORDERED:
            self.wordCharCombo.addItem(item)

    def setupUi(self):
        self.setObjectName("Form")
        super().setupUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def on_addButton_pressed(self):
        item = AbbrListItem("")
        self.abbrListWidget.addItem(item)
        self.abbrListWidget.editItem(item)
        self.removeButton.setEnabled(True)

    def on_removeButton_pressed(self):
        item = self.abbrListWidget.takeItem(self.abbrListWidget.currentRow())
        if self.abbrListWidget.count() == 0:
            self.removeButton.setEnabled(False)

    def on_abbrListWidget_itemChanged(self, item):
        if EMPTY_FIELD_REGEX.match(item.text()):
            row = self.abbrListWidget.row(item)
            self.abbrListWidget.takeItem(row)
            del item

        if self.abbrListWidget.count() == 0:
            self.removeButton.setEnabled(False)

    def on_abbrListWidget_itemDoubleClicked(self, item):
        self.abbrListWidget.editItem(item)

    def on_ignoreCaseCheckbox_stateChanged(self, state):
        if not self.ignoreCaseCheckbox.isChecked():
            self.matchCaseCheckbox.setChecked(False)

    def on_matchCaseCheckbox_stateChanged(self, state):
        if self.matchCaseCheckbox.isChecked():
            self.ignoreCaseCheckbox.setChecked(True)

    def on_immediateCheckbox_stateChanged(self, state):
        if self.immediateCheckbox.isChecked():
            self.omitTriggerCheckbox.setChecked(False)
            self.omitTriggerCheckbox.setEnabled(False)
            self.wordCharCombo.setEnabled(False)
        else:
            self.omitTriggerCheckbox.setEnabled(True)
            self.wordCharCombo.setEnabled(True)
