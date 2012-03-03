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

import logging, sys, os, webbrowser, subprocess, time
from PyKDE4.kio import *
from PyKDE4.kdeui import *
from PyKDE4.kdecore import i18n, ki18n, KUrl
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, QVariant, Qt
from PyQt4 import Qsci
from autokey import common

#CONFIG_WINDOW_TITLE = i18n(common.CONFIG_WINDOW_TITLE)

ACTION_DESCRIPTION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/gui.xml")
API_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/api.txt")

from dialogs import *
from settingsdialog import SettingsDialog
from autokey.configmanager import *
from autokey.iomediator import Recorder
from autokey import model

PROBLEM_MSG_PRIMARY = ki18n("Some problems were found")
PROBLEM_MSG_SECONDARY = "%1\n\nYour changes have not been saved."

_logger = logging.getLogger("configwindow")

def set_url_label(button, path):
    button.setEnabled(True)
    
    if path.startswith(CONFIG_DEFAULT_FOLDER):
        text = path.replace(CONFIG_DEFAULT_FOLDER, i18n("(Default folder)"))
    else:
        text = path.replace(os.path.expanduser("~"), "~")
    
    button.setText(text)
    # TODO elide text?
    button.setUrl("file://" + path)

# ---- Internal widgets

import settingswidget

class SettingsWidget(QWidget, settingswidget.Ui_SettingsWidget):
    
    KEY_MAP = HotkeySettingsDialog.KEY_MAP
    REVERSE_KEY_MAP = HotkeySettingsDialog.REVERSE_KEY_MAP

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        settingswidget.Ui_SettingsWidget.__init__(self)
        self.setupUi(self)
            
        self.abbrDialog = AbbrSettingsDialog(self)
        self.hotkeyDialog = HotkeySettingsDialog(self)
        self.filterDialog = WindowFilterSettingsDialog(self)
        
    def load(self, item):
        self.currentItem = item
        
        self.abbrDialog.load(self.currentItem)
        if model.TriggerMode.ABBREVIATION in item.modes:
            self.abbrLabel.setText(item.get_abbreviations())
            self.clearAbbrButton.setEnabled(True)
            self.abbrEnabled = True
        else:
            self.abbrLabel.setText(i18n("(None configured)"))
            self.clearAbbrButton.setEnabled(False)
            self.abbrEnabled = False
        
        self.hotkeyDialog.load(self.currentItem)
        if model.TriggerMode.HOTKEY in item.modes:
            self.hotkeyLabel.setText(item.get_hotkey_string())
            self.clearHotkeyButton.setEnabled(True)
            self.hotkeyEnabled = True            
        else:
            self.hotkeyLabel.setText(i18n("(None configured)"))
            self.clearHotkeyButton.setEnabled(False)
            self.hotkeyEnabled = False
            
        self.filterDialog.load(self.currentItem)
        self.filterEnabled = False
        self.clearFilterButton.setEnabled(False)
        if item.has_filter() or item.inherits_filter():
            self.windowFilterLabel.setText(item.get_filter_regex())
            
            if not item.inherits_filter():            
                self.clearFilterButton.setEnabled(True)
                self.filterEnabled = True
        
        else:
            self.windowFilterLabel.setText(i18n("(None configured)"))
        
    def save(self):
        # Perform hotkey ungrab
        if model.TriggerMode.HOTKEY in self.currentItem.modes:
            self.topLevelWidget().app.hotkey_removed(self.currentItem)
        
        self.currentItem.set_modes([])
        if self.abbrEnabled:
            self.abbrDialog.save(self.currentItem)
        if self.hotkeyEnabled:
            self.hotkeyDialog.save(self.currentItem)
        if self.filterEnabled:
            self.filterDialog.save(self.currentItem)
        else:
            self.currentItem.set_window_titles(None)

        if self.hotkeyEnabled:
            self.topLevelWidget().app.hotkey_created(self.currentItem)
            
    def set_dirty(self):
        self.topLevelWidget().set_dirty()
        
    def validate(self):
        # Start by getting all applicable information
        if self.abbrEnabled:
            abbreviations = self.abbrDialog.get_abbrs()
        else:
            abbreviations = []
            
        if self.hotkeyEnabled:
            modifiers = self.hotkeyDialog.build_modifiers()
            key = self.hotkeyDialog.key
        else:
            modifiers = []
            key = None
        
        filterExpression = None
        if self.filterEnabled:
            filterExpression = self.filterDialog.get_filter_text()
        elif self.currentItem.parent is not None:
            r = self.currentItem.parent.get_applicable_regex(True)
            if r is not None:
                filterExpression = r.pattern
            
        # Validate
        ret = []
        
        configManager = self.topLevelWidget().app.configManager

        for abbr in abbreviations:        
            unique, conflicting = configManager.check_abbreviation_unique(abbr, filterExpression, self.currentItem)
            if not unique:
                msg = i18n("The abbreviation '%1' is already in use by the %2", abbr, str(conflicting))
                f = conflicting.get_applicable_regex()
                if f is not None:
                    msg += i18n(" for windows matching '%1'.", f.pattern)
                ret.append(msg)
                    
        unique, conflicting = configManager.check_hotkey_unique(modifiers, key, filterExpression, self.currentItem)
        if not unique:
            msg = i18n("The hotkey '%1' is already in use by the %2", conflicting.get_hotkey_string(), str(conflicting))
            f = conflicting.get_applicable_regex()
            if f is not None:
                msg += i18n(" for windows matching '%1'.", f.pattern)
            ret.append(msg)
        
        return ret
        
    # ---- Signal handlers
        
    def on_setAbbrButton_pressed(self):
        self.abbrDialog.exec_()
        
        if self.abbrDialog.result() == QDialog.Accepted:
            self.set_dirty()
            self.abbrEnabled = True
            self.abbrLabel.setText(self.abbrDialog.get_abbrs_readable())
            self.clearAbbrButton.setEnabled(True)
            
    def on_clearAbbrButton_pressed(self):
        self.set_dirty()
        self.abbrEnabled = False
        self.clearAbbrButton.setEnabled(False)
        self.abbrLabel.setText(i18n("(None configured)"))
        self.abbrDialog.reset()
        
    def on_setHotkeyButton_pressed(self):
        self.hotkeyDialog.exec_()
        
        if self.hotkeyDialog.result() == QDialog.Accepted:
            self.set_dirty()
            self.hotkeyEnabled = True
            key = self.hotkeyDialog.key
            modifiers = self.hotkeyDialog.build_modifiers()
            self.hotkeyLabel.setText(self.currentItem.get_hotkey_string(key, modifiers))
            self.clearHotkeyButton.setEnabled(True)
            
    def on_clearHotkeyButton_pressed(self):
        self.set_dirty()
        self.hotkeyEnabled = False
        self.clearHotkeyButton.setEnabled(False)
        self.hotkeyLabel.setText(i18n("(None configured)"))
        self.hotkeyDialog.reset()
        
    def on_setFilterButton_pressed(self):
        self.filterDialog.exec_()
        
        if self.filterDialog.result() == QDialog.Accepted:
            self.set_dirty()
            filterText = self.filterDialog.get_filter_text()
            if filterText != "":
                self.filterEnabled = True
                self.clearFilterButton.setEnabled(True)
                self.windowFilterLabel.setText(filterText)
            else:
                self.filterEnabled = False
                self.clearFilterButton.setEnabled(False)
                if self.currentItem.inherits_filter():
                    text = self.currentItem.parent.get_child_filter()
                else:
                    text = i18n("(None configured)")
                self.windowFilterLabel.setText(text)
                
    def on_clearFilterButton_pressed(self):
        self.set_dirty()
        self.filterEnabled = False
        self.clearFilterButton.setEnabled(False)
        if self.currentItem.inherits_filter():
            text = self.currentItem.parent.get_child_filter()
        else:
            text = i18n("(None configured)")
        self.windowFilterLabel.setText(text)
        self.filterDialog.reset()

import scriptpage

class ScriptPage(QWidget, scriptpage.Ui_ScriptPage):

    def __init__(self):
        QWidget.__init__(self)
        scriptpage.Ui_ScriptPage.__init__(self)
        self.setupUi(self)
        
        self.scriptCodeEditor.setUtf8(1)

        lex = Qsci.QsciLexerPython(self)
        api = Qsci.QsciAPIs(lex)
        api.load(API_FILE)
        api.prepare()

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
        
    def load(self, script):
        self.currentScript = script
        self.scriptCodeEditor.clear()
        self.scriptCodeEditor.append(script.code)
        self.showInTrayCheckbox.setChecked(script.showInTrayMenu)
        self.promptCheckbox.setChecked(script.prompt)
        self.settingsWidget.load(script)
        self.topLevelWidget().set_undo_available(False)
        self.topLevelWidget().set_redo_available(False)
        
        if self.is_new_item():
            self.urlLabel.setEnabled(False)
            self.urlLabel.setText(i18n("(Unsaved)"))
        else:
            set_url_label(self.urlLabel, self.currentScript.path)

    def save(self):
        self.settingsWidget.save()
        self.currentScript.code = unicode(self.scriptCodeEditor.text())
        self.currentScript.showInTrayMenu = self.showInTrayCheckbox.isChecked()
        
        self.currentScript.persist()
        set_url_label(self.urlLabel, self.currentScript.path)
        return False

    def set_item_title(self, title):
        self.currentScript.description = title
        
    def rebuild_item_path(self):
        self.currentScript.rebuild_path()
        
    def is_new_item(self):
        return self.currentScript.path is None
    
    def reset(self):
        self.load(self.currentScript)
        self.topLevelWidget().set_undo_available(False)
        self.topLevelWidget().set_redo_available(False)
    
    def set_dirty(self):
        self.topLevelWidget().set_dirty()  
        
    def start_record(self):
        self.scriptCodeEditor.append("\n")
        
    def start_key_sequence(self):
        self.scriptCodeEditor.append("keyboard.send_keys(\"")
        
    def end_key_sequence(self):
        self.scriptCodeEditor.append("\")\n")        
    
    def append_key(self, key):
        self.scriptCodeEditor.append(key)
        
    def append_hotkey(self, key, modifiers):
        keyString = self.currentScript.get_hotkey_string(key, modifiers)
        self.scriptCodeEditor.append(keyString)
        
    def append_mouseclick(self, xCoord, yCoord, button, windowTitle):
        self.scriptCodeEditor.append("mouse.click_relative(%d, %d, %d) # %s\n" % (xCoord, yCoord, int(button), windowTitle))
        
    def undo(self):
        self.scriptCodeEditor.undo()
        self.topLevelWidget().set_undo_available(self.scriptCodeEditor.isUndoAvailable())
        
    def redo(self):
        self.scriptCodeEditor.redo()
        self.topLevelWidget().set_redo_available(self.scriptCodeEditor.isRedoAvailable())
        
    def validate(self):
        errors = []
        
        # Check script code        
        code = unicode(self.scriptCodeEditor.text())
        if EMPTY_FIELD_REGEX.match(code):
            errors.append(i18n("The script code can't be empty"))
            
        # Check settings
        errors += self.settingsWidget.validate()
        
        if errors:
            msg = i18n(PROBLEM_MSG_SECONDARY, '\n'.join([str(e) for e in errors]))
            KMessageBox.detailedError(self.topLevelWidget(), PROBLEM_MSG_PRIMARY.toString(), msg)
                
        return len(errors) == 0
        
    # --- Signal handlers

    def on_scriptCodeEditor_textChanged(self):
        self.set_dirty()
        self.topLevelWidget().set_undo_available(self.scriptCodeEditor.isUndoAvailable())
        self.topLevelWidget().set_redo_available(self.scriptCodeEditor.isRedoAvailable())

    def on_promptCheckbox_stateChanged(self, state):
        self.set_dirty()

    def on_showInTrayCheckbox_stateChanged(self, state):
        self.set_dirty()
        
    def on_urlLabel_leftClickedUrl(self, url=None):
        if url: subprocess.Popen(["/usr/bin/xdg-open", url])


import phrasepage

class PhrasePage(QWidget, phrasepage.Ui_PhrasePage):

    def __init__(self):
        QWidget.__init__(self)
        phrasepage.Ui_PhrasePage.__init__(self)
        self.setupUi(self)

        self.initialising = True
        l = model.SEND_MODES.keys()
        l.sort()
        for val in l:
            self.sendModeCombo.addItem(val)
        self.initialising = False
        
    def load(self, phrase):
        self.currentPhrase = phrase
        self.phraseText.setPlainText(phrase.phrase)
        self.showInTrayCheckbox.setChecked(phrase.showInTrayMenu)

        for k, v in model.SEND_MODES.iteritems():
            if v == phrase.sendMode:
                self.sendModeCombo.setCurrentIndex(self.sendModeCombo.findText(k))
                break
                
        if self.is_new_item():
            self.urlLabel.setEnabled(False)
            self.urlLabel.setText(i18n("(Unsaved)"))
        else:
            set_url_label(self.urlLabel, self.currentPhrase.path)
        
        # TODO - re-enable me if restoring predictive functionality
        #self.predictCheckbox.setChecked(model.TriggerMode.PREDICTIVE in phrase.modes)
        
        self.promptCheckbox.setChecked(phrase.prompt)
        self.settingsWidget.load(phrase)
        
    def save(self):
        self.settingsWidget.save()
        self.currentPhrase.phrase = unicode(self.phraseText.toPlainText())
        self.currentPhrase.showInTrayMenu = self.showInTrayCheckbox.isChecked()

        self.currentPhrase.sendMode = model.SEND_MODES[str(self.sendModeCombo.currentText())]
        
        # TODO - re-enable me if restoring predictive functionality
        #if self.predictCheckbox.isChecked():
        #    self.currentPhrase.modes.append(model.TriggerMode.PREDICTIVE)
        
        self.currentPhrase.prompt = self.promptCheckbox.isChecked()
        
        self.currentPhrase.persist()
        set_url_label(self.urlLabel, self.currentPhrase.path)
        return False

    def set_item_title(self, title):
        self.currentPhrase.description = title
        
    def rebuild_item_path(self):
        self.currentPhrase.rebuild_path()
        
    def is_new_item(self):
        return self.currentPhrase.path is None
        
    def reset(self):
        self.load(self.currentPhrase)   
        
    def validate(self):        
        errors = []
        
        # Check phrase content
        phrase = unicode(self.phraseText.toPlainText())
        if EMPTY_FIELD_REGEX.match(phrase):
            errors.append(i18n("The phrase content can't be empty"))
            
        # Check settings
        errors += self.settingsWidget.validate()
        
        if errors:
            msg = i18n(PROBLEM_MSG_SECONDARY, '\n'.join([str(e) for e in errors]))
            KMessageBox.detailedError(self.topLevelWidget(), PROBLEM_MSG_PRIMARY.toString(), msg)
                
        return len(errors) == 0
        
    def set_dirty(self):
        self.topLevelWidget().set_dirty()
        
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
        self.topLevelWidget().set_undo_available(state)
        
    def on_phraseText_redoAvailable(self, state):
        self.topLevelWidget().set_redo_available(state)
    
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
        if url: subprocess.Popen(["/usr/bin/xdg-open", url])


import folderpage

class FolderPage(QWidget, folderpage.Ui_FolderPage):

    def __init__(self):
        QWidget.__init__(self)
        folderpage.Ui_FolderPage.__init__(self)
        self.setupUi(self)
        
    def load(self, folder):
        self.currentFolder = folder
        self.showInTrayCheckbox.setChecked(folder.showInTrayMenu)
        self.settingsWidget.load(folder)

        if self.is_new_item():
            self.urlLabel.setEnabled(False)
            self.urlLabel.setText(i18n("(Unsaved)"))
        else:
            set_url_label(self.urlLabel, self.currentFolder.path)
        
    def save(self):
        self.currentFolder.showInTrayMenu = self.showInTrayCheckbox.isChecked()
        self.settingsWidget.save()
        self.currentFolder.persist()
        set_url_label(self.urlLabel, self.currentFolder.path)
        
        return not self.currentFolder.path.startswith(CONFIG_DEFAULT_FOLDER)
        
    def set_item_title(self, title):
        self.currentFolder.title = title
        
    def rebuild_item_path(self):
        self.currentFolder.rebuild_path()
        
    def is_new_item(self):
        return self.currentFolder.path is None
        
    def reset(self):
        self.load(self.currentFolder)        
        
    def validate(self):
        # Check settings
        errors = self.settingsWidget.validate()
        
        if errors:
            msg = i18n(PROBLEM_MSG_SECONDARY, '\n'.join([str(e) for e in errors]))
            KMessageBox.detailedError(self.topLevelWidget(), PROBLEM_MSG_PRIMARY.toString(), msg)
                
        return len(errors) == 0
        
    def set_dirty(self):
        self.topLevelWidget().set_dirty()  
        
    # --- Signal handlers
    def on_showInTrayCheckbox_stateChanged(self, state):
        self.set_dirty()
        
    def on_urlLabel_leftClickedUrl(self, url=None):
        if url: subprocess.Popen(["/usr/bin/xdg-open", url])


class AkTreeWidget(QTreeWidget):

    def edit(self, index, trigger, event):
        if index.column() == 0:
            return QTreeWidget.edit(self, index, trigger, event)
        return False
    
    def keyPressEvent(self, event):
        if self.topLevelWidget().is_dirty() and \
            (event.matches(QKeySequence.MoveToNextLine) or event.matches(QKeySequence.MoveToPreviousLine)):
            veto = self.parentWidget().parentWidget().promptToSave()
            if not veto:
                QTreeWidget.keyPressEvent(self, event)
            else:
                event.ignore()
        else:
            QTreeWidget.keyPressEvent(self, event)        
    
    def mousePressEvent(self, event):
        if self.topLevelWidget().is_dirty():
            veto = self.parentWidget().parentWidget().promptToSave()
            if not veto:
                QTreeWidget.mousePressEvent(self, event)
                QTreeWidget.mouseReleaseEvent(self, event)
            else:
                event.ignore()
        else:
            QTreeWidget.mousePressEvent(self, event)
            
            
    def dragMoveEvent(self, event):
        target = self.itemAt(event.pos())
        if isinstance(target, FolderWidgetItem):
            QTreeWidget.dragMoveEvent(self, event)
        else:
            event.ignore()
            
    def dropEvent(self, event):
        target = self.itemAt(event.pos())
        sources = self.selectedItems()
        self.parentWidget().parentWidget().move_items(sources, target)
                

import centralwidget

class CentralWidget(QWidget, centralwidget.Ui_CentralWidget):

    def __init__(self, parent, app):
        QWidget.__init__(self, parent)
        centralwidget.Ui_CentralWidget.__init__(self)
        self.setupUi(self)

        self.set_dirty(False)
        self.configManager = app.configManager
        self.recorder = Recorder(self.scriptPage)
        
        self.cutCopiedItems = []

        [self.treeWidget.setColumnWidth(x, ConfigManager.SETTINGS[COLUMN_WIDTHS][x]) for x in range(3)]
        hView = self.treeWidget.header()
        hView.setResizeMode(QHeaderView.ResizeMode(QHeaderView.Interactive|QHeaderView.ResizeToContents))
                                
    def populate_tree(self, config):
        factory = WidgetItemFactory(config.folders)
        
        rootFolders = factory.get_root_folder_list()
        for item in rootFolders:
            self.treeWidget.addTopLevelItem(item)
        
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(0))
        self.on_treeWidget_itemSelectionChanged()

    def set_splitter(self, winSize):
        pos = ConfigManager.SETTINGS[HPANE_POSITION]
        self.splitter.setSizes([pos, winSize.width() - pos])
        
    def set_dirty(self, dirty):
        self.dirty = dirty

    def promptToSave(self):
        if ConfigManager.SETTINGS[PROMPT_TO_SAVE]:
            result = KMessageBox.questionYesNoCancel(self.topLevelWidget(),
                        i18n("There are unsaved changes. Would you like to save them?"))
        
            if result == KMessageBox.Yes:
                return self.on_save()
            elif result == KMessageBox.Cancel:
                return True
        else:
            # don't prompt, just save
            return self.on_save()
            
    # ---- Signal handlers
    
    def on_treeWidget_customContextMenuRequested(self, position):
        factory = self.topLevelWidget().guiFactory()
        menu = factory.container("Context", self.topLevelWidget())
        menu.popup(QCursor.pos())
        
    def on_treeWidget_itemChanged(self, item, column):
        if item is self.treeWidget.selectedItems()[0] and column == 0:
            newText = unicode(item.text(0))
            if validate(not EMPTY_FIELD_REGEX.match(newText), i18n("The name can't be empty."),
                        None, self.topLevelWidget()):

                self.parentWidget().app.monitor.suspend()
                self.stack.currentWidget().set_item_title(newText)
                self.stack.currentWidget().rebuild_item_path()

                persistGlobal = self.stack.currentWidget().save()
                self.parentWidget().app.monitor.unsuspend()
                self.parentWidget().app.config_altered(persistGlobal)

                self.treeWidget.sortItems(0, Qt.AscendingOrder)
            else:
                item.update()
        
    def on_treeWidget_itemSelectionChanged(self):
        modelItems = self.__getSelection()
        
        if len(modelItems) == 1:
            modelItem = modelItems[0]
            if isinstance(modelItem, model.Folder):
                self.stack.setCurrentIndex(0)
                self.folderPage.load(modelItem)
                
            elif isinstance(modelItem, model.Phrase):
                self.stack.setCurrentIndex(1)
                self.phrasePage.load(modelItem)
                
            elif isinstance(modelItem, model.Script):
                self.stack.setCurrentIndex(2)
                self.scriptPage.load(modelItem)
                
            self.topLevelWidget().update_actions(modelItems, True)
            self.set_dirty(False)
            self.parentWidget().cancel_record()
            
        else:
            self.topLevelWidget().update_actions(modelItems, False)
        
    def on_new_topfolder(self):
        result = KMessageBox.questionYesNoCancel(self.topLevelWidget(),
                    i18n("Create folder in the default location?"),
                    "Create Folder", KStandardGuiItem.yes(),
                    KGuiItem(i18n("Create Elsewhere")))
        
        self.topLevelWidget().app.monitor.suspend()

        if result == KMessageBox.Yes:
            self.__createFolder(None)

        elif result != KMessageBox.Cancel:
            path = KFileDialog.getExistingDirectory(KUrl(), self.topLevelWidget())

            if path != "":
                path = unicode(path)
                name = os.path.basename(path)
                folder = model.Folder(name, path=path)
                newItem = FolderWidgetItem(None, folder)
                self.treeWidget.addTopLevelItem(newItem)
                self.configManager.folders.append(folder)
                self.topLevelWidget().app.config_altered(True)

            self.topLevelWidget().app.monitor.unsuspend()
        else:
            self.topLevelWidget().app.monitor.unsuspend()

    
    def on_new_folder(self):
        parentItem = self.treeWidget.selectedItems()[0]
        self.__createFolder(parentItem)

    def __createFolder(self, parentItem):
        folder = model.Folder("New Folder")
        newItem = FolderWidgetItem(parentItem, folder)
        self.topLevelWidget().app.monitor.suspend()

        if parentItem is not None:
            parentFolder = self.__extractData(parentItem)
            parentFolder.add_folder(folder)
        else:
            self.treeWidget.addTopLevelItem(newItem)
            self.configManager.folders.append(folder)
        
        folder.persist()
        self.topLevelWidget().app.monitor.unsuspend()

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()
        
    def on_new_phrase(self):
        self.topLevelWidget().app.monitor.suspend()
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)
        
        phrase = model.Phrase("New Phrase", "Enter phrase contents")
        newItem = PhraseWidgetItem(parentItem, phrase)
        parent.add_item(phrase)
        phrase.persist()

        self.topLevelWidget().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.treeWidget.setItemSelected(parentItem, False)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()      
        
    def on_new_script(self):
        self.topLevelWidget().app.monitor.suspend()
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)
        
        script = model.Script("New Script", "#Enter script code")
        newItem = ScriptWidgetItem(parentItem, script)
        parent.add_item(script)
        script.persist()

        self.topLevelWidget().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.treeWidget.setItemSelected(parentItem, False)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()  
        
    def on_undo(self):
        self.stack.currentWidget().undo()

    def on_redo(self):
        self.stack.currentWidget().redo()
        
    def on_copy(self):
        sourceObjects = self.__getSelection()
        
        for source in sourceObjects:        
            if isinstance(source, model.Phrase):
                newObj = model.Phrase('', '')
            else:
                newObj = model.Script('', '')
            newObj.copy(source)
            self.cutCopiedItems.append(newObj)

    def on_clone(self):
        sourceObject = self.__getSelection()[0]
        parentItem = self.treeWidget.selectedItems()[0].parent()
        parent = self.__extractData(parentItem)

        if isinstance(sourceObject, model.Phrase):
            newObj = model.Phrase('', '')
            newObj.copy(sourceObject)
            newItem = PhraseWidgetItem(parentItem, newObj)
        else:
            newObj = model.Script('', '')
            newObj.copy(sourceObject)
            newItem = ScriptWidgetItem(parentItem, newObj)

        parent.add_item(newObj)
        self.topLevelWidget().app.monitor.suspend()
        newObj.persist()
        
        self.topLevelWidget().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.treeWidget.setItemSelected(parentItem, False)
        self.on_treeWidget_itemSelectionChanged()
        self.parentWidget().app.config_altered(False)

    def on_cut(self):
        self.cutCopiedItems = self.__getSelection()
        self.topLevelWidget().app.monitor.suspend()
        
        sourceItems = self.treeWidget.selectedItems()
        result = filter(lambda f: f.parent() not in sourceItems, sourceItems)
        for item in result:
            self.__removeItem(item)

        self.topLevelWidget().app.monitor.unsuspend()
        self.parentWidget().app.config_altered(False)
        
    def on_paste(self):
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)
        self.topLevelWidget().app.monitor.suspend()
        
        newItems = []
        for item in self.cutCopiedItems:
            if isinstance(item, model.Folder):
                f = WidgetItemFactory(None)
                newItem = FolderWidgetItem(parentItem, item)
                f.processFolder(newItem, item)
                parent.add_folder(item)
            elif isinstance(item, model.Phrase):
                newItem = PhraseWidgetItem(parentItem, item)
                parent.add_item(item)
            else:
                newItem = ScriptWidgetItem(parentItem, item)
                parent.add_item(item)

            item.persist()
                
            newItems.append(newItem)

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItems[-1])
        self.on_treeWidget_itemSelectionChanged()
        self.cutCopiedItems = []
        for item in newItems:
            self.treeWidget.setItemSelected(item, True)
        self.topLevelWidget().app.monitor.unsuspend()
        self.parentWidget().app.config_altered(False)

    def on_delete(self):
        widgetItems = self.treeWidget.selectedItems()
        self.topLevelWidget().app.monitor.suspend()

        if len(widgetItems) == 1:
            widgetItem = widgetItems[0]
            data = self.__extractData(widgetItem)
            if isinstance(data, model.Folder):
                msg = i18n("Are you sure you want to delete the '%1' folder and all the items in it?", data.title)
            else:
                msg = i18n("Are you sure you want to delete '%1'?", data.description)
        else:
            msg = i18n("Are you sure you want to delete the %1 selected folders/items?", str(len(widgetItems)))

        result = KMessageBox.questionYesNo(self.topLevelWidget(), msg)

        if result == KMessageBox.Yes:
            for widgetItem in widgetItems:
                self.__removeItem(widgetItem)

        self.topLevelWidget().app.monitor.unsuspend()
        if result == KMessageBox.Yes:
            self.parentWidget().app.config_altered(False)
            
    def on_rename(self):
        widgetItem = self.treeWidget.selectedItems()[0]
        self.treeWidget.editItem(widgetItem, 0)
        
    def on_save(self):
        if self.stack.currentWidget().validate():
            self.parentWidget().app.monitor.suspend()
            persistGlobal = self.stack.currentWidget().save()
            self.topLevelWidget().save_completed(persistGlobal)
            self.set_dirty(False)
            
            item = self.treeWidget.selectedItems()[0]
            item.update()
            self.treeWidget.update()
            self.treeWidget.sortItems(0, Qt.AscendingOrder)
            self.parentWidget().app.monitor.unsuspend()
            return False

        return True
        
    def on_reset(self):
        self.stack.currentWidget().reset()
        self.set_dirty(False)
        self.parentWidget().cancel_record()
        
    def move_items(self, sourceItems, target):
        targetModelItem = self.__extractData(target)
        
        # Filter out any child objects that belong to a parent already in the list
        result = filter(lambda f: f.parent() not in sourceItems, sourceItems)
        
        self.parentWidget().app.monitor.suspend()
        
        for source in result:
            self.__removeItem(source)
            sourceModelItem = self.__extractData(source)
            
            if isinstance(sourceModelItem, model.Folder):
                targetModelItem.add_folder(sourceModelItem)
                self.__moveRecurseUpdate(sourceModelItem)
            else:
                targetModelItem.add_item(sourceModelItem)
                sourceModelItem.path = None
                sourceModelItem.persist()
                
            target.addChild(source)
        
        self.parentWidget().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.parentWidget().app.config_altered(True)  
        
    def __moveRecurseUpdate(self, folder):
        folder.path = None
        folder.persist()
        
        for subfolder in folder.folders:
            self.__moveRecurseUpdate(subfolder)
        
        for child in folder.items:
            child.path = None
            child.persist()
        
    # ---- Private methods

    def get_selected_item(self):
        return self.__getSelection()
    
    def __getSelection(self):
        items = self.treeWidget.selectedItems()
        ret = []
        for item in items:
            ret.append(self.__extractData(item))
            
        # Filter out any child objects that belong to a parent already in the list
        result = filter(lambda f: f.parent not in ret, ret)
        return result
        
    def __extractData(self, item):
        variant = item.data(3, Qt.UserRole)
        return variant.toPyObject()
        
    def __removeItem(self, widgetItem):
        parent = widgetItem.parent()
        item = self.__extractData(widgetItem)
        self.__deleteHotkeys(item)
        
        if parent is None:
            removedIndex = self.treeWidget.indexOfTopLevelItem(widgetItem)
            self.treeWidget.takeTopLevelItem(removedIndex)
            self.configManager.folders.remove(item)
        else:
            removedIndex = parent.indexOfChild(widgetItem)
            parent.removeChild(widgetItem)
        
            if isinstance(item, model.Folder):
                item.parent.remove_folder(item)
            else:
                item.parent.remove_item(item)
        
        item.remove_data()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)

        if parent is not None:
            if parent.childCount() > 0:
                newIndex = min([removedIndex, parent.childCount() - 1])
                self.treeWidget.setCurrentItem(parent.child(newIndex))
            else:
                self.treeWidget.setCurrentItem(parent)
        else:
            newIndex = min([removedIndex, self.treeWidget.topLevelItemCount() - 1])
            self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(newIndex))
            
    def __deleteHotkeys(self, theItem):
        if model.TriggerMode.HOTKEY in theItem.modes:
            self.topLevelWidget().app.hotkey_removed(theItem)

        if isinstance(theItem, model.Folder):
            for subFolder in theItem.folders:
                self.__deleteHotkeys(subFolder)

            for item in theItem.items:
                if model.TriggerMode.HOTKEY in item.modes:
                    self.topLevelWidget().app.hotkey_removed(item)
        
        

# ---- Configuration window
    
class ConfigWindow(KXmlGuiWindow):

    def __init__(self, app):
        KXmlGuiWindow.__init__(self)
        self.centralWidget = CentralWidget(self, app)
        self.setCentralWidget(self.centralWidget)
        self.app = app
        
        # File Menu
        self.create = self.__createMenuAction("create", i18n("New"), iconName="document-new")
        self.create.setDelayed(False)
        
        self.newTopFolder = self.__createAction("new-top-folder", i18n("Folder"), "folder-new", self.centralWidget.on_new_topfolder)
        self.newFolder = self.__createAction("new-folder", i18n("Sub-folder"), "folder-new", self.centralWidget.on_new_folder)
        self.newPhrase = self.__createAction("new-phrase", i18n("Phrase"), "text-x-generic", self.centralWidget.on_new_phrase, KStandardShortcut.New)
        self.newScript = self.__createAction("new-script", i18n("Script"), "text-x-python", self.centralWidget.on_new_script)
        self.newScript.setShortcut(QKeySequence("Ctrl+Shift+n"))
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
        #self.cut.setShortcut(QKeySequence("Ctrl+Shift+x"))
        #self.copy.setShortcut(QKeySequence("Ctrl+Shift+c"))
        self.clone.setShortcut(QKeySequence("Ctrl+Shift+c"))
        
        self.undo = self.__createAction("undo", i18n("Undo"), "edit-undo", self.centralWidget.on_undo, KStandardShortcut.Undo)
        self.redo = self.__createAction("redo", i18n("Redo"), "edit-redo", self.centralWidget.on_redo, KStandardShortcut.Redo)
        
        rename = self.__createAction("rename", i18n("Rename"), None, self.centralWidget.on_rename)
        rename.setShortcut(QKeySequence("f2"))
        
        self.delete = self.__createAction("delete-item", i18n("Delete"), "edit-delete", self.centralWidget.on_delete)
        self.delete.setShortcut(QKeySequence("Ctrl+d"))
        self.record = self.__createToggleAction("record", i18n("Record Script"), self.on_record, "media-record")
        self.run = self.__createAction("run", i18n("Run Script"), "media-playback-start", self.on_run_script)
        self.run.setShortcut(QKeySequence("f8"))
        self.insertMacro = self.__createMenuAction("insert-macro", i18n("Insert Macro"), None, None)
        menu = app.service.phraseRunner.macroManager.get_menu(self.on_insert_macro, self.insertMacro.menu())
        #self.insertMacro.setMenu(menu)
        #print menu
        
        # Settings Menu
        self.enable = self.__createToggleAction("enable-monitoring", i18n("Enable Monitoring"), self.on_enable_toggled)
        self.advancedSettings = self.__createAction("advanced-settings", i18n("Configure AutoKey"), "configure", self.on_advanced_settings)
        self.__createAction("script-error", i18n("View script error"), "dialog-error", self.on_show_error)
        
        # Help Menu
        self.__createAction("online-help", i18n("Online Manual"), "help-contents", self.on_show_help)
        self.__createAction("online-faq", i18n("F.A.Q."), "help-faq", self.on_show_faq)
        self.__createAction("donate", i18n("Donate"), "face-smile", self.on_donate)
        self.__createAction("report-bug", i18n("Report a Bug"), "tools-report-bug", self.on_report_bug)
        self.__createAction("about", i18n("About AutoKey"), "help-about", self.on_about)

        self.setHelpMenuEnabled(False)

        options = KXmlGuiWindow.Default ^ KXmlGuiWindow.StandardWindowOptions(KXmlGuiWindow.StatusBar)
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

    def save_completed(self, persistGlobal):
        self.save.setEnabled(False)
        self.app.config_altered(persistGlobal)
        
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
        ConfigManager.SETTINGS[HPANE_POSITION] = self.centralWidget.splitter.sizes()[0] + 4
        l = []
        for x in xrange(3):
            l.append(self.centralWidget.treeWidget.columnWidth(x))
        ConfigManager.SETTINGS[COLUMN_WIDTHS] = l
        
        if self.is_dirty():
            if self.centralWidget.promptToSave():
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
        self.centralWidget.phrasePage.insert_token(token)
            
    def on_record(self):
        if self.record.isChecked():
            dlg = RecordDialog(self, self.__doRecord)
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
        script = self.centralWidget.get_selected_item()[0]
        time.sleep(2)
        self.app.service.scriptRunner.run_subscript(script)
    
    # Settings Menu
        
    def on_enable_toggled(self):
        if self.enable.isChecked():
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_advanced_settings(self):
        s = SettingsDialog(self)
        s.show()
        
    def on_show_error(self):
        self.app.show_script_error()
            
    # Help Menu
            
    def on_show_faq(self):
        webbrowser.open(common.FAQ_URL, False, True)
        
    def on_show_help(self):
        webbrowser.open(common.HELP_URL, False, True)
        
    def on_donate(self):
        webbrowser.open(common.DONATE_URL, False, True)

    def on_report_bug(self):
        webbrowser.open(common.BUG_URL, False, True)

    def on_about(self):
        dlg = KAboutApplicationDialog(self.app.aboutData, self)
        dlg.show()

# ---- TreeWidget and helper functions

class WidgetItemFactory:
    
    def __init__(self, rootFolders):
        self.folders = rootFolders
    
    def get_root_folder_list(self):
        rootItems = []
        
        for folder in self.folders:
            item = self.__buildItem(None, folder)
            rootItems.append(item)
            self.processFolder(item, folder)
            
        return rootItems
        
    def processFolder(self, parentItem, parentFolder):
        for folder in parentFolder.folders:
            item = self.__buildItem(parentItem, folder)
            self.processFolder(item, folder)
        
        for childModelItem in parentFolder.items:
            self.__buildItem(parentItem, childModelItem)
    
    def __buildItem(self, parent, item):
        if isinstance(item, model.Folder):
            return FolderWidgetItem(parent, item)
        elif isinstance(item, model.Phrase):
            return PhraseWidgetItem(parent, item)
        elif isinstance(item, model.Script):
            return ScriptWidgetItem(parent, item)


class FolderWidgetItem(QTreeWidgetItem):
    
    def __init__(self, parent, folder):
        QTreeWidgetItem.__init__(self)
        self.folder = folder
        self.setIcon(0, KIcon("folder"))
        self.setText(0, folder.title)
        self.setText(1, folder.get_abbreviations())
        self.setText(2, folder.get_hotkey_string())
        self.setData(3, Qt.UserRole, QVariant(folder))
        if parent is not None:
            parent.addChild(self)
            
        self.setFlags(self.flags() | Qt.ItemIsEditable)
            
    def update(self):
        self.setText(0, self.folder.title)
        self.setText(1, self.folder.get_abbreviations())
        self.setText(2, self.folder.get_hotkey_string())        
        
    def __ge__(self, other):
        if isinstance(other, ScriptWidgetItem):
            return QTreeWidgetItem.__ge__(self, other)
        else:
            return False
            
    def __lt__(self, other):
        if isinstance(other, FolderWidgetItem):
            return QTreeWidgetItem.__lt__(self, other)
        else:
            return True
            

class PhraseWidgetItem(QTreeWidgetItem):
    
    def __init__(self, parent, phrase):
        QTreeWidgetItem.__init__(self)
        self.phrase = phrase
        self.setIcon(0, KIcon("text-x-generic"))
        self.setText(0, phrase.description)
        self.setText(1, phrase.get_abbreviations())
        self.setText(2, phrase.get_hotkey_string())
        self.setData(3, Qt.UserRole, QVariant(phrase))
        if parent is not None:
            parent.addChild(self)      
            
        self.setFlags(self.flags() | Qt.ItemIsEditable)
            
    def update(self):
        self.setText(0, self.phrase.description)
        self.setText(1, self.phrase.get_abbreviations())
        self.setText(2, self.phrase.get_hotkey_string())
        
    def __ge__(self, other):
        if isinstance(other, ScriptWidgetItem):
            return QTreeWidgetItem.__ge__(self, other)
        else:
            return True
            
    def __lt__(self, other):
        if isinstance(other, PhraseWidgetItem):
            return QTreeWidgetItem.__lt__(self, other)
        else:
            return False
            

class ScriptWidgetItem(QTreeWidgetItem):
    
    def __init__(self, parent, script):
        QTreeWidgetItem.__init__(self)
        self.script = script
        self.setIcon(0, KIcon("text-x-python"))
        self.setText(0, script.description)
        self.setText(1, script.get_abbreviations())
        self.setText(2, script.get_hotkey_string())
        self.setData(3, Qt.UserRole, QVariant(script))
        if parent is not None:
            parent.addChild(self)
            
        self.setFlags(self.flags() | Qt.ItemIsEditable)
            
    def update(self):
        self.setText(0, self.script.description)
        self.setText(1, self.script.get_abbreviations())
        self.setText(2, self.script.get_hotkey_string())
        
    def __ge__(self, other):
        if isinstance(other, ScriptWidgetItem):
            return QTreeWidgetItem.__ge__(self, other)
        else:
            return True
            
    def __lt__(self, other):
        if isinstance(other, ScriptWidgetItem):
            return QTreeWidgetItem.__lt__(self, other)
        else:
            return False
