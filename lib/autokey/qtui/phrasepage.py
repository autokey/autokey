# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018, 2019 Thomas Hess <thomas.hess@udo.edu>

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

import subprocess

from PyQt5.QtWidgets import QMessageBox

import autokey.model.phrase
from autokey.qtui import common as ui_common


PROBLEM_MSG_PRIMARY = "Some problems were found"
PROBLEM_MSG_SECONDARY = "{}\n\nYour changes have not been saved."


# TODO: Once the port to Qt5 is done, set the editor placeholder text in the UI file to "Enter your phrase here."
# TODO: Pure Qt4 QTextEdit does not support placeholder texts, so this functionality is currently unavailable.
class PhrasePage(*ui_common.inherits_from_ui_file_with_name("phrasepage")):

    def __init__(self):
        super(PhrasePage, self).__init__()
        self.setupUi(self)

        self.initialising = True
        self.current_phrase = None  # type: autokey.model.phrase.Phrase

        for val in sorted(autokey.model.phrase.SEND_MODES.keys()):
            self.sendModeCombo.addItem(val)
        self.initialising = False

    def load(self, phrase: autokey.model.phrase.Phrase):
        self.current_phrase = phrase
        self.phraseText.setPlainText(phrase.phrase)
        self.showInTrayCheckbox.setChecked(phrase.show_in_tray_menu)

        for k, v in autokey.model.phrase.SEND_MODES.items():
            if v == phrase.sendMode:
                self.sendModeCombo.setCurrentIndex(self.sendModeCombo.findText(k))
                break

        if self.is_new_item():
            self.urlLabel.setEnabled(False)
            self.urlLabel.setText("(Unsaved)")  # TODO: i18n
        else:
            ui_common.set_url_label(self.urlLabel, self.current_phrase.path)

        # TODO - re-enable me if restoring predictive functionality
        #self.predictCheckbox.setChecked(model.TriggerMode.PREDICTIVE in phrase.modes)

        self.promptCheckbox.setChecked(phrase.prompt)
        self.settingsWidget.load(phrase)

    def save(self):
        self.settingsWidget.save()
        self.current_phrase.phrase = str(self.phraseText.toPlainText())
        self.current_phrase.show_in_tray_menu = self.showInTrayCheckbox.isChecked()

        self.current_phrase.sendMode = autokey.model.phrase.SEND_MODES[str(self.sendModeCombo.currentText())]

        # TODO - re-enable me if restoring predictive functionality
        #if self.predictCheckbox.isChecked():
        #    self.currentPhrase.modes.append(model.TriggerMode.PREDICTIVE)

        self.current_phrase.prompt = self.promptCheckbox.isChecked()

        self.current_phrase.persist()
        ui_common.set_url_label(self.urlLabel, self.current_phrase.path)
        return False

    def get_current_item(self):
        """Returns the currently held item."""
        return self.current_phrase

    def set_item_title(self, title):
        self.current_phrase.description = title

    def rebuild_item_path(self):
        self.current_phrase.rebuild_path()

    def is_new_item(self):
        return self.current_phrase.path is None

    def reset(self):
        self.load(self.current_phrase)

    def validate(self):
        errors = []

        # Check phrase content
        phrase = str(self.phraseText.toPlainText())
        if ui_common.EMPTY_FIELD_REGEX.match(phrase):
            errors.append("The phrase content can't be empty")  # TODO: i18n

        # Check settings
        errors += self.settingsWidget.validate()

        if errors:
            msg = PROBLEM_MSG_SECONDARY.format('\n'.join([str(e) for e in errors]))
            QMessageBox.critical(self.window(), PROBLEM_MSG_PRIMARY, msg)

        return not bool(errors)

    def set_dirty(self):
        self.window().set_dirty()

    def undo(self):
        self.phraseText.undo()

    def redo(self):
        self.phraseText.redo()

    def insert_token(self, token):
        self.phraseText.insertPlainText(token)

    # --- Signal handlers
    def on_phraseText_textChanged(self):
        self.set_dirty()

    def on_phraseText_undoAvailable(self, state):
        self.window().set_undo_available(state)

    def on_phraseText_redoAvailable(self, state):
        self.window().set_redo_available(state)

    def on_predictCheckbox_stateChanged(self, state):
        self.set_dirty()

    def on_promptCheckbox_stateChanged(self, state):
        self.set_dirty()

    def on_showInTrayCheckbox_stateChanged(self, state):
        self.set_dirty()

    def on_sendModeCombo_currentIndexChanged(self, index):
        if not self.initialising:
            self.set_dirty()

    def on_urlLabel_leftClickedUrl(self, url=None):
        if url:
            subprocess.Popen(["/usr/bin/xdg-open", url])
