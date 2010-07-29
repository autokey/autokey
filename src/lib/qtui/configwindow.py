# -*- coding: utf-8 -*-

# Copyright (C) 2009 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import logging, sys, os, webbrowser
from PyKDE4.kio import *
from PyKDE4.kdeui import *
from PyKDE4.kdecore import i18n
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

_logger = logging.getLogger("configwindow")

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
            self.abbrLabel.setText(item.abbreviation)
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
        if item.uses_default_filter():
            self.windowFilterLabel.setText(i18n("(None configured)"))
            self.clearFilterButton.setEnabled(False)
            self.filterEnabled = False
        else:
            self.windowFilterLabel.setText(item.get_filter_regex())   
            self.clearFilterButton.setEnabled(True)
            self.filterEnabled = True
            
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
        
    # ---- Signal handlers
        
    def on_setAbbrButton_pressed(self):
        self.abbrDialog.exec_()
        
        if self.abbrDialog.result() == QDialog.Accepted:
            self.set_dirty()
            self.abbrEnabled = True
            self.abbrLabel.setText(self.abbrDialog.get_abbr())
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
                self.windowFilterLabel.setText(i18n("(None configured)"))

    def on_clearFilterButton_pressed(self):
        self.set_dirty()
        self.filterEnabled = False
        self.clearFilterButton.setEnabled(False)
        self.windowFilterLabel.setText(i18n("(None configured)"))
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
        self.scriptCodeEditor.setAutoCompletionThreshold(2)
        self.scriptCodeEditor.setAutoCompletionSource(Qsci.QsciScintilla.AcsAll)
        self.scriptCodeEditor.setCallTipsStyle(Qsci.QsciScintilla.CallTipsNone) # TODO disabled due to crashing!
        
    def load(self, script):
        self.currentScript = script
        self.scriptCodeEditor.clear()
        self.scriptCodeEditor.append(script.code)
        self.showInTrayCheckbox.setChecked(script.showInTrayMenu)
        self.promptCheckbox.setChecked(script.prompt)
        self.settingsWidget.load(script)
        self.topLevelWidget().set_undo_available(False)
        self.topLevelWidget().set_redo_available(False)

    def save(self):
        self.settingsWidget.save()
        self.currentScript.code = unicode(self.scriptCodeEditor.text())
        self.currentScript.showInTrayMenu = self.showInTrayCheckbox.isChecked()

    def set_item_title(self, title):
        self.currentScript.description = title
    
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
        code = unicode(self.scriptCodeEditor.text())
        if not validate(not EMPTY_FIELD_REGEX.match(code), i18n("The script code can't be empty."),
                    self.scriptCodeEditor, self.topLevelWidget()): return False
                    
        return True
        
    # --- Signal handlers

    def on_scriptCodeEditor_textChanged(self):
        self.set_dirty()
        self.topLevelWidget().set_undo_available(self.scriptCodeEditor.isUndoAvailable())
        self.topLevelWidget().set_redo_available(self.scriptCodeEditor.isRedoAvailable())

    def on_promptCheckbox_stateChanged(self, state):
        self.set_dirty()

    def on_showInTrayCheckbox_stateChanged(self, state):
        self.set_dirty()        


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

    def set_item_title(self, title):
        self.currentPhrase.description = title
        
    def reset(self):
        self.load(self.currentPhrase)   
        
    def validate(self):                
        phrase = unicode(self.phraseText.toPlainText())
        if not validate(not EMPTY_FIELD_REGEX.match(phrase), i18n("The phrase content can't be empty."),
                    self.phraseText, self.topLevelWidget()): return False

        return True
        
    def set_dirty(self):
        self.topLevelWidget().set_dirty()
        
    def undo(self):
        self.phraseText.undo()
        
    def redo(self):
        self.phraseText.redo()
        
    """def insert_token(self, token):
        self.phraseText.insertPlainText(token)"""
        
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
        
    def save(self):
        self.currentFolder.showInTrayMenu = self.showInTrayCheckbox.isChecked()
        self.settingsWidget.save()
        
    def set_item_title(self, title):
        self.currentFolder.title = title
        
    def reset(self):
        self.load(self.currentFolder)        
        
    def validate(self):
        return True
        
    def set_dirty(self):
        self.topLevelWidget().set_dirty()  
        
    # --- Signal handlers
    def on_showInTrayCheckbox_stateChanged(self, state):
        self.set_dirty()


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
        self.saveButton = self.buttonBox.addButton(KStandardGuiItem.save(),
                        QDialogButtonBox.ButtonRole(QDialogButtonBox.NoRole), self.on_save)
        self.resetButton = self.buttonBox.addButton(KStandardGuiItem.reset(), 
                        QDialogButtonBox.ButtonRole(QDialogButtonBox.NoRole), self.on_reset)
                        
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
        self.saveButton.setEnabled(dirty)
        self.resetButton.setEnabled(dirty)
        
    def promptToSave(self):
        if ConfigManager.SETTINGS[PROMPT_TO_SAVE]:
            result = KMessageBox.questionYesNoCancel(self.topLevelWidget(),
                        i18n("There are unsaved changes. Would you like to save them?"))
        
            if result == KMessageBox.Yes:
                self.on_save()
            elif result == KMessageBox.Cancel:
                return True
        else:
            # don't prompt, just save
            self.on_save()
            
        return False
        
    # ---- Signal handlers
    
    def on_treeWidget_customContextMenuRequested(self, position):
        factory = self.topLevelWidget().guiFactory()
        menu = factory.container("Context", self.topLevelWidget())
        menu.popup(QCursor.pos())
        
    def on_treeWidget_itemChanged(self, item, column):
        if item is self.treeWidget.selectedItems()[0]:
            newText = unicode(item.text(0))
            if validate(not EMPTY_FIELD_REGEX.match(newText), i18n("The name can't be empty."),
                        None, self.topLevelWidget()):   
        
                self.stack.currentWidget().set_item_title(newText)
                self.parentWidget().app.config_altered()
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
        self.__createFolder(None)
        
    def on_new_folder(self):
        parent = self.treeWidget.selectedItems()[0]
        self.__createFolder(parent)
        
    def on_new_phrase(self):
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)
        
        phrase = model.Phrase("New Phrase", "Enter phrase contents")
        newItem = PhraseWidgetItem(parentItem, phrase)
        parent.add_item(phrase)
        
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.treeWidget.setItemSelected(parentItem, False)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()      
        
    def on_new_script(self):
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)
        
        script = model.Script("New Script", "#Enter script code")
        newItem = ScriptWidgetItem(parentItem, script)
        parent.add_item(script)
        
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.treeWidget.setItemSelected(parentItem, False)
        self.on_treeWidget_itemSelectionChanged()     
        self.on_rename()  
        
    def on_import(self):
        paths = KFileDialog.getOpenFileNames()
        
        if paths:
            parentItem = self.treeWidget.selectedItems()[0]
            parentFolder = self.__extractData(parentItem)
            newItems = []
            imported = False
            
            for path in paths:
                try:
                    items = load_items(path, self.configManager)

                    for item in items:
                        if isinstance(item, model.Folder):
                            f = WidgetItemFactory(None)
                            newItem = FolderWidgetItem(parentItem, item)
                            f.processFolder(newItem, item)
                            parentFolder.add_folder(item)
                        elif isinstance(item, model.Phrase):
                            newItem = PhraseWidgetItem(parentItem, item)
                            parentFolder.add_item(item)
                        else:
                            newItem = ScriptWidgetItem(parentItem, item)
                            parentFolder.add_item(item)
                            
                        newItems.append(newItem)    
                        
                    imported = True
                    
                except Exception, e:
                    _logger.exception("Error while importing data from %s", path)
                    KMessageBox.error(self.topLevelWidget(), i18n("Error while importing data from %s.\n%s", path, str(e)))
                        
            if imported:
                self.treeWidget.sortItems(0, Qt.AscendingOrder)
                self.treeWidget.setCurrentItem(newItems[-1])
                self.on_treeWidget_itemSelectionChanged()
                for item in newItems:
                    self.treeWidget.setItemSelected(item, True)
                self.parentWidget().app.config_altered()                        
                KMessageBox.information(self.topLevelWidget(), i18n("The files were imported successfully."), i18n("Import"))
            
        
        
    def on_export(self):
        path = KFileDialog.getSaveFileName()
        
        if path:
            sourceObjects = self.__getSelection()
            
            try:
                export_items(sourceObjects, path)
                KMessageBox.information(self.topLevelWidget(), i18n("The items were exported successfully."), i18n("Export"))
            except Exception, e:
                _logger.exception("Error while exporting data.")            
                KMessageBox.error(self.topLevelWidget(), i18n("Error while exporting data:\n%s", str(e)))
        
    def on_undo(self):
        self.stack.currentWidget().undo()

    def on_redo(self):
        self.stack.currentWidget().redo()
        
    def on_convert(self):
        """
        @deprecated
        """
        sourceItem = self.treeWidget.selectedItems()[0]
        parentItem = sourceItem.parent()
        source = self.__getSelection()
        self.__removeItem()
        
        # Replace \n and quotes
        string = source.phrase.replace('\n', "<enter>")
        string = string.replace('"', '\\"')
        
        code = "keyboard.send_keys(\"%s\")" % string
        script = model.Script(source.description, code)
        newItem = ScriptWidgetItem(parentItem, script)
        source.parent.add_item(script)
        
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.on_treeWidget_itemSelectionChanged()        
        self.parentWidget().app.config_altered()
        
    def on_copy(self):
        sourceObjects = self.__getSelection()
        
        for source in sourceObjects:        
            if isinstance(source, model.Phrase):
                newObj = model.Phrase('', '')
            else:
                newObj = model.Script('', '')
            newObj.copy(source)
            self.cutCopiedItems.append(newObj)
        
    def on_cut(self):
        self.cutCopiedItems = self.__getSelection()
        
        sourceItems = self.treeWidget.selectedItems()
        result = filter(lambda f: f.parent() not in sourceItems, sourceItems)
        for item in result:
            self.__removeItem(item)
        self.parentWidget().app.config_altered()
        
    def on_paste(self):
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)
        
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
                
            newItems.append(newItem)        

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItems[-1])
        self.on_treeWidget_itemSelectionChanged()
        self.cutCopiedItems = []
        for item in newItems:
            self.treeWidget.setItemSelected(item, True)
        self.parentWidget().app.config_altered()

    def on_delete(self):
        widgetItems = self.treeWidget.selectedItems()
        modified = False
        
        for widgetItem in widgetItems:
            data = self.__extractData(widgetItem)
            if isinstance(data, model.Folder):
                msg = "Are you sure you want to delete the '%s' folder and all the items in it?" % data.title
            else:
                msg = "Are you sure you want to delete '%s'?" % data.description
                
            result = KMessageBox.questionYesNo(self.topLevelWidget(), msg)
            if result == KMessageBox.Yes:
                self.__removeItem(widgetItem)
                modified = True

        if modified:
            self.parentWidget().app.config_altered()
            
    def on_rename(self):
        widgetItem = self.treeWidget.selectedItems()[0]
        self.treeWidget.editItem(widgetItem, 0)
        
    def on_save(self):
        if self.stack.currentWidget().validate():
            self.stack.currentWidget().save()
            self.topLevelWidget().save_completed()
            self.set_dirty(False)
            
            item = self.treeWidget.selectedItems()[0]
            item.update()
            self.treeWidget.update()
            self.treeWidget.sortItems(0, Qt.AscendingOrder)
        
    def on_reset(self):
        self.stack.currentWidget().reset()
        self.set_dirty(False)
        self.parentWidget().cancel_record()
        
    def move_items(self, sourceItems, target):
        targetModelItem = self.__extractData(target)
        
        # Filter out any child objects that belong to a parent already in the list
        result = filter(lambda f: f.parent() not in sourceItems, sourceItems)
        
        for source in result:
            self.__removeItem(source)
            sourceModelItem = self.__extractData(source)
            
            if isinstance(sourceModelItem, model.Folder):
                targetModelItem.add_folder(sourceModelItem)
            else:
                targetModelItem.add_item(sourceModelItem)
                
            target.addChild(source)
            
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.parentWidget().app.config_altered()  
        
        
    # ---- Private methods
    
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
        
    def __createFolder(self, parentItem):
        folder = model.Folder("New Folder")
        newItem = FolderWidgetItem(parentItem, folder)        
                
        if parentItem is not None:
            parentFolder = self.__extractData(parentItem)
            parentFolder.add_folder(folder)
        else:
            self.treeWidget.addTopLevelItem(newItem)
            self.configManager.folders[folder.title] = folder
            
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()
        
    def __removeItem(self, widgetItem):
        parent = widgetItem.parent()
        item = self.__extractData(widgetItem)
        self.__deleteHotkeys(item)
        
        if parent is None:
            removedIndex = self.treeWidget.indexOfTopLevelItem(widgetItem)
            self.treeWidget.takeTopLevelItem(removedIndex)
            del self.configManager.folders[item.title]
        else:
            removedIndex = parent.indexOfChild(widgetItem)
            parent.removeChild(widgetItem)
        
            if isinstance(item, model.Folder):
                item.parent.remove_folder(item)
            else:
                item.parent.remove_item(item)
        
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
        self.create = self.__createMenuAction("create", i18n("Create"))
        self.create.setDelayed(False)
        
        self.newTopFolder = self.__createAction("new-top-folder", i18n("New Top-level Folder"), "folder-new", self.centralWidget.on_new_topfolder)
        self.newFolder = self.__createAction("new-folder", i18n("New Folder"), "folder-new", self.centralWidget.on_new_folder)
        self.newPhrase = self.__createAction("new-phrase", i18n("New Phrase"), "document-new", self.centralWidget.on_new_phrase, KStandardShortcut.New)
        self.newScript = self.__createAction("new-script", i18n("New Script"), "document-new", self.centralWidget.on_new_script)
        self.newScript.setShortcut(QKeySequence("Ctrl+Shift+n"))
        self.save = self.__createAction("save", i18n("Save"), "document-save", self.centralWidget.on_save, KStandardShortcut.Save)
        
        self.importAction = self.__createAction("import", i18n("Import"), None, self.centralWidget.on_import)
        self.exportAction = self.__createAction("export", i18n("Export"), None, self.centralWidget.on_export)
        
        self.create.addAction(self.newTopFolder)
        self.create.addAction(self.newFolder)
        self.create.addAction(self.newPhrase)
        self.create.addAction(self.newScript)

        #self.importSettings = self.__createAction("import", i18n("Import Settings"), target=self.new_folder)

        self.close = self.__createAction("close-window", i18n("Close Window"), "window-close", self.on_close, KStandardShortcut.Close)
        KStandardAction.quit(self.on_quit, self.actionCollection())

        # Edit Menu 
        self.cut = self.__createAction("cut-item", i18n("Cut Item"), "edit-cut", self.centralWidget.on_cut)
        self.copy = self.__createAction("copy-item", i18n("Copy Item"), "edit-copy", self.centralWidget.on_copy)
        self.paste = self.__createAction("paste-item", i18n("Paste Item"), "edit-paste", self.centralWidget.on_paste)
        self.cut.setShortcut(QKeySequence("Ctrl+Shift+x"))
        self.copy.setShortcut(QKeySequence("Ctrl+Shift+c"))
        self.paste.setShortcut(QKeySequence("Ctrl+Shift+v"))
        
        self.undo = self.__createAction("undo", i18n("Undo"), "edit-undo", self.centralWidget.on_undo, KStandardShortcut.Undo)
        self.redo = self.__createAction("redo", i18n("Redo"), "edit-redo", self.centralWidget.on_redo, KStandardShortcut.Redo)
        
        self.__createAction("rename", i18n("Rename"), None, self.centralWidget.on_rename)        
        
        #self.convert = self.__createAction("convert", i18n("Convert to Script"), None, self.centralWidget.on_convert)
        self.delete = self.__createAction("delete-item", i18n("Delete"), "edit-delete", self.centralWidget.on_delete)
        self.delete.setShortcut(QKeySequence("Ctrl+d"))
        self.record = self.__createToggleAction("record", i18n("Record Macro"), self.on_record, "media-record")
        
        # Settings Menu
        self.enable = self.__createToggleAction("enable-monitoring", i18n("Enable Monitoring"), self.on_enable_toggled)
        self.advancedSettings = self.__createAction("advanced-settings", i18n("Configure AutoKey"), "configure", self.on_advanced_settings)
        self.__createAction("script-error", i18n("View script error"), "dialog-error", self.on_show_error)
        
        # Help Menu
        self.__createAction("online-help", i18n("Online Manual"), "help-contents", self.on_show_help)
        self.__createAction("online-faq", i18n("F.A.Q."), "help-faq", self.on_show_faq)
        self.__createAction("donate", i18n("Donate"), "face-smile", self.on_donate)
        self.__createAction("about", i18n("About AutoKey"), "help-about", self.on_about)

        self.setHelpMenuEnabled(False)

        options = KXmlGuiWindow.Default ^ KXmlGuiWindow.StandardWindowOptions(KXmlGuiWindow.StatusBar)
        self.setupGUI(options, ACTION_DESCRIPTION_FILE)

        #self.setCaption(CONFIG_WINDOW_TITLE)
        
        # Initialise action states
        self.enable.setChecked(self.app.service.is_running())
        self.undo.setEnabled(False)
        self.redo.setEnabled(False)
        
        self.centralWidget.populate_tree(self.app.configManager)
        self.centralWidget.set_splitter(self.size())
        
        self.setAutoSaveSettings()
        
    def set_dirty(self):
        self.centralWidget.set_dirty(True)
        self.save.setEnabled(True)
        
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
            
            self.importAction.setEnabled(canCreate)
            self.exportAction.setEnabled(True)
            
            self.copy.setEnabled(canCopy)
            self.paste.setEnabled(canCreate and len(self.centralWidget.cutCopiedItems) > 0)
            #self.convert.setEnabled(isinstance(item, model.Phrase))
            self.record.setEnabled(isinstance(items[0], model.Script) and len(items) == 1)

            if changed:
                self.save.setEnabled(False)
                self.undo.setEnabled(False)
                self.redo.setEnabled(False)
        
    def set_undo_available(self, state):
        self.undo.setEnabled(state)
        
    def set_redo_available(self, state):
        self.redo.setEnabled(state)

    def save_completed(self):
        self.save.setEnabled(False)
        self.app.config_altered()
        
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
    
    """def on_insert_macro(self, macroName):
        token = self.app.service.phraseRunner.pluginManager.get_token(macroName, self)
        if token is not None:
            self.centralWidget.phrasePage.insert_token(token)"""
            
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

    def on_about(self):
        dlg = KAboutApplicationDialog(self.app.aboutData, self)
        dlg.show()

# ---- TreeWidget and helper functions

class WidgetItemFactory:
    
    def __init__(self, rootFolders):
        self.folders = rootFolders
    
    def get_root_folder_list(self):
        rootItems = []
        
        for folder in self.folders.values():
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
        self.setText(1, folder.get_abbreviation())
        self.setText(2, folder.get_hotkey_string())
        self.setData(3, Qt.UserRole, QVariant(folder))
        if parent is not None:
            parent.addChild(self)
            
        self.setFlags(self.flags() | Qt.ItemIsEditable)
            
    def update(self):
        self.setText(0, self.folder.title)
        self.setText(1, self.folder.get_abbreviation())
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
        self.setIcon(0, KIcon("edit-paste"))
        self.setText(0, phrase.description)
        self.setText(1, phrase.get_abbreviation())
        self.setText(2, phrase.get_hotkey_string())
        self.setData(3, Qt.UserRole, QVariant(phrase))
        if parent is not None:
            parent.addChild(self)      
            
        self.setFlags(self.flags() | Qt.ItemIsEditable)
            
    def update(self):
        self.setText(0, self.phrase.description)
        self.setText(1, self.phrase.get_abbreviation())
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
        self.setIcon(0, KIcon("text-x-script"))
        self.setText(0, script.description)
        self.setText(1, script.get_abbreviation())
        self.setText(2, script.get_hotkey_string())
        self.setData(3, Qt.UserRole, QVariant(script))
        if parent is not None:
            parent.addChild(self)
            
        self.setFlags(self.flags() | Qt.ItemIsEditable)
            
    def update(self):
        self.setText(0, self.script.description)
        self.setText(1, self.script.get_abbreviation())
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
