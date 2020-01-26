# Copyright (C) 2020 Thomas Hess <thomas.hess@udo.edu>

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

import typing

from PyQt5.QtWidgets import QApplication, QAbstractButton, QDialogButtonBox
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from autokey.model import ScriptErrorRecord

from autokey.qtui import common as ui_common


logger = __import__("autokey.logger").logger.get_logger(__name__)


class ShowRecentScriptErrorsDialog(*ui_common.inherits_from_ui_file_with_name("show_recent_script_errors_dialog")):
    """
    This dialogue is used to show errors that caused user Scripts to abort. The ScriptRunner class holds a list
    with errors, which can be viewed and cleared using this dialogue window.
    """

    # When switching errors, emit a boolean indicating if further errors are available. The Next button reacts on
    # this and enables/disables itself based on the boolean value. The connection is defined in the .ui file.
    has_previous_error = pyqtSignal(bool, name="has_previous_error")
    # When switching errors, emit a boolean indicating if previous errors are available. The Previous button reacts on
    # this and enables/disables itself based on the boolean value. The connection is defined in the .ui file.
    has_next_error = pyqtSignal(bool, name="has_next_error")

    script_errors_available = pyqtSignal(bool, name="script_errors_available")

    def __init__(self, parent):
        super(ShowRecentScriptErrorsDialog, self).__init__(parent)
        self.setupUi(self)
        # This can’t be done in the UI editor, which can only set specific fonts. Just use the system default monospace
        # font.
        self.stack_trace_text_browser.setFontFamily("monospace")
        self.buttonBox.clicked.connect(self.handle_button_box_buttons)

        self.recent_script_errors = QApplication.instance().\
            service.scriptRunner.error_records  # type: typing.List[ScriptErrorRecord]
        self.currently_viewed_error_index = 0

    def hide(self):
        self.script_errors_available.emit(bool(self.recent_script_errors))
        super(ShowRecentScriptErrorsDialog, self).hide()

    @pyqtSlot(QAbstractButton)
    def handle_button_box_buttons(self, clicked_button: QAbstractButton):
        """
        Used to connect the button presses with logic for 'Reset error list' and 'Discard current error' buttons in
        the button box at the bottom of the dialogue window.
        """
        button_role = self.buttonBox.buttonRole(clicked_button)
        # The Close is handled internally and simply hides the dialogue, therefore nothing is implemented here.
        if button_role == QDialogButtonBox.DestructiveRole:  # Discard current error
            self.remove_currently_shown_error_from_error_list()
        elif button_role == QDialogButtonBox.ResetRole:  # Clear the error list
            self.clear_error_list()

    @pyqtSlot()
    def update_and_show(self):
        error_count = len(self.recent_script_errors)
        if error_count:
            if self.currently_viewed_error_index >= error_count:
                self.currently_viewed_error_index = error_count-1

            self.has_next_error.emit(self.currently_viewed_error_index < error_count-1)
            self.has_previous_error.emit(self.currently_viewed_error_index > 0)

            logger.info("User views the last script errors. There are {} errors to review.".format(error_count))
            self._show_error(self.currently_viewed_error_index)

            self.show()
        else:
            logger.error(
                "User is able to view the script error dialogue, even if no errors are available. "
                "This should be impossible. Do not show the dialogue window.")

    @pyqtSlot()
    def show_next_error(self):
        """
        Switch to the next error in the error list.
        The connection from the Next button to this slot function is defined in the .ui file.
        """
        logger.debug("User views the next error.")
        # Out of bounds handling is not needed, as the Next button gets disables when the last error is reached.
        # See has_next_error Signal.
        self.currently_viewed_error_index += 1
        self.has_next_error.emit(self.currently_viewed_error_index < len(self.recent_script_errors)-1)
        self._show_error(self.currently_viewed_error_index)

    @pyqtSlot()
    def show_previous_error(self):
        """
        Switch to the previous error in the error list.
        The connection from the Previous button to this slot function is defined in the .ui file.
        """
        logger.debug("User views the previous error.")
        # Out of bounds handling is not needed, as the Previous button gets disables when the first error is reached.
        # See has_previous_error Signal.
        self.currently_viewed_error_index -= 1
        self.has_previous_error.emit(self.currently_viewed_error_index > 0)
        self._show_error(self.currently_viewed_error_index)

    def remove_currently_shown_error_from_error_list(self):
        """
        Delete the currently shown error from the error list.
        Shows the next error, if available. Otherwise, show the previous error, if available.
        Or clear the list and hide the window, if the deleted error was the only one in the list.
        """
        error_count = len(self.recent_script_errors)
        if error_count == 1:
            self.clear_error_list()
        else:
            del self.recent_script_errors[self.currently_viewed_error_index]
            if self.currently_viewed_error_index == error_count-1:
                self.show_previous_error()
            else:
                self.has_next_error.emit(self.currently_viewed_error_index < len(self.recent_script_errors)-1)
                self._show_error(self.currently_viewed_error_index)

    def clear_error_list(self):
        """Clears all errors in the error list and hides the dialogue window."""
        self.currently_viewed_error_index = 0
        QApplication.instance().service.scriptRunner.clear_error_records()
        self.hide()

    def _show_error(self, script_at_index: int):
        """Update the GUI to show the error at the given list index."""
        script_error = self.recent_script_errors[self.currently_viewed_error_index]
        self.currently_shown_error_number_label.setText(str(script_at_index+1))
        # Update the count on each show. This updates the GUI, if new errors occur while the
        # dialogue window is shown and the user clicks on a previous or next button.
        self.total_error_count_label.setText(str(len(self.recent_script_errors)))
        self.script_start_time_edit.setTime(script_error.start_time)
        self.script_error_time_edit.setTime(script_error.error_time)
        self.script_name_view.setText(script_error.script_name)
        self.stack_trace_text_browser.setText(script_error.error_traceback)

