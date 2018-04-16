# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import webbrowser
import time
import logging
import threading

from PyKDE4.kdeui import *  # TODO: Remove
from PyKDE4.kdecore import i18n, ki18n  # TODO: Remove

import PyQt4.QtGui
from PyQt4.QtCore import SIGNAL

import autokey.common
from autokey import model
from autokey import configmanager as cm

import autokey.qtui.common
from . import dialogs
from .settingsdialog import SettingsDialog


ACTION_DESCRIPTION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/gui.xml")


PROBLEM_MSG_PRIMARY = ki18n("Some problems were found")
PROBLEM_MSG_SECONDARY = "%1\n\nYour changes have not been saved."

_logger = autokey.qtui.common.logger.getChild("configwindow")  # type: logging.Logger


# ---- Configuration window
from . import centralwidget


class ConfigWindow(KXmlGuiWindow):

    def __init__(self, app):
        KXmlGuiWindow.__init__(self)
        self.centralWidget = centralwidget.CentralWidget(self, app)
        self.setCentralWidget(self.centralWidget)
        self.app = app
        
        # File Menu
        self.create = self.__createMenuAction("create", i18n("New"), iconName="document-new")
        self.create.setDelayed(False)
        
        self.newTopFolder = self.__createAction("new-top-folder", i18n("Folder"), "folder-new", self.centralWidget.on_new_topfolder)
        self.newFolder = self.__createAction("new-folder", i18n("Sub-folder"), "folder-new", self.centralWidget.on_new_folder)
        self.newPhrase = self.__createAction("new-phrase", i18n("Phrase"), "text-x-generic", self.centralWidget.on_new_phrase, KStandardShortcut.New)
        self.newScript = self.__createAction("new-script", i18n("Script"), "text-x-python", self.centralWidget.on_new_script)
        self.newScript.setShortcut(PyQt4.QtGui.QKeySequence("Ctrl+Shift+n"))
        self.save = self.__createAction("save", i18n("Save"), "document-save", self.centralWidget.on_save, KStandardShortcut.Save)
        
        self.create.addAction(self.newTopFolder)
        self.create.addAction(self.newFolder)
        self.create.addAction(self.newPhrase)
        self.create.addAction(self.newScript)

        self.close = self.__createAction("close-window", i18n("Close Window"), "window-close", self.on_close, KStandardShortcut.Close)
        KStandardAction.quit(self.on_quit, self.actionCollection())

        # Edit Menu 
        self.cut = self.__createAction("cut-item", i18n("Cut Item"), "edit-cut", self.centralWidget.on_cut)
        self.copy = self.__createAction("copy-item", i18n("Copy Item"), "edit-copy", self.centralWidget.on_copy)
        self.paste = self.__createAction("paste-item", i18n("Paste Item"), "edit-paste", self.centralWidget.on_paste)
        self.clone = self.__createAction("clone-item", i18n("Clone Item"), "edit-copy", self.centralWidget.on_clone)
        #self.cut.setShortcut(PyQt4.QtGui.QKeySequence("Ctrl+Shift+x"))
        #self.copy.setShortcut(PyQt4.QtGui.QKeySequence("Ctrl+Shift+c"))
        self.clone.setShortcut(PyQt4.QtGui.QKeySequence("Ctrl+Shift+c"))
        
        self.undo = self.__createAction("undo", i18n("Undo"), "edit-undo", self.centralWidget.on_undo, KStandardShortcut.Undo)
        self.redo = self.__createAction("redo", i18n("Redo"), "edit-redo", self.centralWidget.on_redo, KStandardShortcut.Redo)
        
        rename = self.__createAction("rename", i18n("Rename"), None, self.centralWidget.on_rename)
        rename.setShortcut(PyQt4.QtGui.QKeySequence("f2"))
        
        self.delete = self.__createAction("delete-item", i18n("Delete"), "edit-delete", self.centralWidget.on_delete)
        self.delete.setShortcut(PyQt4.QtGui.QKeySequence("Ctrl+d"))
        self.record = self.__createToggleAction("record", i18n("Record Script"), self.on_record, "media-record")
        self.run = self.__createAction("run", i18n("Run Script"), "media-playback-start", self.on_run_script)
        self.run.setShortcut(PyQt4.QtGui.QKeySequence("f8"))
        self.insertMacro = self.__createMenuAction("insert-macro", i18n("Insert Macro"), None, None)
        menu = app.service.phraseRunner.macroManager.get_menu(self.on_insert_macro, self.insertMacro.menu())
        
        # Settings Menu
        self.enable = self.__createToggleAction("enable-monitoring", i18n("Enable Monitoring"), self.on_enable_toggled)
        self.advancedSettings = self.__createAction("advanced-settings", i18n("Configure AutoKey"), "configure", self.on_advanced_settings)
        self.__createAction("script-error", i18n("View script error"), "dialog-error", self.on_show_error)
        self.showLog = self.__createToggleAction("show-log-view", i18n("Show log view"), self.on_show_log)
        self.showLog.setShortcut(PyQt4.QtGui.QKeySequence("f4"))
        
        # Help Menu
        self.__createAction("online-help", i18n("Online Manual"), "help-contents", self.on_show_help)
        self.__createAction("online-faq", i18n("F.A.Q."), "help-faq", self.on_show_faq)
        self.__createAction("online-api", i18n("Scripting Help"), None, self.on_show_api)
        self.__createAction("report-bug", i18n("Report a Bug"), "tools-report-bug", self.on_report_bug)
        self.__createAction("about", i18n("About AutoKey"), "help-about", self.on_about)

        self.setHelpMenuEnabled(True)

        # Log view context menu
        act = self.__createAction("clear-log", i18n("Clear Log"), None, self.centralWidget.on_clear_log)
        self.centralWidget.listWidget.addAction(act)
        act = self.__createAction("clear-log", i18n("Save Log As..."), None, self.centralWidget.on_save_log)
        self.centralWidget.listWidget.addAction(act)

        #self.createStandardStatusBarAction() # TODO statusbar
        options = KXmlGuiWindow.Default ^ KXmlGuiWindow.StandardWindowOptions(KXmlGuiWindow.StatusBar)
        #options = KXmlGuiWindow.Default # TODO  statusbar
        self.setupGUI(options)
        
        # Initialise action states
        self.enable.setChecked(self.app.service.is_running())
        self.enable.setEnabled(not self.app.serviceDisabled)
        self.undo.setEnabled(False)
        self.redo.setEnabled(False)
        
        self.centralWidget.populate_tree(self.app.configManager)
        self.centralWidget.set_splitter(self.size())
        
        self.setAutoSaveSettings()
        
    def set_dirty(self):
        self.centralWidget.set_dirty(True)
        self.save.setEnabled(True)

    def config_modified(self):
        pass
        
    def is_dirty(self):
        return self.centralWidget.dirty
        
    def update_actions(self, items, changed):
        if len(items) > 0:
            canCreate = isinstance(items[0], model.Folder) and len(items) == 1
            canCopy = True
            for item in items:
                if isinstance(item, model.Folder):
                    canCopy = False
                    break        
            
            self.create.setEnabled(True)
            self.newTopFolder.setEnabled(True)
            self.newFolder.setEnabled(canCreate)
            self.newPhrase.setEnabled(canCreate)
            self.newScript.setEnabled(canCreate)
            
            self.copy.setEnabled(canCopy)
            self.clone.setEnabled(canCopy)
            self.paste.setEnabled(canCreate and len(self.centralWidget.cutCopiedItems) > 0)
            self.record.setEnabled(isinstance(items[0], model.Script) and len(items) == 1)
            self.run.setEnabled(isinstance(items[0], model.Script) and len(items) == 1)
            self.insertMacro.setEnabled(isinstance(items[0], model.Phrase) and len(items) == 1)

            if changed:
                self.save.setEnabled(False)
                self.undo.setEnabled(False)
                self.redo.setEnabled(False)
        
    def set_undo_available(self, state):
        self.undo.setEnabled(state)
        
    def set_redo_available(self, state):
        self.redo.setEnabled(state)

    def save_completed(self, persist_global):
        _logger.debug("Saving completed. persist_global: {}".format(persist_global))
        self.save.setEnabled(False)
        self.app.config_altered(persist_global)
        
    def __createAction(self, actionName, name, iconName=None, target=None, shortcut=None):
        if iconName is not None:
            action = KAction(KIcon(iconName), name, self.actionCollection())
        else:
            action = KAction(name, self.actionCollection())
        
        if shortcut is not None:
            standardShortcut = KStandardShortcut.shortcut(shortcut)
            action.setShortcut(standardShortcut)

        if target is not None:
            self.connect(action, SIGNAL("triggered()"), target)
        self.actionCollection().addAction(actionName, action)
        return action


    def __createToggleAction(self, actionName, name, target, iconName=None):
        if iconName is not None:
            action = KToggleAction(KIcon(iconName), name, self.actionCollection())
        else:
            action = KToggleAction(name, self.actionCollection())
            
        if target is not None:
            self.connect(action, SIGNAL("triggered()"), target)
        self.actionCollection().addAction(actionName, action)
        return action
        
    def __createMenuAction(self, actionName, name, target=None, iconName=None):
        if iconName is not None:
            action = KActionMenu(KIcon(iconName), name, self.actionCollection())
        else:
            action = KActionMenu(name, self.actionCollection())
            
        if target is not None:
            self.connect(action, SIGNAL("triggered()"), target)
        self.actionCollection().addAction(actionName, action)
        return action
        
    def cancel_record(self):
        if self.record.isChecked():
            self.record.setChecked(False)
            self.centralWidget.recorder.stop()
        
    # ---- Signal handlers ----
    
    def queryClose(self):
        cm.ConfigManager.SETTINGS[cm.HPANE_POSITION] = self.centralWidget.splitter.sizes()[0] + 4
        l = []
        for x in range(3):
            l.append(self.centralWidget.treeWidget.columnWidth(x))
        cm.ConfigManager.SETTINGS[cm.COLUMN_WIDTHS] = l
        
        if self.is_dirty():
            if self.centralWidget.promptToSave():
                return False

        self.hide()
        logging.getLogger().removeHandler(self.centralWidget.logHandler)
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
        self.centralWidget.phrasePage.insert_token(token)
            
    def on_record(self):
        if self.record.isChecked():
            dlg = dialogs.RecordDialog(self, self.__doRecord)
            dlg.show()
        else:
            self.centralWidget.recorder.stop()
            
    def __doRecord(self, ok, recKb, recMouse, delay):
        if ok:
            self.centralWidget.recorder.set_record_keyboard(recKb)
            self.centralWidget.recorder.set_record_mouse(recMouse)
            self.centralWidget.recorder.start(delay)
        else:
            self.record.setChecked(False)

    def on_run_script(self):
        t = threading.Thread(target=self.__runScript)
        t.start()

    def __runScript(self):
        script = self.centralWidget.get_selected_item()[0]
        time.sleep(2)
        self.app.service.scriptRunner.execute(script)
    
    # Settings Menu
        
    def on_enable_toggled(self):
        if self.enable.isChecked():
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_advanced_settings(self):
        s = SettingsDialog(self)
        s.show()

    def on_show_log(self):
        self.centralWidget.listWidget.setVisible(self.showLog.isChecked())
        
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
        dlg = KAboutApplicationDialog(self.app.aboutData, self)
        dlg.show()

