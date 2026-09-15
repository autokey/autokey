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

        self._apply_editor_theme(lex)

    def _apply_editor_theme(self, lex: Qsci.QsciLexerPython):
        from PyQt5.QtGui import QColor
        from PyQt5.QtWidgets import QApplication

        palette = QApplication.palette()
        base = palette.color(palette.Base)
        # Determine if system theme is dark by checking luminance of Base color
        r, g, b = base.red(), base.green(), base.blue()
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        is_dark = luminance < 128

        if is_dark:
            # Dark theme — VS Code Dark+ inspired
            bg          = base
            fg          = QColor("#d4d4d4")
            caret       = QColor("#ffffff")
            caret_line  = QColor("#2a2a2a")
            sel_bg      = palette.color(palette.Highlight)
            sel_fg      = palette.color(palette.HighlightedText)
            margin_bg   = QColor("#252526")
            margin_fg   = QColor("#858585")
            guide       = QColor("#404040")
            brace_bg    = QColor("#3b3b3b")
            brace_fg    = QColor("#ffd700")
            brace_bad   = QColor("#f44747")
            token_colors = {
                Qsci.QsciLexerPython.Default:                   ("#d4d4d4", "#1e1e1e"),
                Qsci.QsciLexerPython.Comment:                   ("#6a9955", "#1e1e1e"),
                Qsci.QsciLexerPython.CommentBlock:              ("#6a9955", "#1e1e1e"),
                Qsci.QsciLexerPython.Number:                    ("#b5cea8", "#1e1e1e"),
                Qsci.QsciLexerPython.DoubleQuotedString:        ("#ce9178", "#1e1e1e"),
                Qsci.QsciLexerPython.SingleQuotedString:        ("#ce9178", "#1e1e1e"),
                Qsci.QsciLexerPython.TripleSingleQuotedString:  ("#ce9178", "#1e1e1e"),
                Qsci.QsciLexerPython.TripleDoubleQuotedString:  ("#ce9178", "#1e1e1e"),
                Qsci.QsciLexerPython.Keyword:                   ("#569cd6", "#1e1e1e"),
                Qsci.QsciLexerPython.Operator:                  ("#d4d4d4", "#1e1e1e"),
                Qsci.QsciLexerPython.Identifier:                ("#d4d4d4", "#1e1e1e"),
                Qsci.QsciLexerPython.FunctionMethodName:        ("#dcdcaa", "#1e1e1e"),
                Qsci.QsciLexerPython.ClassName:                 ("#4ec9b0", "#1e1e1e"),
                Qsci.QsciLexerPython.Decorator:                 ("#c586c0", "#1e1e1e"),
                Qsci.QsciLexerPython.HighlightedIdentifier:     ("#9cdcfe", "#1e1e1e"),
                Qsci.QsciLexerPython.UnclosedString:            ("#ce9178", "#3b0000"),
            }
        else:
            # Light theme — VS Code Light+ inspired
            bg          = base
            fg          = QColor("#000000")
            caret       = QColor("#000000")
            caret_line  = QColor("#e8e8e8")
            sel_bg      = palette.color(palette.Highlight)
            sel_fg      = palette.color(palette.HighlightedText)
            margin_bg   = QColor("#f3f3f3")
            margin_fg   = QColor("#6e6e6e")
            guide       = QColor("#d0d0d0")
            brace_bg    = QColor("#e8e8e8")
            brace_fg    = QColor("#0000ff")
            brace_bad   = QColor("#ff0000")
            token_colors = {
                Qsci.QsciLexerPython.Default:                   ("#000000", "#ffffff"),
                Qsci.QsciLexerPython.Comment:                   ("#008000", "#ffffff"),
                Qsci.QsciLexerPython.CommentBlock:              ("#008000", "#ffffff"),
                Qsci.QsciLexerPython.Number:                    ("#098658", "#ffffff"),
                Qsci.QsciLexerPython.DoubleQuotedString:        ("#a31515", "#ffffff"),
                Qsci.QsciLexerPython.SingleQuotedString:        ("#a31515", "#ffffff"),
                Qsci.QsciLexerPython.TripleSingleQuotedString:  ("#a31515", "#ffffff"),
                Qsci.QsciLexerPython.TripleDoubleQuotedString:  ("#a31515", "#ffffff"),
                Qsci.QsciLexerPython.Keyword:                   ("#0000ff", "#ffffff"),
                Qsci.QsciLexerPython.Operator:                  ("#000000", "#ffffff"),
                Qsci.QsciLexerPython.Identifier:                ("#000000", "#ffffff"),
                Qsci.QsciLexerPython.FunctionMethodName:        ("#795e26", "#ffffff"),
                Qsci.QsciLexerPython.ClassName:                 ("#267f99", "#ffffff"),
                Qsci.QsciLexerPython.Decorator:                 ("#af00db", "#ffffff"),
                Qsci.QsciLexerPython.HighlightedIdentifier:     ("#001080", "#ffffff"),
                Qsci.QsciLexerPython.UnclosedString:            ("#a31515", "#fff0f0"),
            }

        # Apply editor-level colors
        self.scriptCodeEditor.setPaper(bg)
        self.scriptCodeEditor.setColor(fg)
        self.scriptCodeEditor.setCaretForegroundColor(caret)
        self.scriptCodeEditor.setCaretLineVisible(True)
        self.scriptCodeEditor.setCaretLineBackgroundColor(caret_line)
        self.scriptCodeEditor.setSelectionBackgroundColor(sel_bg)
        self.scriptCodeEditor.setSelectionForegroundColor(sel_fg)
        self.scriptCodeEditor.setMarginsBackgroundColor(margin_bg)
        self.scriptCodeEditor.setMarginsForegroundColor(margin_fg)
        self.scriptCodeEditor.setIndentationGuidesBackgroundColor(guide)
        self.scriptCodeEditor.setIndentationGuidesForegroundColor(guide)
        self.scriptCodeEditor.setMatchedBraceBackgroundColor(brace_bg)
        self.scriptCodeEditor.setMatchedBraceForegroundColor(brace_fg)
        self.scriptCodeEditor.setUnmatchedBraceBackgroundColor(brace_bg)
        self.scriptCodeEditor.setUnmatchedBraceForegroundColor(brace_bad)

        # Apply lexer token colors
        lex.setDefaultPaper(bg)
        lex.setDefaultColor(fg)
        for style, (fg_hex, bg_hex) in token_colors.items():
            lex.setColor(QColor(fg_hex), style)
            lex.setPaper(QColor(bg_hex), style)
            lex.setFont(ui_common.monospace_font(), style)

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
