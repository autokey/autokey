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

from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QKeySequence, QCloseEvent
from PyQt5.QtWidgets import QApplication, QAction, QMenu


import autokey.common
import autokey.model.folder
import autokey.model.phrase
import autokey.model.script
import autokey.qtui.common
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants

from .settings import SettingsDialog
from . import dialogs

logger = __import__("autokey.logger").logger.get_logger(__name__)
PROBLEM_MSG_PRIMARY = "Some problems were found"
PROBLEM_MSG_SECONDARY = "%1\n\nYour changes have not been saved."


class ConfigWindow(*autokey.qtui.common.inherits_from_ui_file_with_name("mainwindow")):

    script_errors_available = pyqtSignal(bool, name="script_errors_available")

    def __init__(self, app: QApplication):
        super().__init__()
        self.setupUi(self)
        self.about_dialog = dialogs.AboutAutokeyDialog(self)
        self.show_script_errors_dialog = self._create_show_recent_script_errors_dialog()
        self.app = app
        self.action_create = self._create_action_create()
        self.toolbar.insertAction(self.action_save, self.action_create)  # Insert before action_save, i.e. at index 0
        self._connect_all_file_menu_signals()
        self._connect_all_edit_menu_signals()
        self._connect_all_tools_menu_signals()
        self._connect_all_settings_menu_signals()
        self._connect_all_help_menu_signals()
        self._initialise_action_states()
        self._set_platform_specific_keyboard_shortcuts()
        self.central_widget.init(app)
        self.central_widget.populate_tree(self.app.configManager)

    def _create_action_create(self) -> QAction:
        """
        The action_create action contains a menu with all four "new" actions. It is inserted into the main window
        tool bar and lets the user create new items in the file tree.
        QtCreator currently does not support defining such actions that open a menu with choices, so do it in code.
        """
        icon = QIcon.fromTheme("document-new")
        action_create = QAction(icon, "New…", self)
        create_menu = QMenu(self)
        create_menu.insertActions(None, (  # "Insert before None", so append all items to the (empty) action list
            self.action_new_top_folder,
            self.action_new_sub_folder,
            self.action_new_phrase,
            self.action_new_script
        ))
        action_create.setMenu(create_menu)
        return action_create

    def _create_show_recent_script_errors_dialog(self) -> dialogs.ShowRecentScriptErrorsDialog:
        show_script_errors_dialog = dialogs.ShowRecentScriptErrorsDialog(self)
        # Forward the signal from the dialog instance to the own signal
        show_script_errors_dialog.script_errors_available.connect(self.script_errors_available)
        return show_script_errors_dialog

    def _connect_all_file_menu_signals(self):
        # Show the action_create popup menu regardless where the user places the click.
        # The Action is displayed as "[<icon>]v". Clicking on the downwards arrow opens the popup menu as
        # expected, but clicking on the larger icon does nothing by default, because no action is associated.
        # The intention is to show the popup regardless of where the user places the click, so call the containing
        # button’s showMenu when the action itself is pressed.
        #
        # Unlike other methods using action_create.menu().exec_() or .popup(position), this way is 100% UI consistent.
        self.action_create.triggered.connect(self.toolbar.widgetForAction(self.action_create).showMenu)
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
        self.action_show_last_script_errors.triggered.connect(self.show_script_errors_dialog.update_and_show)
        # Only enable action_show_last_script_errors if script errors are recorded.
        # Automatically disable the action if no errors are viewable to prevent the user from seeing a dialogue window
        # in some undefined state.
        self.script_errors_available.connect(self.action_show_last_script_errors.setEnabled)

        self.action_record_script.triggered.connect(self.on_record)
        self.action_run_script.triggered.connect(self.on_run_script)
        # Add all defined macros to the »Insert Macros« menu
        self.app.service.phraseRunner.macroManager.get_menu(self.on_insert_macro, self.menu_insert_macros)

    def _connect_all_settings_menu_signals(self):
        # TODO: Connect and implement unconnected actions
        app = QApplication.instance()
        # Sync the action_enable_monitoring checkbox with the global state. Prevents a desync when the global hotkey
        # is used
        app.monitoring_disabled.connect(self.action_enable_monitoring.setChecked)

        self.action_enable_monitoring.triggered.connect(app.toggle_service)
        self.action_show_log_view.triggered.connect(self.on_show_log)

        self.action_configure_shortcuts.triggered.connect(self._none_action)  # Currently not shown in any menu
        self.action_configure_toolbars.triggered.connect(self._none_action)  # Currently not shown in any menu
        # Both actions above were part of the KXMLGUI window functionality and allowed to customize keyboard shortcuts
        # and toolbar items
        self.action_configure_autokey.triggered.connect(self.on_advanced_settings)

    def _connect_all_help_menu_signals(self):
        self.action_show_online_manual.triggered.connect(lambda: self.open_external_url(autokey.common.HELP_URL))
        self.action_show_faq.triggered.connect(lambda: self.open_external_url(autokey.common.FAQ_URL))
        self.action_show_api.triggered.connect(lambda: self.open_external_url(autokey.common.API_URL))
        self.action_report_bug.triggered.connect(lambda: self.open_external_url(autokey.common.BUG_URL))
        self.action_about_autokey.triggered.connect(self.about_dialog.show)
        self.action_about_qt.triggered.connect(QApplication.aboutQt)

    def _initialise_action_states(self):
        """
        Some menu actions have on/off states that have to be initialised. Perform all non-trivial action state
        initialisations.
        Trivial ones (i.e. setting to some constant) are done in the Qt UI file,
        so only perform those that require some run-time state or configuration value here.
        """
        self.action_enable_monitoring.setChecked(self.app.service.is_running())
        self.action_enable_monitoring.setEnabled(not self.app.serviceDisabled)

    def _set_platform_specific_keyboard_shortcuts(self):
        """
        QtDesigner does not support QKeySequence::StandardKey enum based default keyboard shortcuts.
        This means that all default key combinations ("Save", "Quit", etc) have to be defined in code.
        """
        self.action_new_phrase.setShortcuts(QKeySequence.New)
        self.action_save.setShortcuts(QKeySequence.Save)
        self.action_close_window.setShortcuts(QKeySequence.Close)
        self.action_quit.setShortcuts(QKeySequence.Quit)

        self.action_undo.setShortcuts(QKeySequence.Undo)
        self.action_redo.setShortcuts(QKeySequence.Redo)
        self.action_cut_item.setShortcuts(QKeySequence.Cut)
        self.action_copy_item.setShortcuts(QKeySequence.Copy)
        self.action_paste_item.setShortcuts(QKeySequence.Paste)
        self.action_delete_item.setShortcuts(QKeySequence.Delete)

        self.action_configure_autokey.setShortcuts(QKeySequence.Preferences)

    def _none_action(self):
        import warnings
        warnings.warn("Unconnected menu item clicked! Nothing happens…", UserWarning)

    def set_dirty(self):
        self.central_widget.set_dirty(True)
        self.action_save.setEnabled(True)

    def closeEvent(self, event: QCloseEvent):
        """
        This function is automatically called when the window is closed using the close [X] button in the window
        decorations or by right clicking in the system window list and using the close action, or similar ways to close
        the window.
        Just ignore this event and simulate that the user used the action_close_window instead.

        To quote the Qt5 QCloseEvent documentation: If you do not want your widget to be hidden, or want some special
        handling, you should reimplement the event handler and ignore() the event.
        """
        event.ignore()
        # Be safe and emit this signal, because it might be connected to multiple slots.
        self.action_close_window.triggered.emit(True)

    def config_modified(self):
        pass
        
    def is_dirty(self):
        return self.central_widget.dirty
        
    def update_actions(self, items, changed):
        if len(items) > 0:
            can_create = isinstance(items[0], autokey.model.folder.Folder) and len(items) == 1
            can_copy = True
            for item in items:
                if isinstance(item, autokey.model.folder.Folder):
                    can_copy = False
                    break
            
            self.action_new_top_folder.setEnabled(True)
            self.action_new_sub_folder.setEnabled(can_create)
            self.action_new_phrase.setEnabled(can_create)
            self.action_new_script.setEnabled(can_create)
            
            self.action_copy_item.setEnabled(can_copy)
            self.action_clone_item.setEnabled(can_copy)
            self.action_paste_item.setEnabled(can_create and len(self.central_widget.cutCopiedItems) > 0)
            self.action_record_script.setEnabled(isinstance(items[0], autokey.model.script.Script) and len(items) == 1)
            self.action_run_script.setEnabled(isinstance(items[0], autokey.model.script.Script) and len(items) == 1)
            self.menu_insert_macros.setEnabled(isinstance(items[0], autokey.model.phrase.Phrase) and len(items) == 1)

            if changed:
                self.action_save.setEnabled(False)
                self.action_undo.setEnabled(False)
                self.action_redo.setEnabled(False)
        
    def set_undo_available(self, state):
        self.action_undo.setEnabled(state)
        
    def set_redo_available(self, state):
        self.action_redo.setEnabled(state)

    def save_completed(self, persist_global):
        logger.debug("Saving completed. persist_global: {}".format(persist_global))
        self.action_save.setEnabled(False)
        self.app.config_altered(persist_global)
        
    def cancel_record(self):
        if self.action_record_script.isChecked():
            self.action_record_script.setChecked(False)
            self.central_widget.recorder.stop()
        
    # ---- Signal handlers ----
    
    def queryClose(self):
        cm.ConfigManager.SETTINGS[cm_constants.HPANE_POSITION] = self.central_widget.splitter.sizes()[0] + 4
        cm.ConfigManager.SETTINGS[cm_constants.COLUMN_WIDTHS] = [
            self.central_widget.treeWidget.columnWidth(column_index) for column_index in range(3)
        ]
        
        if self.is_dirty():
            if self.central_widget.promptToSave():
                return False

        self.hide()
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
            dlg = dialogs.RecordDialog(self, self._do_record)
            dlg.show()
        else:
            self.central_widget.recorder.stop()
            
    def _do_record(self, ok: bool, record_keyboard: bool, record_mouse: bool, delay: float):
        if ok:
            self.central_widget.recorder.set_record_keyboard(record_keyboard)
            self.central_widget.recorder.set_record_mouse(record_mouse)
            self.central_widget.recorder.start(delay)
        else:
            self.action_record_script.setChecked(False)

    def on_run_script(self):
        script = self.central_widget.get_selected_item()[0]
        QTimer.singleShot(
            2000,  # Fix the GUI tooltip for action_run_script when changing this!
            (lambda: self.app.service.scriptRunner.execute_script(
                script
            ))
        )

    # Settings Menu
            
    def on_advanced_settings(self):
        s = SettingsDialog(self)
        s.show()

    def on_show_log(self):
        self.central_widget.listWidget.setVisible(self.action_show_log_view.isChecked())

    # Help Menu

    @staticmethod
    def open_external_url(url: str):
        webbrowser.open(url, False, True)
