# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import webbrowser
import time
import logging
import threading

from PyQt4.QtGui import QKeySequence, QMessageBox

import autokey.common
from autokey import model
from autokey import configmanager as cm

import autokey.qtui.common
from . import dialogs
from .settingsdialog import SettingsDialog


PROBLEM_MSG_PRIMARY = "Some problems were found"
PROBLEM_MSG_SECONDARY = "%1\n\nYour changes have not been saved."

_logger = autokey.qtui.common.logger.getChild("configwindow")  # type: logging.Logger


class ConfigWindow(*autokey.qtui.common.inherits_from_ui_file_with_name("mainwindow")):

    def __init__(self, app):
        super().__init__()
        self.setupUi(self)
        self.central_widget.init(app)
        self.app = app
        self._connect_all_file_menu_signals()
        self._connect_all_edit_menu_signals()
        self._connect_all_tools_menu_signals()
        self._connect_all_settings_menu_signals()
        self._connect_all_help_menu_signals()
        self._initialise_action_states()
        self._set_platform_specific_keyboard_shortcuts()

        self.central_widget.populate_tree(self.app.configManager)
        # self.central_widget.set_splitter(self.size())  # TODO: needed?

        # self.setAutoSaveSettings()  # TODO: KDE4 function?

    def _connect_all_file_menu_signals(self):

        self.action_new_top_folder.triggered.connect(self.central_widget.on_new_topfolder)
        self.action_new_sub_folder.triggered.connect(self.central_widget.on_new_folder)
        self.action_new_phrase.triggered.connect(self.central_widget.on_new_phrase)
        self.action_new_script.triggered.connect(self.central_widget.on_new_script)
        self.action_save.triggered.connect(self.central_widget.on_save)
        self.action_close_window.triggered.connect(self.on_close)
        self.action_quit.triggered.connect(self.on_quit)

    def _connect_all_edit_menu_signals(self):
        self.action_undo.triggered.connect(self.central_widget.on_undo)
        self.action_redo.triggered.connect(self.central_widget.on_redo)
        self.action_cut_item.triggered.connect(self.central_widget.on_cut)
        self.action_copy_item.triggered.connect(self.central_widget.on_copy)
        self.action_paste_item.triggered.connect(self.central_widget.on_paste)
        self.action_clone_item.triggered.connect(self.central_widget.on_clone)
        self.action_delete_item.triggered.connect(self.central_widget.on_delete)
        self.action_rename_item.triggered.connect(self.central_widget.on_rename)

    def _connect_all_tools_menu_signals(self):
        self.action_show_last_script_error.triggered.connect(self.on_show_error)
        self.action_record_script.triggered.connect(self.on_record)
        self.action_run_script.triggered.connect(self.on_run_script)
        # Add all defined macros to the »Insert Macros« menu
        self.app.service.phraseRunner.macroManager.get_menu(self.on_insert_macro, self.menu_insert_macros)

    def _connect_all_settings_menu_signals(self):
        # TODO: Connect unconnected actions
        self.action_enable_monitoring.triggered.connect(self.on_enable_toggled)
        self.action_show_toolbar.triggered.connect(self._none_action)
        self.action_show_log_view.triggered.connect(self.on_show_log)
        self.action_configure_shortcuts.triggered.connect(self._none_action)
        self.action_configure_toolbars.triggered.connect(self._none_action)
        self.action_configure_autokey.triggered.connect(self.on_advanced_settings)

    def _connect_all_help_menu_signals(self):
        self.action_show_online_manual.triggered.connect(self.on_show_help)
        self.action_show_faq.triggered.connect(self.on_show_faq)
        self.action_show_api.triggered.connect(self.on_show_api)
        self.action_report_bug.triggered.connect(self.on_report_bug)
        self.action_about_autokey.triggered.connect(self.on_about)
        self.action_about_qt.triggered.connect(self._none_action)  # TODO

    def _initialise_action_states(self):
        """
        Perform all non-trivial action state initialisations.
        Trivial ones (i.e. setting to some constant) are done in the Qt UI file,
        so only perform those that require some run-time state or configuration value here.
        """
        self.action_enable_monitoring.setChecked(self.app.service.is_running())
        self.action_enable_monitoring.setEnabled(not self.app.serviceDisabled)

    def _set_platform_specific_keyboard_shortcuts(self):
        """
        QtDesigner does not support QKeySequence::StandardKey enum based default keyboard shortcuts.
        This means that all default key combinations ("Save", "Quit", etc) have to be defined in code.
        :return:
        """
        self.action_save.setShortcuts(QKeySequence.Save)

    def _none_action(self):
        import warnings
        warnings.warn("Unconnected menu item clicked!", UserWarning)

    def set_dirty(self):
        self.central_widget.set_dirty(True)
        self.action_save.setEnabled(True)

    def config_modified(self):
        pass
        
    def is_dirty(self):
        return self.central_widget.dirty
        
    def update_actions(self, items, changed):
        if len(items) > 0:
            canCreate = isinstance(items[0], model.Folder) and len(items) == 1
            canCopy = True
            for item in items:
                if isinstance(item, model.Folder):
                    canCopy = False
                    break        
            
            #self.create.setEnabled(True)  # TODO: This is used in the toolbar to create a menu having all 4 options.
            self.action_new_top_folder.setEnabled(True)
            self.action_new_sub_folder.setEnabled(canCreate)
            self.action_new_phrase.setEnabled(canCreate)
            self.action_new_script.setEnabled(canCreate)
            
            self.action_copy_item.setEnabled(canCopy)
            self.action_clone_item.setEnabled(canCopy)
            self.action_paste_item.setEnabled(canCreate and len(self.central_widget.cutCopiedItems) > 0)
            self.action_record_script.setEnabled(isinstance(items[0], model.Script) and len(items) == 1)
            self.action_run_script.setEnabled(isinstance(items[0], model.Script) and len(items) == 1)
            # self.insertMacro.setEnabled(isinstance(items[0], model.Phrase) and len(items) == 1)  # TODO: fixme

            if changed:
                self.action_save.setEnabled(False)
                self.action_undo.setEnabled(False)
                self.action_redo.setEnabled(False)
        
    def set_undo_available(self, state):
        self.action_undo.setEnabled(state)
        
    def set_redo_available(self, state):
        self.action_redo.setEnabled(state)

    def save_completed(self, persist_global):
        _logger.debug("Saving completed. persist_global: {}".format(persist_global))
        self.action_save.setEnabled(False)
        self.app.config_altered(persist_global)
        
    def cancel_record(self):
        if self.action_record_script.isChecked():
            self.action_record_script.setChecked(False)
            self.central_widget.recorder.stop()
        
    # ---- Signal handlers ----
    
    def queryClose(self):
        cm.ConfigManager.SETTINGS[cm.HPANE_POSITION] = self.central_widget.splitter.sizes()[0] + 4
        l = []  # TODO: list comprehension
        for x in range(3):
            l.append(self.central_widget.treeWidget.columnWidth(x))
        cm.ConfigManager.SETTINGS[cm.COLUMN_WIDTHS] = l
        
        if self.is_dirty():
            if self.central_widget.promptToSave():
                return False

        self.hide()
        logging.getLogger().removeHandler(self.central_widget.logHandler)
        return True
    
    # File Menu

    def on_close(self):
        self.cancel_record()
        self.queryClose()
        
    def on_quit(self):
        if self.queryClose():
            self.app.shutdown()
            
    # Edit Menu
    
    def on_insert_macro(self, macro):
        token = macro.get_token()
        self.central_widget.phrasePage.insert_token(token)
            
    def on_record(self):
        if self.action_record_script.isChecked():
            dlg = dialogs.RecordDialog(self, self.__doRecord)
            dlg.show()
        else:
            self.central_widget.recorder.stop()
            
    def __doRecord(self, ok, recKb, recMouse, delay):
        if ok:
            self.central_widget.recorder.set_record_keyboard(recKb)
            self.central_widget.recorder.set_record_mouse(recMouse)
            self.central_widget.recorder.start(delay)
        else:
            self.action_record_script.setChecked(False)

    def on_run_script(self):
        t = threading.Thread(target=self.__runScript)
        t.start()

    def __runScript(self):
        script = self.central_widget.get_selected_item()[0]
        time.sleep(2)  # Fix the GUI tooltip for action_run_script when changing this!
        self.app.service.scriptRunner.execute(script)
    
    # Settings Menu
        
    def on_enable_toggled(self):
        if self.action_enable_monitoring.isChecked():
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_advanced_settings(self):
        s = SettingsDialog(self)
        s.show()

    def on_show_log(self):
        self.central_widget.listWidget.setVisible(self.action_show_log_view.isChecked())
        
    def on_show_error(self):
        self.app.show_script_error()
            
    # Help Menu
            
    def on_show_faq(self):
        webbrowser.open(autokey.common.FAQ_URL, False, True)
        
    def on_show_help(self):
        webbrowser.open(autokey.common.HELP_URL, False, True)

    def on_show_api(self):
        webbrowser.open(autokey.common.API_URL, False, True)
        
    def on_report_bug(self):
        webbrowser.open(autokey.common.BUG_URL, False, True)

    def on_about(self):
        QMessageBox.information(self, "About", "The About dialog is currently unavailable.", QMessageBox.Ok)
