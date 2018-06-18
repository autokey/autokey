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

from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtGui import QFontMetrics

from ..common import inherits_from_ui_file_with_name
from .detectdialog import DetectDialog

from ... import iomediator
from ... import model


# TODO: Once the port to Qt5 is done, enable the clearButtonEnable property for the line edit in the UI editor.
# TODO: Pure Qt4 does not support the line edit clear button, so this functionality is currently unavailable.
class WindowFilterSettingsDialog(*inherits_from_ui_file_with_name("window_filter_settings_dialog")):

    def __init__(self, parent):
        super(WindowFilterSettingsDialog, self).__init__(parent)
        self.setupUi(self)
        m = QFontMetrics(QApplication.font())
        self.triggerRegexLineEdit.setMinimumWidth(m.width("windowclass.WindowClass"))
        self.target_item = None
        self.grabber = None  # type: iomediator.WindowGrabber

    def load(self, item):
        self.target_item = item

        if not isinstance(item, model.Folder):
            self.recursiveCheckBox.hide()
        else:
            self.recursiveCheckBox.show()

        if not item.has_filter():
            self.reset()
        else:
            self.triggerRegexLineEdit.setText(item.get_filter_regex())
            self.recursiveCheckBox.setChecked(item.isRecursive)

    def save(self, item):
        item.set_window_titles(self.get_filter_text())
        item.set_filter_recursive(self.get_is_recursive())

    def get_is_recursive(self):
        return self.recursiveCheckBox.isChecked()

    def reset(self):
        self.triggerRegexLineEdit.clear()
        self.recursiveCheckBox.setChecked(False)

    def reset_focus(self):
        self.triggerRegexLineEdit.setFocus()

    def get_filter_text(self):
        return str(self.triggerRegexLineEdit.text())

    def receive_window_info(self, info):
        self.parentWidget().window().app.exec_in_main(self._receiveWindowInfo, info)

    def _receiveWindowInfo(self, info):
        dlg = DetectDialog(self)
        dlg.populate(info)
        dlg.exec_()

        if dlg.result() == QDialog.Accepted:
            self.triggerRegexLineEdit.setText(dlg.get_choice())

        self.detectButton.setEnabled(True)

    # --- Signal handlers ---

    def on_detectButton_pressed(self):
        self.detectButton.setEnabled(False)
        self.grabber = iomediator.WindowGrabber(self)
        self.grabber.start()

    # --- event handlers ---

    def slotButtonClicked(self, button):
        if button == QDialog.Cancel:
            self.load(self.targetItem)

        QDialog.slotButtonClicked(self, button)

