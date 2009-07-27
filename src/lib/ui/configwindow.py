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
from PyKDE4.kdeui import *
from PyKDE4.kdecore import i18n
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, QVariant, Qt


CONFIG_WINDOW_TITLE = i18n("Configuration")

FAQ_URL = "http://autokey.wiki.sourceforge.net/FAQ"
HELP_URL = "http://autokey.wiki.sourceforge.net/manual"
DONATE_URL = "https://sourceforge.net/donate/index.php?group_id=216191"

ACTION_DESCRIPTION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/gui.xml")

from dialogs import *
from .. configmanager import *
from .. import model

# ---- Internal widgets

import settingswidget

class SettingsWidget(QWidget, settingswidget.Ui_SettingsWidget):

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        settingswidget.Ui_SettingsWidget.__init__(self)
        self.setupUi(self)
        
    def on_setAbbrButton_pressed(self):
        dlg = AbbrSettingsDialog(self)
        dlg.show()
        
    def on_setHotkeyButton_pressed(self):
        dlg = HotkeySettingsDialog(self)
        dlg.show()
        
    def on_setFilterButton_pressed(self):
        dlg = WindowFilterSettingsDialog(self)
        dlg.show()



import scriptpage

class ScriptPage(QWidget, scriptpage.Ui_ScriptPage):

    def __init__(self):
        QWidget.__init__(self)
        scriptpage.Ui_ScriptPage.__init__(self)
        self.setupUi(self)

import phrasepage

class PhrasePage(QWidget, phrasepage.Ui_PhrasePage):

    def __init__(self):
        QWidget.__init__(self)
        phrasepage.Ui_PhrasePage.__init__(self)
        self.setupUi(self)

import folderpage

class FolderPage(QWidget, folderpage.Ui_FolderPage):

    def __init__(self):
        QWidget.__init__(self)
        folderpage.Ui_FolderPage.__init__(self)
        self.setupUi(self)

import centralwidget

class CentralWidget(QWidget, centralwidget.Ui_CentralWidget):

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        centralwidget.Ui_CentralWidget.__init__(self)
        self.setupUi(self)
        self.buttonBox.addButton(KStandardGuiItem.save(),
                        QDialogButtonBox.ButtonRole(QDialogButtonBox.NoRole), self.on_button)
        self.buttonBox.addButton(KStandardGuiItem.reset(), 
                        QDialogButtonBox.ButtonRole(QDialogButtonBox.NoRole), self.on_button)
    
    def on_treeView_customContextMenuRequested(self, position):
        print "blah"
        
    def on_button(self):
        print "blah"
    
        
    """def on_buttonBox_clicked(self, button):
        sb = self.buttonBox.standardButton(button)
        
        if sb == QDialogButtonBox.Save:
            print "Save"
        elif sb == QDialogButtonBox.Discard:
            print "Discard"
        elif sb == QDialogButtonBox.RestoreDefaults:
            print "Restore"
    """

# ---- Configuration window
    
class ConfigWindow(KXmlGuiWindow):

    def __init__(self, app):
        KXmlGuiWindow.__init__(self)
        self.centralWidget = CentralWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.app = app
        
        # File Menu
        self.newTopFolder = self.__createAction("new-top-folder", i18n("Top-level Folder"), "folder-new", self.new_folder)
        self.newFolder = self.__createAction("new-folder", i18n("Folder"), "folder-new", self.new_folder)
        self.newPhrase = self.__createAction("new-phrase", i18n("Phrase"), "document-new", self.new_folder)
        self.newScript = self.__createAction("new-script", i18n("Script"), "document-new", self.new_folder)
        self.save = self.__createAction("save", i18n("Save"), "document-new", self.new_folder, KStandardShortcut.Save)

        self.importSettings = self.__createAction("import", i18n("Import Settings"), target=self.new_folder)

        self.close = self.__createAction("close-window", i18n("Close Window"), "window-close", self.on_close, KStandardShortcut.Close)
        KStandardAction.quit(self.on_quit, self.actionCollection())

        # Edit Menu
        self.cut = self.__createAction("cut-item", i18n("Cut Item"), "edit-cut", self.new_folder)
        self.copy = self.__createAction("copy-item", i18n("Copy Item"), "edit-copy", self.new_folder)
        self.paste = self.__createAction("paste-item", i18n("Paste Item"), "edit-paste", self.new_folder)
        self.delete = self.__createAction("delete-item", i18n("Delete Item"), "edit-delete", self.new_folder)
        self.insert = self.__createAction("insert-macro", i18n("Insert Macro"), "insert-text", self.new_folder)
        self.record = self.__createAction("record-keystrokes", i18n("Record Keystrokes"), "media-record", self.new_folder)
        
        # Settings Menu
        self.enable = self.__createToggleAction("enable-monitoring", i18n("Enable Monitoring"), self.on_enable_toggled)
        self.advancedSettings = self.__createAction("advanced-settings", i18n("Advanced Settings"), "configure", self.new_folder)
        KStandardAction.configureToolbars(self.configureToolbars, self.actionCollection())
        
        # Help Menu
        self.__createAction("online-help", i18n("Online Manual"), "help-contents", self.on_show_help)
        self.__createAction("online-faq", i18n("F.A.Q."), "help-faq", self.on_show_faq)
        self.__createAction("donate", i18n("Donate"), "face-smile", self.on_donate)

        self.createGUI(ACTION_DESCRIPTION_FILE)
        self.setStandardToolBarMenuEnabled(True)

        self.setCaption(CONFIG_WINDOW_TITLE)
        self.resize(700, 550)
        
        # Initialise action states
        self.enable.setChecked(self.app.service.is_running())
        
        self.__popupateTreeWidget()

    def new_folder(self):
        print "new folder"

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


    def __createToggleAction(self, actionName, name, target):
        action = KToggleAction(name, self.actionCollection())
        if target is not None:
            self.connect(action, SIGNAL("triggered()"), target)
        self.actionCollection().addAction(actionName, action)
        return action
        
        
    def __popupateTreeWidget(self):
        factory = WidgetItemFactory(self.app.configManager.folders)
        
        for item in factory.get_root_folder_list():
            self.centralWidget.treeWidget.addTopLevelItem(item)
        
    # ---- Signal handlers ----
    
    # File Menu
    
    def on_close(self):
        #if self.dirty:
        #    selectedObject = self.__getTreeSelection()
        #    child = self.settingsBox.get_children()[0]
        #    child.on_save(None)           
        # TODO - prompt to save
        
        self.hide()
        self.destroy()
        self.app.configureWindow = None
        
    def on_quit(self):
        self.app.shutdown()
        
    # Settings Menu
        
    def on_enable_toggled(self):
        if self.enable.isChecked():
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    # Help Menu
            
    def on_show_faq(self):
        webbrowser.open(FAQ_URL, False, True)
        
    def on_show_help(self):
        webbrowser.open(HELP_URL, False, True)
        
    def on_donate(self):
        webbrowser.open(DONATE_URL, False, True)
        

# ---- TreeWidget and helper functions

class WidgetItemFactory:
    
    def __init__(self, rootFolders):
        self.folders = rootFolders
    
    def get_root_folder_list(self):
        rootItems = []
        
        for folder in self.folders.values():
            item = self.__buildItem(None, folder)
            rootItems.append(item)
            self.__processFolder(item, folder)
            
        return rootItems
        
    def __processFolder(self, parentItem, parentFolder):
        for folder in parentFolder.folders:
            item = self.__buildItem(parentItem, folder)
            self.__processFolder(item, folder)
        
        for childModelItem in parentFolder.items:
            self.__buildItem(parentItem, childModelItem)
    
    def __buildItem(self, parent, item):
        if isinstance(item, model.Folder):
            return self.__buildFolderWidgetItem(parent, item)
        elif isinstance(item, model.Phrase):
            return self.__buildPhraseWidgetItem(parent, item)
        elif isinstance(item, model.Script):
            return self.__buildScriptWidgetItem(parent, item)


    def __buildFolderWidgetItem(self, parent, folder):
        item = QTreeWidgetItem()
        item.setIcon(0, KIcon("folder"))
        item.setText(0, folder.title)
        item.setData(1, Qt.UserRole, QVariant(folder))
        if parent is not None:
            parent.addChild(item)
            
        return item

    def __buildPhraseWidgetItem(self, parent, phrase):
        item = QTreeWidgetItem()
        item.setIcon(0, KIcon("edit-paste"))
        item.setText(0, phrase.description)
        item.setData(1, Qt.UserRole, QVariant(phrase))
        if parent is not None:
            parent.addChild(item)
            
        return item

    def __buildScriptWidgetItem(self, parent, script):
        item = QTreeWidgetItem()
        item.setIcon(0, KIcon("text-x-script"))
        item.setText(0, script.description)
        item.setData(1, Qt.UserRole, QVariant(script))
        if parent is not None:
            parent.addChild(item)
            
        return item