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

import re

from PyQt5.QtWidgets import QDialog

import autokey.iomediator.windowgrabber
import autokey.model.folder
import autokey.model.modelTypes
from autokey.qtui import common as qtui_common
from autokey import UI_common_functions as UI_common
from .detectdialog import DetectDialog

from autokey import iomediator

logger = __import__("autokey.logger").logger.get_logger(__name__)


class WindowFilterSettingsDialog(*qtui_common.inherits_from_ui_file_with_name("window_filter_settings_dialog")):

    def __init__(self, parent):
        super(WindowFilterSettingsDialog, self).__init__(parent)
        self.setupUi(self)
        self.target_item = None
        self.grabber = None  # type: autokey.iomediator._windowgrabber.WindowGrabber

    def load(self, item: autokey.model.modelTypes.Item):
        self.target_item = item

        if not isinstance(item, autokey.model.folder.Folder):
            self.apply_recursive_check_box.hide()
        else:
            self.apply_recursive_check_box.show()

        if not item.has_filter():
            self.reset()
        else:
            self.trigger_regex_line_edit.setText(item.get_filter_regex())
            self.apply_recursive_check_box.setChecked(item.isRecursive)

    def save(self, item):
        UI_common.save_item_filter(self, item)

    def get_is_recursive(self):
        return self.apply_recursive_check_box.isChecked()

    def reset(self):
        self.trigger_regex_line_edit.clear()
        self.apply_recursive_check_box.setChecked(False)

    def reset_focus(self):
        self.trigger_regex_line_edit.setFocus()

    def get_filter_text(self):
        return str(self.trigger_regex_line_edit.text())

    def receive_window_info(self, info):
        self.parentWidget().window().app.exec_in_main(self._receiveWindowInfo, info)

    def _receiveWindowInfo(self, info):
        dlg = DetectDialog(self)
        dlg.populate(info)
        dlg.exec_()

        if dlg.result() == QDialog.Accepted:
            self.trigger_regex_line_edit.setText(dlg.get_choice())

        self.detect_window_properties_button.setEnabled(True)

    # --- Signal handlers ---

    def on_detect_window_properties_button_pressed(self):
        self.detect_window_properties_button.setEnabled(False)
        self.grabber = iomediator.windowgrabber.WindowGrabber(self)
        self.grabber.start()

    # --- event handlers ---

    def slotButtonClicked(self, button):
        if button == QDialog.Cancel:
            self.load(self.targetItem)

        QDialog.slotButtonClicked(self, button)

