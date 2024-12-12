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

from autokey.qtui import common as ui_common


logger = __import__("autokey.logger").logger.get_logger(__name__)

class RecordDialog(*ui_common.inherits_from_ui_file_with_name("record_dialog")):

    def __init__(self, parent, closure):
        super().__init__(parent)
        self.setupUi(self)
        self.closure = closure

    def get_record_keyboard(self):
        return self.record_keyboard_button.isChecked()

    def get_record_mouse(self):
        return self.record_mouse_button.isChecked()

    def get_delay(self):
        return self.delay_recording_start_seconds_spin_box.value()

    def accept(self):
        super().accept()
        logger.info("Dialog accepted: Record keyboard: {}, record mouse: {}, delay: {} s".format(
            self.get_record_keyboard(), self.get_record_mouse(), self.get_delay()
        ))
        self.closure(True, self.get_record_keyboard(), self.get_record_mouse(), self.get_delay())

    def reject(self):
        super().reject()
        logger.info("Dialog closed (rejected/aborted): Record keyboard: {}, record mouse: {}, delay: {} s".format(
            self.get_record_keyboard(), self.get_record_mouse(), self.get_delay()
        ))
        self.closure(False, self.get_record_keyboard(), self.get_record_mouse(), self.get_delay())
