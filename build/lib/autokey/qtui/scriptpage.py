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

import os.path
import subprocess

from PyQt5 import Qsci
from PyQt5.QtWidgets import QMessageBox

import autokey.model.script
from autokey.qtui import common as ui_common

API_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/api.txt")

PROBLEM_MSG_PRIMARY = "Some problems were found"
PROBLEM_MSG_SECONDARY = "{}\n\nYour changes have not been saved."


class ScriptPage(*ui_common.inherits_from_ui_file_with_name("scriptpage")):

    def __init__(self):
        super(ScriptPage, self).__init__()
        self.setupUi(self)

        self.scriptCodeEditor.setUtf8(1)

        lex = Qsci.QsciLexerPython(self)
        api = Qsci.QsciAPIs(lex)
        api.load(API_FILE)
        api.prepare()
        self.current_script = None  # type: autokey.model.script.Script
        self.scriptCodeEditor.setLexer(lex)

        self.scriptCodeEditor.setBraceMatching(Qsci.QsciScintilla.SloppyBraceMatch)
        self.scriptCodeEditor.setAutoIndent(True)
        self.scriptCodeEditor.setBackspaceUnindents(True)
        self.scriptCodeEditor.setIndentationWidth(4)
        self.scriptCodeEditor.setIndentationGuides(True)
        self.scriptCodeEditor.setIndentationsUseTabs(False)
        self.scriptCodeEditor.setAutoCompletionThreshold(3)
        self.scriptCodeEditor.setAutoCompletionSource(Qsci.QsciScintilla.AcsAll)
        self.scriptCodeEditor.setCallTipsStyle(Qsci.QsciScintilla.CallTipsNoContext)
        lex.setFont(ui_common.monospace_font())

    def load(self, script: autokey.model.script.Script):
        self.current_script = script
        self.scriptCodeEditor.clear()
        self.scriptCodeEditor.append(script.code)
        self.showInTrayCheckbox.setChecked(script.show_in_tray_menu)
        self.promptCheckbox.setChecked(script.prompt)
        self.settingsWidget.load(script)
        self.window().set_undo_available(False)
        self.window().set_redo_available(False)

        if self.is_new_item():
            self.urlLabel.setEnabled(False)
            self.urlLabel.setText("(Unsaved)")  # TODO: i18n
        else:
            ui_common.set_url_label(self.urlLabel, self.current_script.path)

    def save(self):
        self.settingsWidget.save()
        self.current_script.code = str(self.scriptCodeEditor.text())
        self.current_script.show_in_tray_menu = self.showInTrayCheckbox.isChecked()
        self.current_script.prompt = self.promptCheckbox.isChecked()
        self.current_script.persist()
        ui_common.set_url_label(self.urlLabel, self.current_script.path)
        return False

    def get_current_item(self):
        """Returns the currently held item."""
        return self.current_script

    def set_item_title(self, title):
        self.current_script.description = title

    def rebuild_item_path(self):
        self.current_script.rebuild_path()

    def is_new_item(self):
        return self.current_script.path is None

    def reset(self):
        self.load(self.current_script)
        self.window().set_undo_available(False)
        self.window().set_redo_available(False)

    def set_dirty(self):
        self.window().set_dirty()

    def start_record(self):
        self.scriptCodeEditor.append("\n")

    def start_key_sequence(self):
        self.scriptCodeEditor.append("keyboard.send_keys(\"")

    def end_key_sequence(self):
        self.scriptCodeEditor.append("\")\n")

    def append_key(self, key):
        self.scriptCodeEditor.append(key)

    def append_hotkey(self, key, modifiers):
        keyString = self.current_script.get_hotkey_string(key, modifiers)
        self.scriptCodeEditor.append(keyString)

    def append_mouseclick(self, xCoord, yCoord, button, windowTitle):
        self.scriptCodeEditor.append("mouse.click_relative(%d, %d, %d) # %s\n" % (xCoord, yCoord, int(button), windowTitle))

    def undo(self):
        self.scriptCodeEditor.undo()
        self.window().set_undo_available(self.scriptCodeEditor.isUndoAvailable())

    def redo(self):
        self.scriptCodeEditor.redo()
        self.window().set_redo_available(self.scriptCodeEditor.isRedoAvailable())

    def validate(self):
        errors = []

        # Check script code
        code = str(self.scriptCodeEditor.text())
        if ui_common.EMPTY_FIELD_REGEX.match(code):
            errors.append("The script code can't be empty")  # TODO: i18n

        # Check settings
        errors += self.settingsWidget.validate()

        if errors:
            msg = PROBLEM_MSG_SECONDARY.format('\n'.join([str(e) for e in errors]))
            header = PROBLEM_MSG_PRIMARY
            QMessageBox.critical(self.window(), header, msg)

        return not bool(errors)

    # --- Signal handlers

    def on_scriptCodeEditor_textChanged(self):
        self.set_dirty()
        self.window().set_undo_available(self.scriptCodeEditor.isUndoAvailable())
        self.window().set_redo_available(self.scriptCodeEditor.isRedoAvailable())

    def on_promptCheckbox_stateChanged(self, state):
        self.set_dirty()

    def on_showInTrayCheckbox_stateChanged(self, state):
        self.set_dirty()

    def on_urlLabel_leftClickedUrl(self, url=None):
        if url: subprocess.Popen(["/usr/bin/xdg-open", url])
