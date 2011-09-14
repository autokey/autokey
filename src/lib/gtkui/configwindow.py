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

import logging, sys, os, webbrowser, re
import gtk, gtk.glade, gtksourceview2, pango

import gettext
import locale

GETTEXT_DOMAIN = 'autokey'

locale.setlocale(locale.LC_ALL, '')
for module in gtk.glade, gettext:
    module.bindtextdomain(GETTEXT_DOMAIN)
    module.textdomain(GETTEXT_DOMAIN)


from dialogs import *
from settingsdialog import SettingsDialog
from autokey.configmanager import *
from autokey.iomediator import Recorder
from autokey import model, common

CONFIG_WINDOW_TITLE = "AutoKey"

UI_DESCRIPTION_FILE = os.path.join(os.path.dirname(__file__), "data/menus.xml")

_logger = logging.getLogger("configwindow")

def get_ui(fileName):
    builder = gtk.Builder()
    uiFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/" + fileName)
    builder.add_from_file(uiFile)
    return builder

def set_linkbutton(button, path):
    button.set_sensitive(True)
    
    if path.startswith(CONFIG_DEFAULT_FOLDER):
        text = path.replace(CONFIG_DEFAULT_FOLDER, _("(Default folder)"))
    else:
        text = path.replace(os.path.expanduser("~"), "~")
    
    button.set_label(text)
    button.set_uri("file://" + path)
    label = button.get_child()
    label.set_ellipsize(pango.ELLIPSIZE_START)
    
class RenameDialog:
    
    def __init__(self, parentWindow, oldName, isNew, title=_("Rename '%s'")):
        builder = get_ui("renamedialog.xml")
        self.ui = builder.get_object("dialog")
        builder.connect_signals(self)
        
        self.nameEntry = builder.get_object("nameEntry")
        self.checkButton = builder.get_object("checkButton")
        self.image = builder.get_object("image")
        
        self.nameEntry.set_text(oldName.encode("utf-8"))
        self.checkButton.set_active(True)
        
        if isNew:
            self.checkButton.hide()
            self.set_title(title)
        else:
            self.set_title(title % oldName)
        
    def get_name(self):
        return self.nameEntry.get_text().decode("utf-8")
    
    def get_update_fs(self):
        return self.checkButton.get_active()
    
    def set_image(self, stockId):
        self.image.set_from_stock(stockId, gtk.ICON_SIZE_DIALOG)
        
    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)

class SettingsWidget:
	
    KEY_MAP = HotkeySettingsDialog.KEY_MAP
    REVERSE_KEY_MAP = HotkeySettingsDialog.REVERSE_KEY_MAP
	
    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("settingswidget.xml")
        self.ui = builder.get_object("settingswidget")
        builder.connect_signals(self)
        
        self.abbrDialog = AbbrSettingsDialog(parentWindow.ui, parentWindow.app.configManager, self.on_abbr_response)
        self.hotkeyDialog = HotkeySettingsDialog(parentWindow.ui, parentWindow.app.configManager, self.on_hotkey_response)
        self.filterDialog = WindowFilterSettingsDialog(parentWindow.ui)
        
        self.abbrLabel = builder.get_object("abbrLabel")
        self.clearAbbrButton = builder.get_object("clearAbbrButton")
        self.hotkeyLabel = builder.get_object("hotkeyLabel")
        self.clearHotkeyButton = builder.get_object("clearHotkeyButton")
        self.windowFilterLabel = builder.get_object("windowFilterLabel")
        self.clearFilterButton = builder.get_object("clearFilterButton")
        
    def load(self, item):
        self.currentItem = item
        
        self.abbrDialog.load(self.currentItem)
        if model.TriggerMode.ABBREVIATION in item.modes:
            self.abbrLabel.set_text(item.abbreviation)
            self.clearAbbrButton.set_sensitive(True)
            self.abbrEnabled = True
        else:
            self.abbrLabel.set_text(_("(None configured)"))
            self.clearAbbrButton.set_sensitive(False)
            self.abbrEnabled = False
        
        self.hotkeyDialog.load(self.currentItem)
        if model.TriggerMode.HOTKEY in item.modes:
            self.hotkeyLabel.set_text(item.get_hotkey_string())
            self.clearHotkeyButton.set_sensitive(True)
            self.hotkeyEnabled = True
        else:
            self.hotkeyLabel.set_text(_("(None configured)"))
            self.clearHotkeyButton.set_sensitive(False)
            self.hotkeyEnabled = False
        
        self.filterDialog.load(self.currentItem)
        if item.uses_default_filter():
            self.windowFilterLabel.set_text(_("(None configured)"))
            self.clearFilterButton.set_sensitive(False)
            self.filterEnabled = False
        else:
            self.windowFilterLabel.set_text(item.get_filter_regex())
            self.clearFilterButton.set_sensitive(True)
            self.filterEnabled = True
            
    def save(self):
        # Perform hotkey ungrab
        if model.TriggerMode.HOTKEY in self.currentItem.modes:
            self.parentWindow.app.hotkey_removed(self.currentItem)
        
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
            self.parentWindow.app.hotkey_created(self.currentItem)
            
    def set_dirty(self):
        self.parentWindow.set_dirty(True)
        
    # ---- Signal handlers
        
    def on_setAbbrButton_clicked(self, widget, data=None):
        self.abbrDialog.run()
         
    def on_abbr_response(self, res):
        if res == gtk.RESPONSE_OK:
            self.set_dirty()
            self.abbrEnabled = True
            self.abbrLabel.set_text(self.abbrDialog.get_abbr())
            self.clearAbbrButton.set_sensitive(True)
            
    def on_clearAbbrButton_clicked(self, widget, data=None):
        self.set_dirty()
        self.abbrEnabled = False
        self.clearAbbrButton.set_sensitive(False)
        self.abbrLabel.set_text(_("(None configured)"))
        self.abbrDialog.reset()
        
    def on_setHotkeyButton_clicked(self, widget, data=None):
        self.hotkeyDialog.run()
        
    def on_hotkey_response(self, res):
        if res == gtk.RESPONSE_OK:
            self.set_dirty()
            self.hotkeyEnabled = True
            key = self.hotkeyDialog.key
            modifiers = self.hotkeyDialog.build_modifiers()
            self.hotkeyLabel.set_text(self.currentItem.get_hotkey_string(key, modifiers))
            self.clearHotkeyButton.set_sensitive(True)
            
    def on_clearHotkeyButton_clicked(self, widget, data=None):
        self.set_dirty()
        self.hotkeyEnabled = False
        self.clearHotkeyButton.set_sensitive(False)
        self.hotkeyLabel.set_text(_("(None configured)"))
        self.hotkeyDialog.reset()

    def on_setFilterButton_clicked(self, widget, data=None):
        if self.filterDialog.run() == gtk.RESPONSE_OK:
            self.set_dirty()
            filterText = self.filterDialog.get_filter_text()
            if filterText != "":
                self.filterEnabled = True
                self.clearFilterButton.set_sensitive(True)
                self.windowFilterLabel.set_text(filterText)
            else:
                self.filterEnabled = False
                self.clearFilterButton.set_sensitive(False)
                self.windowFilterLabel.set_text(_("(None configured)"))

    def on_clearFilterButton_clicked(self, widget, data=None):
        self.set_dirty()
        self.filterEnabled = False
        self.clearFilterButton.set_sensitive(False)
        self.windowFilterLabel.set_text(_("(None configured)"))
        self.filterDialog.reset()

    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)

class BlankPage:
    
    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("blankpage.xml")
        self.ui = builder.get_object("blankpage")
        
    def load(self, theFolder):
        pass
            
    def save(self):
        pass
        
    def set_item_title(self, newTitle):
        pass
    
    def reset(self):
        pass
        
    def validate(self):
        return True
        
    def on_modified(self, widget, data=None):
        pass
    
    def set_dirty(self):
        self.parentWindow.set_dirty(True)

class FolderPage:
    
    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("folderpage.xml")
        self.ui = builder.get_object("folderpage")
        builder.connect_signals(self)
        
        self.showInTrayCheckbox = builder.get_object("showInTrayCheckbox")
        self.linkButton = builder.get_object("linkButton")
        label = self.linkButton.get_child()
        label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        
        vbox = builder.get_object("settingsVbox")
        self.settingsWidget = SettingsWidget(parentWindow)
        vbox.pack_start(self.settingsWidget.ui)
        
    def load(self, theFolder):
        self.currentFolder = theFolder
        self.showInTrayCheckbox.set_active(theFolder.showInTrayMenu)
        self.settingsWidget.load(theFolder)
        
        if self.is_new_item():
            self.linkButton.set_sensitive(False)
            self.linkButton.set_label(_("(Unsaved)"))
        else:
            set_linkbutton(self.linkButton, self.currentFolder.path)
    
    def save(self):
        self.currentFolder.showInTrayMenu = self.showInTrayCheckbox.get_active()
        self.settingsWidget.save()
        self.currentFolder.persist()
        set_linkbutton(self.linkButton, self.currentFolder.path)
        
        return not self.currentFolder.path.startswith(CONFIG_DEFAULT_FOLDER)
        
    def set_item_title(self, newTitle):
        self.currentFolder.title = newTitle.decode("utf-8")
        
    def rebuild_item_path(self):
        self.currentFolder.rebuild_path()
        
    def is_new_item(self):
        return self.currentFolder.path is None
    
    def reset(self):
        self.load(self.currentFolder)
        
    def validate(self):
        return True
        
    def on_modified(self, widget, data=None):
        self.set_dirty()
    
    def set_dirty(self):
        self.parentWindow.set_dirty(True)


class ScriptPage:
    
    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("scriptpage.xml")
        self.ui = builder.get_object("scriptpage")
        builder.connect_signals(self)
        
        self.buffer = gtksourceview2.Buffer()
        self.buffer.connect("changed", self.on_modified)
        self.editor = gtksourceview2.View(self.buffer)
        scrolledWindow = builder.get_object("scrolledWindow")
        scrolledWindow.add(self.editor)
        self.promptCheckbox = builder.get_object("promptCheckbox")
        self.showInTrayCheckbox = builder.get_object("showInTrayCheckbox")
        self.linkButton = builder.get_object("linkButton")
        label = self.linkButton.get_child()
        label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)

        vbox = builder.get_object("settingsVbox")
        self.settingsWidget = SettingsWidget(parentWindow)
        vbox.pack_start(self.settingsWidget.ui)
        
        # Configure script editor
        self.__m = gtksourceview2.LanguageManager()
        self.__sm = gtksourceview2.StyleSchemeManager()
        self.buffer.set_language(self.__m.get_language("python"))
        self.buffer.set_style_scheme(self.__sm.get_scheme("kate"))
        self.editor.set_auto_indent(True)
        self.editor.set_smart_home_end(True)
        self.editor.set_insert_spaces_instead_of_tabs(True)
        self.editor.set_tab_width(4)
        
        self.ui.show_all()

    def load(self, theScript):
        self.currentItem = theScript
        
        self.buffer.begin_not_undoable_action()
        self.buffer.set_text(theScript.code.encode("utf-8"))
        self.buffer.end_not_undoable_action()
        self.buffer.place_cursor(self.buffer.get_start_iter())
        
        self.promptCheckbox.set_active(theScript.prompt)
        self.showInTrayCheckbox.set_active(theScript.showInTrayMenu)
        self.settingsWidget.load(theScript)
        
        if self.is_new_item():
            self.linkButton.set_sensitive(False)
            self.linkButton.set_label(_("(Unsaved)"))
        else:
            set_linkbutton(self.linkButton, self.currentItem.path)
    
    def save(self):
        self.currentItem.code = self.buffer.get_text(self.buffer.get_start_iter(),
                                    self.buffer.get_end_iter()).decode("utf-8")
    
        self.currentItem.prompt = self.promptCheckbox.get_active()
        self.currentItem.showInTrayMenu = self.showInTrayCheckbox.get_active()
        
        self.settingsWidget.save()
        self.currentItem.persist()
        set_linkbutton(self.linkButton, self.currentItem.path)
        
        return False
        
    def set_item_title(self, newTitle):
        self.currentItem.description = newTitle.decode("utf-8")

    def rebuild_item_path(self):
        self.currentItem.rebuild_path()
        
    def is_new_item(self):
        return self.currentItem.path is None
    
    def reset(self):
        self.load(self.currentItem)
        self.parentWindow.set_undo_available(False)
        self.parentWindow.set_redo_available(False)
        
    def validate(self):
        text = self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter())
        if not validate(not EMPTY_FIELD_REGEX.match(text), _("The script code can't be empty"), self.editor,
                         self.parentWindow.ui):
            return False
        
        return True
        
    def start_record(self):
        self.buffer.insert(self.buffer.get_end_iter(), "\n")
        
    def start_key_sequence(self):
        self.buffer.insert(self.buffer.get_end_iter(), "keyboard.send_keys(\"")
        
    def end_key_sequence(self):
        self.buffer.insert(self.buffer.get_end_iter(), "\")\n")        
    
    def append_key(self, key):
        #line, pos = self.buffer.getCursorPosition()
        self.buffer.insert(self.buffer.get_end_iter(), key)
        #self.scriptCodeEditor.setCursorPosition(line, pos + len(key))
        
    def append_hotkey(self, key, modifiers):
        #line, pos = self.scriptCodeEditor.getCursorPosition()
        keyString = self.currentItem.get_hotkey_string(key, modifiers)
        self.buffer.insert(self.buffer.get_end_iter(), keyString)
        #self.scriptCodeEditor.setCursorPosition(line, pos + len(keyString))
        
    def append_mouseclick(self, xCoord, yCoord, button, windowTitle):
        self.buffer.insert(self.buffer.get_end_iter(), "mouse.click_relative(%d, %d, %d) # %s\n" % (xCoord, yCoord, int(button), windowTitle))
        
    def undo(self):
        self.buffer.undo()
        self.parentWindow.set_undo_available(self.buffer.can_undo())
        self.parentWindow.set_redo_available(self.buffer.can_redo())
                
    def redo(self):
        self.buffer.redo()
        self.parentWindow.set_undo_available(self.buffer.can_undo())
        self.parentWindow.set_redo_available(self.buffer.can_redo())
        
    def on_modified(self, widget, data=None):
        self.set_dirty()
        self.parentWindow.set_undo_available(self.buffer.can_undo())
        self.parentWindow.set_redo_available(self.buffer.can_redo())
    
    def set_dirty(self):
        self.parentWindow.set_dirty(True)


class PhrasePage(ScriptPage):

    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("phrasepage.xml")
        self.ui = builder.get_object("phrasepage")
        builder.connect_signals(self)
        
        self.buffer = gtksourceview2.Buffer()
        self.buffer.connect("changed", self.on_modified)
        self.editor = gtksourceview2.View(self.buffer)
        scrolledWindow = builder.get_object("scrolledWindow")
        scrolledWindow.add(self.editor)
        self.promptCheckbox = builder.get_object("promptCheckbox")
        self.showInTrayCheckbox = builder.get_object("showInTrayCheckbox")
        self.sendModeCombo = gtk.combo_box_new_text()
        self.sendModeCombo.connect("changed", self.on_modified)
        sendModeHbox = builder.get_object("sendModeHbox")
        sendModeHbox.pack_start(self.sendModeCombo, False, False)
        
        self.linkButton = builder.get_object("linkButton")

        vbox = builder.get_object("settingsVbox")
        self.settingsWidget = SettingsWidget(parentWindow)
        vbox.pack_start(self.settingsWidget.ui)

        # Populate combo
        l = model.SEND_MODES.keys()
        l.sort()
        for val in l:
            self.sendModeCombo.append_text(val)
        
        # Configure script editor
        #self.__m = gtksourceview2.LanguageManager()
        self.__sm = gtksourceview2.StyleSchemeManager()
        self.buffer.set_language(None)
        self.buffer.set_style_scheme(self.__sm.get_scheme("kate"))
        self.buffer.set_highlight_matching_brackets(False)
        self.editor.set_auto_indent(False)
        self.editor.set_smart_home_end(False)
        self.editor.set_insert_spaces_instead_of_tabs(True)
        self.editor.set_tab_width(4)
        
        self.ui.show_all()

    def load(self, thePhrase):
        self.currentItem = thePhrase
        
        self.buffer.begin_not_undoable_action()
        self.buffer.set_text(thePhrase.phrase.encode("utf-8"))
        self.buffer.end_not_undoable_action()
        self.buffer.place_cursor(self.buffer.get_start_iter())
        
        self.promptCheckbox.set_active(thePhrase.prompt)
        self.showInTrayCheckbox.set_active(thePhrase.showInTrayMenu)
        self.settingsWidget.load(thePhrase)
        
        if self.is_new_item():
            self.linkButton.set_sensitive(False)
            self.linkButton.set_label(_("(Unsaved)"))
        else:
            set_linkbutton(self.linkButton, self.currentItem.path)

        l = model.SEND_MODES.keys()
        l.sort()
        for k, v in model.SEND_MODES.iteritems():
            if v == thePhrase.sendMode:
                self.sendModeCombo.set_active(l.index(k))
                break
        
    
    def save(self):
        self.currentItem.phrase = self.buffer.get_text(self.buffer.get_start_iter(),
                                                        self.buffer.get_end_iter()).decode("utf-8")
    
        self.currentItem.prompt = self.promptCheckbox.get_active()
        self.currentItem.showInTrayMenu = self.showInTrayCheckbox.get_active()
        self.currentItem.sendMode = model.SEND_MODES[self.sendModeCombo.get_active_text()]
        
        self.settingsWidget.save()
        self.currentItem.persist()
        set_linkbutton(self.linkButton, self.currentItem.path)
        return False

    def validate(self):
        text = self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter()).decode("utf-8")
        if not validate(not EMPTY_FIELD_REGEX.match(text), _("The phrase content can't be empty"), self.editor,
                         self.parentWindow.ui):
            return False

        return True

        

class ConfigWindow:
    
    def __init__(self, app):
        app.monitor.suspend()
        self.app = app
        self.cutCopiedItems = []
        
        builder = get_ui("mainwindow.xml")
        self.ui = builder.get_object("mainwindow")
        builder.connect_signals(self)
        self.ui.set_title(CONFIG_WINDOW_TITLE)
        
        # Menus and Actions
        self.uiManager = gtk.UIManager()
        self.add_accel_group(self.uiManager.get_accel_group())
        
        # Menu Bar
        actionGroup = gtk.ActionGroup("menu")
        actions = [
                ("File", None, _("_File")),
                ("create", None, _("Create...")),
                ("new-top-folder", "folder-new", _("New _Top-Level Folder"), "", _("Create a new top-level phrase folder"), self.on_new_topfolder),
                ("new-folder", "folder-new", _("New _Folder"), "", _("Create a new phrase folder in the current folder"), self.on_new_folder),
                ("new-phrase", gtk.STOCK_NEW, _("New _Phrase"), "<control>n", _("Create a new phrase in the current folder"), self.on_new_phrase),
                ("new-script", gtk.STOCK_NEW, _("New _Script"), "<control><shift>n", _("Create a new script in the current folder"), self.on_new_script),
                ("save", gtk.STOCK_SAVE, _("_Save"), None, _("Save changes to current item"), self.on_save),
                ("close-window", gtk.STOCK_CLOSE, _("_Close window"), None, _("Close the configuration window"), self.on_close),
                ("quit", gtk.STOCK_QUIT, _("_Quit"), None, _("Completely exit AutoKey"), self.on_quit),
                ("Edit", None, _("_Edit")),
                ("cut-item", gtk.STOCK_CUT, _("Cu_t Item"), "", _("Cut the selected item"), self.on_cut_item),
                ("copy-item", gtk.STOCK_COPY, _("_Copy Item"), "", _("Copy the selected item"), self.on_copy_item),
                ("paste-item", gtk.STOCK_PASTE, _("_Paste Item"), "", _("Paste the last cut/copied item"), self.on_paste_item),
                ("clone-item", gtk.STOCK_COPY, _("C_lone Item"), "<control><shift>c", _("Clone the selected item"), self.on_clone_item),
                ("delete-item", gtk.STOCK_DELETE, _("_Delete Item"), "<control>d", _("Delete the selected item"), self.on_delete_item),
                ("rename", None, _("_Rename"), "F2", _("Rename the selected item"), self.on_rename),
                ("undo", gtk.STOCK_UNDO, _("_Undo"), "<control>z", _("Undo the last edit"), self.on_undo),
                ("redo", gtk.STOCK_REDO, _("_Redo"), "<control><shift>z", _("Redo the last undone edit"), self.on_redo),
                ("preferences", gtk.STOCK_PREFERENCES, _("_Preferences"), "", _("Additional options"), self.on_advanced_settings),
                ("View", None, _("_View")),
                ("script-error", gtk.STOCK_DIALOG_ERROR, _("Vie_w script error"), None, _("View script error information"), self.on_show_error),
                #("Settings", None, _("_Settings"), None, None, None),
                #("advanced", gtk.STOCK_PREFERENCES, _("_Advanced Settings"), "", _("Advanced configuration options"), self.on_advanced_settings),
                ("Help", None, _("_Help")),
                ("faq", None, _("_F.A.Q."), None, _("Display Frequently Asked Questions"), self.on_show_faq),
                ("help", gtk.STOCK_HELP, _("Online _Help"), None, _("Display Online Help"), self.on_show_help),
                ("donate", gtk.STOCK_YES, _("Donate"), "", _("Make A Donation"), self.on_donate),
                ("about", gtk.STOCK_ABOUT, _("About AutoKey"), None, _("Show program information"), self.on_show_about)
                ]
        actionGroup.add_actions(actions)
        
        toggleActions = [
                         #("enable-monitoring", None, _("_Enable Monitoring"), None, _("Toggle monitoring on/off"), self.on_enable_toggled),
                         ("toolbar", None, _("_Show Toolbar"), None, _("Show/hide the toolbar"), self.on_toggle_toolbar),
                         ("record", gtk.STOCK_MEDIA_RECORD, _("R_ecord Macro"), None, _("Record a keyboard/mouse macro"), self.on_record_keystrokes),
                         ]
        actionGroup.add_toggle_actions(toggleActions)
                
        self.uiManager.insert_action_group(actionGroup, 0)
        self.uiManager.add_ui_from_file(UI_DESCRIPTION_FILE)
        self.vbox = builder.get_object("vbox")
        self.vbox.pack_end(self.uiManager.get_widget("/MenuBar"), False, False)
        
        # Toolbar 'create' button 
        create = gtk.MenuToolButton(gtk.STOCK_NEW)
        create.show()
        menu = self.uiManager.get_widget('/NewDropdown')
        create.set_menu(menu)
        toolbar = self.uiManager.get_widget('/Toolbar')
        s = gtk.SeparatorToolItem()
        s.show()
        toolbar.insert(s, 0)
        toolbar.insert(create, 0)
        #if ConfigManager.SETTINGS[SHOW_TOOLBAR]:
        #    self.__addToolbar()
        self.uiManager.get_action("/MenuBar/View/toolbar").set_active(ConfigManager.SETTINGS[SHOW_TOOLBAR])
        
        self.treeView = builder.get_object("treeWidget")
        self.__initTreeWidget()
        
        self.stack = builder.get_object("stack")
        self.__initStack()
        
        self.saveButton = builder.get_object("saveButton")
        self.revertButton = builder.get_object("revertButton")
        self.hpaned = builder.get_object("hpaned")
        
        #self.uiManager.get_action("/MenuBar/Settings/enable-monitoring").set_active(app.service.is_running())
        #self.uiManager.get_action("/MenuBar/Settings/enable-monitoring").set_sensitive(not app.serviceDisabled)
        
        rootIter = self.treeView.get_model().get_iter_root()        
        if rootIter is not None:
            self.treeView.get_selection().select_iter(rootIter)

        self.on_tree_selection_changed(self.treeView)

        self.treeView.columns_autosize()
        
        width, height = ConfigManager.SETTINGS[WINDOW_DEFAULT_SIZE]
        self.set_default_size(width, height)
        self.hpaned.set_position(ConfigManager.SETTINGS[HPANE_POSITION])
        
        self.recorder = Recorder(self.scriptPage)
        
    def __addToolbar(self):
        toolbar = self.uiManager.get_widget('/Toolbar')
        self.vbox.pack_end(toolbar, False, False)
        self.vbox.reorder_child(toolbar, 1)
        
    def cancel_record(self):
        if self.uiManager.get_widget("/MenuBar/Edit/record").get_active():
            self.uiManager.get_widget("/MenuBar/Edit/record").set_active(False)
            self.recorder.stop()
            
    def save_completed(self, persistGlobal):
        self.saveButton.set_sensitive(False)
        self.uiManager.get_action("/MenuBar/File/save").set_sensitive(False)        
        self.app.config_altered(persistGlobal)
        
    def set_dirty(self, dirty):
        self.dirty = dirty
        self.uiManager.get_action("/MenuBar/File/save").set_sensitive(dirty)
        self.saveButton.set_sensitive(dirty)
        self.revertButton.set_sensitive(dirty)
        
    def update_actions(self, items, changed):
        if len(items) == 0:
            canCreate = False
            canCopy = False
            canRecord = False
            enableAny = False
        else:
            canCreate = isinstance(items[0], model.Folder) and len(items) == 1
            canCopy = True
            canRecord = isinstance(items[0], model.Script) and len(items) == 1
            enableAny = True
            for item in items:
                if isinstance(item, model.Folder):
                    canCopy = False
                    break
        
        self.uiManager.get_action("/MenuBar/File/create").set_sensitive(enableAny)
        self.uiManager.get_action("/MenuBar/File/create/new-top-folder").set_sensitive(True)
        self.uiManager.get_action("/MenuBar/File/create/new-folder").set_sensitive(canCreate)
        self.uiManager.get_action("/MenuBar/File/create/new-phrase").set_sensitive(canCreate)
        self.uiManager.get_action("/MenuBar/File/create/new-script").set_sensitive(canCreate)
        
        self.uiManager.get_action("/MenuBar/Edit/copy-item").set_sensitive(canCopy)
        self.uiManager.get_action("/MenuBar/Edit/cut-item").set_sensitive(enableAny)
        self.uiManager.get_action("/MenuBar/Edit/clone-item").set_sensitive(canCopy)
        self.uiManager.get_action("/MenuBar/Edit/paste-item").set_sensitive(canCreate and len(self.cutCopiedItems) > 0)
        self.uiManager.get_action("/MenuBar/Edit/delete-item").set_sensitive(enableAny)
        self.uiManager.get_action("/MenuBar/Edit/rename").set_sensitive(enableAny)
        self.uiManager.get_action("/MenuBar/Edit/record").set_sensitive(canRecord)
        
        if changed:
            self.uiManager.get_action("/MenuBar/File/save").set_sensitive(False)
            self.saveButton.set_sensitive(False)
            self.uiManager.get_action("/MenuBar/Edit/undo").set_sensitive(False)
            self.uiManager.get_action("/MenuBar/Edit/redo").set_sensitive(False)
        
    def set_undo_available(self, state):
        self.uiManager.get_action("/MenuBar/Edit/undo").set_sensitive(state)
        
    def set_redo_available(self, state):
        self.uiManager.get_action("/MenuBar/Edit/redo").set_sensitive(state)
        
    def refresh_tree(self):
        model, selectedPaths = self.treeView.get_selection().get_selected_rows()
        for path in selectedPaths:
            model.update_item(model[path].iter, self.__getTreeSelection())
        
    # ---- Signal handlers ----
    
    def on_save(self, widget, data=None):
        if self.__getCurrentPage().validate():
            persistGlobal = self.__getCurrentPage().save()
            self.save_completed(persistGlobal)
            self.set_dirty(False)
            
            self.refresh_tree()
    
    def on_reset(self, widget, data=None):
        self.__getCurrentPage().reset()
        self.set_dirty(False)
        self.cancel_record()
    
    def queryClose(self):
        if self.dirty:
            return self.promptToSave()

        return False
        
    def on_close(self, widget, data=None):
        ConfigManager.SETTINGS[WINDOW_DEFAULT_SIZE] = self.get_size()
        ConfigManager.SETTINGS[HPANE_POSITION] = self.hpaned.get_position()
        self.cancel_record()
        if self.queryClose():
            return True
        else:
            self.hide()
            self.destroy()
            self.app.configWindow = None
            self.app.config_altered(True)
            self.app.monitor.unsuspend()
            
    def on_quit(self, widget, data=None):
        #if not self.queryClose():
        ConfigManager.SETTINGS[WINDOW_DEFAULT_SIZE] = self.get_size()
        ConfigManager.SETTINGS[HPANE_POSITION] = self.hpaned.get_position()
        self.app.shutdown()
            
    # File Menu
    
    def on_new_topfolder(self, widget, data=None):
        dlg = gtk.FileChooserDialog(_("Create New Folder"), self.ui)
        dlg.set_action(gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER)
        dlg.set_local_only(True)
        dlg.add_buttons(_("Use Default"), gtk.RESPONSE_NONE, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK)
        
        response = dlg.run()
        if response == gtk.RESPONSE_OK:
            path = dlg.get_filename()
            self.__createFolder(os.path.basename(path), None, path)
        elif response == gtk.RESPONSE_NONE:
            self.__createFolder("New Folder", None)
            
        dlg.destroy()
        
    def on_new_folder(self, widget, data=None):
        name = self.__getNewItemName("Folder")
        if name is not None:
            theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
            parentIter = theModel[selectedPaths[0]].iter
            self.__createFolder(name, parentIter)
        
    def __createFolder(self, title, parentIter, path=None):
        theModel = self.treeView.get_model()        
        newFolder = model.Folder(title, path=path)
        newFolder.persist()
        newIter = theModel.append_item(newFolder, parentIter)
        self.treeView.expand_to_path(theModel.get_path(newIter))
        self.treeView.get_selection().unselect_all()
        self.treeView.get_selection().select_iter(newIter)
        self.on_tree_selection_changed(self.treeView)
        
        #if path is None:
        #    self.on_rename(self.treeView)
            
    def __getNewItemName(self, itemType):
        dlg = RenameDialog(self.ui, "New %s" % itemType, True, _("Create New %s") % itemType)
        dlg.set_image(gtk.STOCK_NEW)
                
        if dlg.run() == 1:
            newText = dlg.get_name()
            if validate(not EMPTY_FIELD_REGEX.match(newText), _("The name can't be empty"),
                             None, self.ui):
                dlg.destroy()
                return newText
            else:
                dlg.destroy()
                return None
            
        dlg.destroy()
        return None
        
    def on_new_phrase(self, widget, data=None):
        name = self.__getNewItemName("Phrase")
        if name is not None:
            theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
            parentIter = theModel[selectedPaths[0]].iter
            newPhrase = model.Phrase(name, "Enter phrase contents")
            newIter = theModel.append_item(newPhrase, parentIter)
            newPhrase.persist()
            self.treeView.expand_to_path(theModel.get_path(newIter))
            self.treeView.get_selection().unselect_all()
            self.treeView.get_selection().select_iter(newIter)
            self.on_tree_selection_changed(self.treeView)
            #self.on_rename(self.treeView)        
    
    def on_new_script(self, widget, data=None):
        name = self.__getNewItemName("Script")
        if name is not None:
            theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
            parentIter = theModel[selectedPaths[0]].iter
            newScript = model.Script(name, "# Enter script code")
            newIter = theModel.append_item(newScript, parentIter)
            newScript.persist()
            self.treeView.expand_to_path(theModel.get_path(newIter))
            self.treeView.get_selection().unselect_all()
            self.treeView.get_selection().select_iter(newIter)
            self.on_tree_selection_changed(self.treeView)
           # self.on_rename(self.treeView)

    # Edit Menu

    def on_cut_item(self, widget, data=None):
        self.cutCopiedItems = self.__getTreeSelection()
        selection = self.treeView.get_selection()
        model, selectedPaths = selection.get_selected_rows()
        refs = []
        for path in selectedPaths:
            refs.append(gtk.TreeRowReference(model, path))
            
        for ref in refs:
            if ref.valid():
                self.__removeItem(model, model[ref.get_path()].iter)
                
        if len(selectedPaths) > 1:
            self.treeView.get_selection().unselect_all()        
            self.treeView.get_selection().select_iter(model.get_iter_root())
            self.on_tree_selection_changed(self.treeView)
            
        self.app.config_altered(True)    
    
    def on_copy_item(self, widget, data=None):
        sourceObjects = self.__getTreeSelection()
        
        for source in sourceObjects:
            if isinstance(source, model.Phrase):
                newObj = model.Phrase('', '')
            else:
                newObj = model.Script('', '')
            newObj.copy(source)
            self.cutCopiedItems.append(newObj)
    
    def on_paste_item(self, widget, data=None):
        theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
        parentIter = theModel[selectedPaths[0]].iter
        
        newIters = []
        for item in self.cutCopiedItems:
            newIter = theModel.append_item(item, parentIter)
            if isinstance(item, model.Folder):
                theModel.populate_store(newIter, item)
            newIters.append(newIter)
            item.path = None
            item.persist()
                
        self.treeView.expand_to_path(theModel.get_path(newIters[-1]))
        self.treeView.get_selection().unselect_all()
        self.treeView.get_selection().select_iter(newIters[0])
        self.cutCopiedItems = []
        self.on_tree_selection_changed(self.treeView)        
        for iter in newIters:
            self.treeView.get_selection().select_iter(iter)        
        self.app.config_altered(True)
        
    def on_clone_item(self, widget, data=None):
        source = self.__getTreeSelection()[0]
        theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
        sourceIter = theModel[selectedPaths[0]].iter
        parentIter = theModel.iter_parent(sourceIter)
        
        if isinstance(source, model.Phrase):
            newObj = model.Phrase('', '')
        else:
            newObj = model.Script('', '')
        newObj.copy(source)
        newObj.persist()

        newIter = theModel.append_item(newObj, parentIter)
        self.app.config_altered(True)        
        
    def on_delete_item(self, widget, data=None):
        selection = self.treeView.get_selection()
        theModel, selectedPaths = selection.get_selected_rows()
        refs = []
        for path in selectedPaths:
            refs.append(gtk.TreeRowReference(theModel, path))

        modified = False
        
        if len(refs) == 1:
            item = theModel[refs[0].get_path()].iter
            modelItem = theModel.get_value(item, AkTreeModel.OBJECT_COLUMN)            
            if isinstance(modelItem, model.Folder):
                msg = _("Are you sure you want to delete '%s' and all the items in it?") % modelItem.title
            else:
                msg = _("Are you sure you want to delete '%s'?") % modelItem.description
        else:
            msg = _("Are you sure you want to delete the %d selected items?") % len(refs)
            
        dlg = gtk.MessageDialog(self.ui, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
        if dlg.run() == gtk.RESPONSE_YES:
            for ref in refs:
                if ref.valid():
                    item = theModel[ref.get_path()].iter
                    modelItem = theModel.get_value(item, AkTreeModel.OBJECT_COLUMN)
                    self.__removeItem(theModel, item)
                    modified = True

        dlg.destroy()            
        
        if modified: 
            if len(selectedPaths) > 1:
                self.treeView.get_selection().unselect_all()
                self.treeView.get_selection().select_iter(theModel.get_iter_root())
                self.on_tree_selection_changed(self.treeView)
            
            self.app.config_altered(True)
            
    def __removeItem(self, model, item):
        #selection = self.treeView.get_selection()
        #model, selectedPaths = selection.get_selected_rows()
        #parentIter = model.iter_parent(model[selectedPaths[0]].iter)
        parentIter = model.iter_parent(item)
        nextIter = model.iter_next(item)

        data = model.get_value(item, AkTreeModel.OBJECT_COLUMN)
        self.__deleteHotkeys(data)

        model.remove_item(item)

        if nextIter is not None:
            self.treeView.get_selection().select_iter(nextIter)
        elif parentIter is not None:
            self.treeView.get_selection().select_iter(parentIter)
        elif model.iter_n_children(None) > 0:
            selectIter = model.iter_nth_child(None, model.iter_n_children(None) - 1)
            self.treeView.get_selection().select_iter(selectIter)
        
        self.on_tree_selection_changed(self.treeView)

    def __deleteHotkeys(self, theItem):
        if model.TriggerMode.HOTKEY in theItem.modes:
            self.app.hotkey_removed(theItem)

        if isinstance(theItem, model.Folder):
            for subFolder in theItem.folders:
                self.__deleteHotkeys(subFolder)

            for item in theItem.items:
                if model.TriggerMode.HOTKEY in item.modes:
                    self.app.hotkey_removed(item)
        
    def on_undo(self, widget, data=None):
        self.__getCurrentPage().undo()

    def on_redo(self, widget, data=None):
        self.__getCurrentPage().redo()
        
    def on_record_keystrokes(self, widget, data=None):
        if widget.get_active():
            dlg = RecordDialog(self.ui, self.on_rec_response)
            dlg.run()
        else:
            self.recorder.stop()
            
    def on_rec_response(self, response, recKb, recMouse, delay):
        if response == gtk.RESPONSE_OK:
            self.recorder.set_record_keyboard(recKb)
            self.recorder.set_record_mouse(recMouse)
            self.recorder.start(delay)
        elif response == gtk.RESPONSE_CANCEL:
            self.uiManager.get_widget("/MenuBar/Edit/record").set_active(False)
        
    # View Menu
    
    def on_toggle_toolbar(self, widget, data=None):
        if widget.get_active():
            self.__addToolbar()
        else:
            self.vbox.remove(self.uiManager.get_widget('/Toolbar'))
            
        ConfigManager.SETTINGS[SHOW_TOOLBAR] = widget.get_active()
        
    def on_show_error(self, widget, data=None):
        self.app.show_script_error()
    
    # Settings Menu
    
    def on_enable_toggled(self, widget, data=None):
        if widget.get_active():
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_advanced_settings(self, widget, data=None):
        s = SettingsDialog(self.ui, self.app.configManager)
        s.show()

    # Help Menu
            
    def on_show_faq(self, widget, data=None):
        webbrowser.open(common.FAQ_URL, False, True)
        
    def on_show_help(self, widget, data=None):
        webbrowser.open(common.HELP_URL, False, True)
        
    def on_donate(self, widget, data=None):
        webbrowser.open(common.DONATE_URL, False, True)
        
    def on_show_about(self, widget, data=None):
        dlg = gtk.AboutDialog()
        dlg.set_name("AutoKey")
        dlg.set_comments(_("A desktop automation utility for Linux and X11."))
        dlg.set_version(common.VERSION)
        p = gtk.gdk.pixbuf_new_from_file_at_size(common.ICON_FILE, 100, 100)
        dlg.set_logo(p)
        dlg.set_website(common.HOMEPAGE)
        dlg.set_authors(["Chris Dekter (Developer) <cdekter@gmail.com>",
                        "Sam Peterson (Original developer) <peabodyenator@gmail.com>"])
        dlg.run()
        dlg.destroy()
        
    # Tree widget
    
    def on_rename(self, widget, data=None):
        selection = self.treeView.get_selection()
        theModel, selectedPaths = selection.get_selected_rows()
        selection.unselect_all()
        self.treeView.set_cursor(selectedPaths[0], self.treeView.get_column(0), False)
        selectedObject = self.__getTreeSelection()[0]
        if isinstance(selectedObject, model.Folder):
            oldName = selectedObject.title
        else:
            
            oldName = selectedObject.description
        
        dlg = RenameDialog(self.ui, oldName, False)
        dlg.set_image(gtk.STOCK_EDIT)
                
        if dlg.run() == 1:
            newText = dlg.get_name()
            if validate(not EMPTY_FIELD_REGEX.match(newText), _("The name can't be empty"),
                             None, self.ui):
                self.__getCurrentPage().set_item_title(newText)
                
                if dlg.get_update_fs():
                    self.__getCurrentPage().rebuild_item_path()
                
                persistGlobal = self.__getCurrentPage().save()
                self.refresh_tree()
                self.app.config_altered(persistGlobal)
            
        dlg.destroy()
    
    def on_treeWidget_row_activated(self, widget, path, viewColumn, data=None):
        widget.expand_row(path, False)
        
    def on_treeview_buttonpress(self, widget, event, data=None):
        return self.dirty
        
    def on_treeview_buttonrelease(self, widget, event, data=None):          
        if self.promptToSave():
            # True result indicates user selected Cancel. Stop event propagation
            return True
        else:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = widget.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                currentPath, currentCol = widget.get_cursor()
                if currentPath != path:
                    widget.set_cursor(path, col, 0)
                if event.button == 3:
                    self.__popupMenu(event)
            return False
    
    def on_drag_begin(self, *args):
        selection = self.treeView.get_selection()
        theModel, self.__sourceRows = selection.get_selected_rows()
        self.__sourceObjects = self.__getTreeSelection()
        
    def on_tree_selection_changed(self, widget, data=None):
        selectedObjects = self.__getTreeSelection()
        
        if len(selectedObjects) == 0:
            self.stack.set_current_page(0)
            self.set_dirty(False)
            self.cancel_record()
            self.update_actions(selectedObjects, True)
            self.selectedObject = None
        
        elif len(selectedObjects) == 1:
            selectedObject = selectedObjects[0]
 
            if isinstance(selectedObject, model.Folder):
                self.stack.set_current_page(1)
                self.folderPage.load(selectedObject)
            elif isinstance(selectedObject, model.Phrase):
                self.stack.set_current_page(2)
                self.phrasePage.load(selectedObject)
            else:
                self.stack.set_current_page(3)
                self.scriptPage.load(selectedObject)

            self.set_dirty(False)
            self.cancel_record()
            self.update_actions(selectedObjects, True)            
            self.selectedObject = selectedObject

        else:
            self.update_actions(selectedObjects, False)
                
    def on_drag_data_received(self, treeview, context, x, y, selection, info, etime):
        selection = self.treeView.get_selection()
        theModel, sourcePaths = selection.get_selected_rows()
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            targetIter = theModel.get_iter(path)
            
        targetModelItem = theModel.get_value(targetIter, AkTreeModel.OBJECT_COLUMN)
    
        for path in self.__sourceRows:
            self.__removeItem(theModel, theModel[path].iter)
        
        newIters = []
        for item in self.__sourceObjects:
            newIter = theModel.append_item(item, targetIter)    
            if isinstance(item, model.Folder):
                theModel.populate_store(newIter, item)
                self.__dropRecurseUpdate(item)
            else:
                item.path = None
                item.persist()
            newIters.append(newIter)
                
        self.treeView.expand_to_path(theModel.get_path(newIters[-1]))
        selection.unselect_all()
        for iter in newIters:
            selection.select_iter(iter)
        self.on_tree_selection_changed(self.treeView)
        self.app.config_altered(True)
        
    def __dropRecurseUpdate(self, folder):
        folder.path = None
        folder.persist()
        
        for subfolder in folder.folders:
            self.__dropRecurseUpdate(subfolder)
        
        for child in folder.items:
            child.path = None
            child.persist()
        
    def on_drag_drop(self, widget, drag_context, x, y, timestamp):
        drop_info = widget.get_dest_row_at_pos(x, y)
        if drop_info:
            selection = widget.get_selection()
            theModel, sourcePaths = selection.get_selected_rows()
            path, position = drop_info
            
            if position not in (gtk.TREE_VIEW_DROP_INTO_OR_BEFORE, gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
                return True
            
            targetIter = theModel.get_iter(path)
            targetModelItem = theModel.get_value(targetIter, AkTreeModel.OBJECT_COLUMN)
            if isinstance(targetModelItem, model.Folder) and path not in self.__sourceRows:
                # checking path prevents dropping a folder onto itself
                return False
            else:
                return True
        
        return True
            
    def __initTreeWidget(self):
        self.treeView.set_model(AkTreeModel(self.app.configManager.folders))
        self.treeView.set_headers_visible(True)
        self.treeView.set_reorderable(False)
        self.treeView.set_rubber_banding(True)
        targets = [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0)]
        self.treeView.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, targets, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_MOVE)
        self.treeView.enable_model_drag_dest(targets, gtk.gdk.ACTION_DEFAULT)
        self.treeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        # Treeview columns
        column1 = gtk.TreeViewColumn(_("Name"))
        iconRenderer = gtk.CellRendererPixbuf()
        textRenderer = gtk.CellRendererText()
        #textRenderer.set_property("editable", True)
        #textRenderer.connect("edited", self.on_cell_modified)
        column1.pack_start(iconRenderer, False)
        column1.pack_end(textRenderer, True)
        column1.add_attribute(iconRenderer, "icon-name", 0)
        column1.add_attribute(textRenderer, "text", 1)
        column1.set_expand(True)
        column1.set_min_width(150)
        self.treeView.append_column(column1)

        column2 = gtk.TreeViewColumn(_("Abbr."))
        textRenderer = gtk.CellRendererText()
        textRenderer.set_property("editable", False)
        column2.pack_start(textRenderer, True)
        column2.add_attribute(textRenderer, "text", 2)
        column2.set_expand(False)
        column2.set_min_width(50)
        self.treeView.append_column(column2)
        
        column3 = gtk.TreeViewColumn(_("Hotkey"))
        textRenderer = gtk.CellRendererText()
        textRenderer.set_property("editable", False)
        column3.pack_start(textRenderer, True)
        column3.add_attribute(textRenderer, "text", 3)
        column3.set_expand(False)
        column3.set_min_width(100)
        self.treeView.append_column(column3)
        
    def __popupMenu(self, event):
        menu = self.uiManager.get_widget("/Context")
        menu.popup(None, None, None, event.button, event.time)
        
    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)
    
    def __getTreeSelection(self):
        selection = self.treeView.get_selection()
        model, items = selection.get_selected_rows()
        ret = []

        if items:
            for item in items:
                value = model.get_value(model[item].iter, AkTreeModel.OBJECT_COLUMN)
                if value.parent not in ret: # Filter out any child objects that belong to a parent already in the list
                    ret.append(value)

        return ret
        
    def __initStack(self):
        self.blankPage = BlankPage(self)
        self.folderPage = FolderPage(self)
        self.phrasePage = PhrasePage(self)
        self.scriptPage = ScriptPage(self)
        self.stack.append_page(self.blankPage.ui)
        self.stack.append_page(self.folderPage.ui)
        self.stack.append_page(self.phrasePage.ui)
        self.stack.append_page(self.scriptPage.ui)
        
    def promptToSave(self):
        selectedObject = self.__getTreeSelection()
        current = self.__getCurrentPage()
            
        result = False
 
        if self.dirty:
            if ConfigManager.SETTINGS[PROMPT_TO_SAVE]:
                dlg = gtk.MessageDialog(self.ui, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                        _("There are unsaved changes. Would you like to save them?"))
                dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
                response = dlg.run()
                 
                if response == gtk.RESPONSE_YES:
                    self.on_save(None)
                    
                elif response == gtk.RESPONSE_CANCEL:
                    result = True
                
                dlg.destroy()
            else:
                self.on_save(None)

        return result
            
    def __getCurrentPage(self):
        #selectedObject = self.__getTreeSelection()
        
        if isinstance(self.selectedObject, model.Folder):
            return self.folderPage
        elif isinstance(self.selectedObject, model.Phrase):
            return self.phrasePage
        elif isinstance(self.selectedObject, model.Script):
            return self.scriptPage
        else:
            return None


class AkTreeModel(gtk.TreeStore):
    
    OBJECT_COLUMN = 4
    
    def __init__(self, folders):
        gtk.TreeStore.__init__(self, str, str, str, str, object)
        
        for folder in folders:
            iter = self.append(None, folder.get_tuple())
            self.populate_store(iter, folder)
            
        self.folders = folders
        self.set_sort_func(AkTreeModel.OBJECT_COLUMN, self.compare)
        self.set_sort_column_id(AkTreeModel.OBJECT_COLUMN, gtk.SORT_ASCENDING)

    def populate_store(self, parent, parentFolder):
        for folder in parentFolder.folders:
            iter = self.append(parent, folder.get_tuple())
            self.populate_store(iter, folder)
        
        for item in parentFolder.items:
            self.append(parent, item.get_tuple())
            
    def append_item(self, item, parentIter):
        if parentIter is None:
            self.folders.append(item)
            return self.append(None, item.get_tuple())
        
        else:
            parentFolder = self.get_value(parentIter, self.OBJECT_COLUMN)
            if isinstance(item, model.Folder):
                parentFolder.add_folder(item)
            else:
                parentFolder.add_item(item)
            
            return self.append(parentIter, item.get_tuple())
            
    def remove_item(self, iter):
        item = self.get_value(iter, self.OBJECT_COLUMN)
        item.remove_data()
        if item.parent is None:
            self.folders.remove(item)
        else:
            if isinstance(item, model.Folder):
                item.parent.remove_folder(item)
            else:
                item.parent.remove_item(item)
            
        self.remove(iter)
        
    def update_item(self, targetIter, items):
        for item in items:
            itemTuple = item.get_tuple()
            updateList = []
            for n in range(len(itemTuple)):
                updateList.append(n)
                updateList.append(itemTuple[n])
            self.set(targetIter, *updateList)
        
    def compare(self, theModel, iter1, iter2):
        item1 = theModel.get_value(iter1, AkTreeModel.OBJECT_COLUMN)
        item2 = theModel.get_value(iter2, AkTreeModel.OBJECT_COLUMN)
        
        if isinstance(item1, model.Folder) and (isinstance(item2, model.Phrase) or isinstance(item2, model.Script)):
            return -1
        elif isinstance(item2, model.Folder) and (isinstance(item1, model.Phrase) or isinstance(item1, model.Script)):
            return 1
        else:
            return cmp(str(item1), str(item2))
