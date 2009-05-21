import gtk, gobject, pynotify, re, time, copy, webbrowser, os.path
import phrase, phrasemenu, iomediator
from configurationmanager import *

UI_DESCRIPTION_FILE = os.path.join(os.path.dirname(__file__), "data/menus.xml")
ICON_FILE = "/usr/share/icons/autokeyicon.svg"
CONFIG_WINDOW_TITLE = "AutoKey Configuration"

FAQ_URL = "http://autokey.wiki.sourceforge.net/FAQ"
HELP_URL = "http://autokey.wiki.sourceforge.net/manual"
DONATE_URL = "https://sourceforge.net/donate/index.php?group_id=216191"

APPLICATION_VERSION = "0.53.1"

def gthreaded(f):
    
    def wrapper(*args):
        gtk.gdk.threads_enter()
        f(*args)
        gtk.gdk.threads_leave()
        
    wrapper.__name__ = f.__name__
    wrapper.__dict__ = f.__dict__
    wrapper.__doc__ = f.__doc__
    return wrapper

EMPTY_FIELD_REGEX = re.compile(r"^ *$", re.UNICODE)

def validate(expression, message, widget, parent):
    if not expression:
        dlg = gtk.MessageDialog(parent, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
                                 gtk.BUTTONS_OK, message)
        dlg.run()
        dlg.destroy()
        if widget is not None:
            widget.grab_focus()
    return expression

# Treemodel columns (used for combo box)

TREEMODEL_COLUMNS = {
                     "Title/Description" : 1,
                     "Abbreviation" : 2
                     }


WORD_CHAR_OPTIONS = {
                     "Default (locale dependent)" : phrase.DEFAULT_WORDCHAR_REGEX,
                     "All except Space and Enter" : r"[^ \n]"
                     }
WORD_CHAR_OPTIONS_ORDERED = ["Default (locale dependent)", "All except Space and Enter"]

class ConfigurationWindow(gtk.Window):
    
    def __init__(self, autokeyApp):
        gtk.Window.__init__(self)
        
        self.app = autokeyApp
        self.phraseSettings = PhraseSettings(self)
        self.folderSettings = PhraseFolderSettings(self) 
        self.settingsBox = gtk.VBox()
        self.settingsBox.add(gtk.Label(""))
        
        self.set_title(CONFIG_WINDOW_TITLE)
        self.set_size_request(800, 600)
        self.set_icon_from_file(ICON_FILE)
        vbox = gtk.VBox(False, 0)
        
        self.uiManager = gtk.UIManager()
        self.add_accel_group(self.uiManager.get_accel_group())
        
        # Menu Bar
        actionGroup = gtk.ActionGroup("menu")
        actions = [
                   ("File", None, "_File", None, None, self.on_show_file),
                   ("New Top-Level Folder", gtk.STOCK_NEW, "New _Top-Level Folder", "", "Create a new top-level phrase folder", self.on_new_folder),
                   ("New Folder", gtk.STOCK_NEW, "New _Folder", "", "Create a new phrase folder in the current folder", self.on_new_subfolder),
                   ("New Phrase", gtk.STOCK_NEW, "New _Phrase", "", "Create a new phrase in the current folder", self.on_new_phrase),
                   ("Save", gtk.STOCK_SAVE, "_Save", None, "Save changes to phrase/folder", self.on_save),
                   ("Import Settings", None, "_Import Settings", None, "Import settings from AutoKey 0.40", self.on_import_settings),                   
                   ("Close", gtk.STOCK_CLOSE, "_Close window", None, "Close the configuration window", self.on_close),
                   ("Quit", gtk.STOCK_QUIT, "_Quit AutoKey", None, "Completely exit AutoKey", self.on_destroy_and_exit),
                   ("Edit", None, "_Edit", None, None, self.on_show_edit),
                   ("Cut Item", gtk.STOCK_CUT, "Cu_t Item", "", "Cut the selected item", self.on_cut_item),
                   ("Copy Item", gtk.STOCK_COPY, "_Copy Item", "", "Copy the selected item", self.on_copy_item),
                   ("Paste Item", gtk.STOCK_PASTE, "_Paste Item", "", "Paste the last cut/copied item", self.on_paste_item),
                   ("Delete Item", gtk.STOCK_DELETE, "_Delete Item", None, "Delete the selected item", self.on_delete_item),
                   ("Insert Macro", None, "Insert _Macro", "", "Insert a macro into the current phrase", None),
                   ("Settings", None, "_Settings", None, None, self.on_show_settings),
                   ("Advanced Settings", gtk.STOCK_PREFERENCES, "_Advanced Settings", "", "Advanced configuration options", self.on_show_advanced_settings),
                   ("Help", None, "_Help"),
                   ("FAQ", None, "_FAQ", None, "Display Frequently Asked Questions", self.on_show_faq),
                   ("Online Help", gtk.STOCK_HELP, "Online _Help", None, "Display Online Help", self.on_show_help),
                   ("Donate", gtk.STOCK_YES, "Donate", "", "Make A Donation", self.on_donate),
                   ("About", gtk.STOCK_ABOUT, "About AutoKey", None, "Show program information", self.on_show_about)
                   ]
        actionGroup.add_actions(actions)
        
        toggleActions = [
                         ("Enable Expansions", None, "_Enable Expansions", None, "Toggle expansions on/off", self.on_expansions_toggled)
                         ]
        actionGroup.add_toggle_actions(toggleActions)
                
        self.uiManager.insert_action_group(actionGroup, 0)
        print os.path.realpath('.')
        self.uiManager.add_ui_from_file(UI_DESCRIPTION_FILE)        
        #vbox.pack_start(self.uiManager.get_widget("/MenuBar"), False, False)
        alignment = gtk.Alignment(xscale=1.0)
        alignment.add(self.uiManager.get_widget("/MenuBar"))
        vbox.pack_start(alignment, False, False, 5)
        
        # Get references to toolbar buttons and misc items
        self.toggleExpansionsMenuItem = self.uiManager.get_widget("/MenuBar/Settings/Enable Expansions")
        self.uiManager.get_widget("/MenuBar/Settings/Enable Expansions").set_active(autokeyApp.service.is_running())

        #Panes
        self.panes = gtk.HPaned()
        self.panes.set_position(250)
        vbox.add(self.panes)
        
        # Treeview
        treeViewVbox = gtk.VBox()
        self.panes.add1(treeViewVbox)
        self.panes.add2(self.settingsBox)
        
        treeViewScrolledWindow = gtk.ScrolledWindow()
        treeViewScrolledWindow.set_shadow_type(gtk.SHADOW_IN)
        treeViewScrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        treeViewVbox.pack_start(treeViewScrolledWindow)
        self.treeView = PhraseTreeView(autokeyApp.service.configManager.folders)
        self.treeView.connect("cursor-changed", self.on_tree_selection_changed)
        self.treeView.connect("button-press-event", self.on_treeview_clicked)
        treeViewScrolledWindow.add(self.treeView)
        
        # Search expander
        expander = SearchExpander()
        treeViewVbox.pack_start(expander, False, False, 5)
        self.treeView.set_search_entry(expander.searchEntry)
        expander.searchColumnCombo.connect("changed", self.on_combo_selection_changed)
        
        self.add(vbox)
        self.connect("hide", self.on_close)
        self.show_all()
        #self.treeView.get_selection().select_path(0)
        #self.on_tree_selection_changed(self.treeView)
        
        self.dirty = False
        self.cutCopiedItem = None
        
    def refresh_tree(self, item):
        self.app.service.configManager.config_altered()
        model, iter = self.treeView.get_selection().get_selected()
        model.update_item(iter, item)
    
    def on_show_file(self, widget, data=None):
        selection = self.__getTreeSelection()
        canCreatePhrase = isinstance(selection, phrase.PhraseFolder)
        canCreateSubFolder = canCreatePhrase
        self.uiManager.get_widget("/MenuBar/File/New Top-Level Folder").set_sensitive(True)
        self.uiManager.get_widget("/MenuBar/File/New Folder").set_sensitive(canCreateSubFolder)
        self.uiManager.get_widget("/MenuBar/File/New Phrase").set_sensitive(canCreatePhrase)
        self.uiManager.get_widget("/MenuBar/File/Save").set_sensitive(self.dirty)
            
    def on_show_edit(self, widget, data=None):
        selection = self.__getTreeSelection()
        self.uiManager.get_widget("/MenuBar/Edit/Cut").set_sensitive(selection is not None)
        self.uiManager.get_widget("/MenuBar/Edit/Copy").set_sensitive(isinstance(selection, phrase.Phrase))
        self.uiManager.get_widget("/MenuBar/Edit/Paste").set_sensitive((self.cutCopiedItem is not None)
                                                                        and canCreatePhrase)
        self.uiManager.get_widget("/MenuBar/Edit/Delete").set_sensitive(selection is not None)
        
        insertMacroItem = self.uiManager.get_widget("/MenuBar/Edit/Insert Macro") 
        if isinstance(selection, phrase.Phrase):
            insertMacroItem.set_sensitive(True)
            
            # Build submenu
            subMenu = gtk.Menu()
            for actionName in self.app.service.pluginManager.get_action_list():
                menuItem = gtk.MenuItem(actionName)
                menuItem.connect("activate", self.on_insert_macro, actionName)
                subMenu.append(menuItem)
            
            subMenu.show_all()
            insertMacroItem.set_submenu(subMenu)
                
        else:
            insertMacroItem.set_sensitive(False)
        
    def on_show_settings(self, widget, data=None):
        self.toggleExpansionsMenuItem.set_active(ConfigurationManager.SETTINGS[SERVICE_RUNNING])
        
    def on_close(self, widget, data=None):
        if self.dirty:
            selectedObject = self.__getTreeSelection()
            child = self.settingsBox.get_children()[0]
            child.on_save(None)           
        
        self.hide()
        self.destroy()
        self.app.configureWindow = None
        
    def on_destroy_and_exit(self, widget, data=None):
        self.app.shutdown()
        gtk.main_quit()
        
    def on_combo_selection_changed(self, widget, data=None):
        selected = widget.get_active_text()
        self.treeView.set_search_column(TREEMODEL_COLUMNS[selected])
        
    def on_tree_selection_changed(self, widget, data=None):
        selectedObject = self.__getTreeSelection()
        child = self.settingsBox.get_children()[0]
 
        if selectedObject is not None:
            if isinstance(selectedObject, phrase.Phrase):
                if child is not self.phraseSettings:
                    self.settingsBox.remove(child)
                    self.settingsBox.add(self.phraseSettings)
                self.phraseSettings.load(selectedObject)
            else:
                if child is not self.folderSettings:
                    self.settingsBox.remove(child)
                    self.settingsBox.add(self.folderSettings)
                self.folderSettings.load(selectedObject)
            
            self.dirty = False
        
        else:    
            self.settingsBox.remove(child)
            self.settingsBox.add(gtk.Label(""))  
    
    def on_new_folder(self, widget, data=None):
        self.__createFolder(None)
        
    def on_new_subfolder(self, widget, data=None):
        model, parentIter = self.treeView.get_selection().get_selected()
        self.__createFolder(parentIter)
        
    def __createFolder(self, parentIter):
        model = self.treeView.get_model()
        newFolder = phrase.PhraseFolder("New Folder")   
        newIter = model.append_item(newFolder, parentIter)
        self.treeView.expand_to_path(model.get_path(newIter))
        self.treeView.get_selection().select_iter(newIter)
        self.on_tree_selection_changed(self.treeView)
        
    def on_new_phrase(self, widget, data=None):
        model, parentIter = self.treeView.get_selection().get_selected()
        newPhrase = phrase.Phrase("New Phrase", "Enter phrase contents")
        newIter = model.append_item(newPhrase, parentIter)
        self.treeView.expand_to_path(model.get_path(newIter))
        self.treeView.get_selection().select_iter(newIter)
        self.on_tree_selection_changed(self.treeView)
        
    def on_insert_macro(self, widget, actionName):
        phraseSettings = self.settingsBox.get_children()[0]
        token = self.app.service.pluginManager.get_token(actionName, self)
        if token is not None:
            phraseSettings.insert_token(token)        
        
    def on_save(self, widget, data=None):
        child = self.settingsBox.get_children()[0]
        child.on_save(widget)
        
    def on_cut_item(self, widget, data=None):
        self.cutCopiedItem = self.__getTreeSelection()
        selection = self.treeView.get_selection()
        model, item = selection.get_selected()
        self.__removeItem(model, item)
    
    def on_copy_item(self, widget, data=None):
        self.cutCopiedItem = phrase.Phrase('', '')
        self.cutCopiedItem.copy(self.__getTreeSelection())
    
    def on_paste_item(self, widget, data=None):
        model, parentIter = self.treeView.get_selection().get_selected()
        newIter = model.append_item(self.cutCopiedItem, parentIter)
        if isinstance(self.cutCopiedItem, phrase.PhraseFolder):
            model.populate_store(newIter, self.cutCopiedItem)
        self.treeView.expand_to_path(model.get_path(newIter))  
        self.cutCopiedItem = None
        
    def on_delete_item(self, widget, data=None):
        selection = self.treeView.get_selection()
        model, item = selection.get_selected()
        
        # Prompt for removal of a folder with phrases
        if model.iter_n_children(item) > 0:
            dlg = gtk.MessageDialog(self, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                    "Are you sure you want to delete this folder and all the folders/phrases in it?")
            if dlg.run() == gtk.RESPONSE_YES:
                self.__removeItem(model, item)
            dlg.destroy()
            
        else:
            self.__removeItem(model, item)

    def __removeItem(self, model, item):
        model.remove_item(item)
        self.app.service.configManager.config_altered()
        self.on_tree_selection_changed(self.treeView)            
        
    def on_import_settings(self, widget, data=None):
        dlg = gtk.FileChooserDialog("Import settings from AutoKey 0.40", self, 
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dlg.set_default_response(gtk.RESPONSE_OK)
        dlg.set_select_multiple(False)
        filter = gtk.FileFilter()
        filter.set_name("Configuration files")
        filter.add_pattern("*.ini")
        dlg.add_filter(filter)
        
        if dlg.run() == gtk.RESPONSE_OK:
            fileName = dlg.get_filename()
            
            try:
                folder, phrases = self.app.service.configManager.import_legacy_settings(fileName)
            except ImportException, ie:
                self.app.show_error_dialog("Unable to import the configuration file:\n" + str(ie))
            else:
                model = self.treeView.get_model()
                
                iter = model.append_item(folder, None)
                for phrase in phrases:
                    model.append_item(phrase, iter)
                    
        dlg.destroy()
        
        self.app.service.configManager.config_altered()
        
    def on_expansions_toggled(self, widget, data=None):
        if self.toggleExpansionsMenuItem.active:
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_show_advanced_settings(self, widget, data=None):
        dlg = AdvancedSettingsDialog(self)
        dlg.load(self.app.service.configManager)
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            dlg.save(self.app.service.configManager)
        dlg.destroy()        

    def on_show_faq(self, widget, data=None):
        webbrowser.open(FAQ_URL, False, True)
        
    def on_show_help(self, widget, data=None):
        webbrowser.open(HELP_URL, False, True)
        
    def on_donate(self, widget, data=None):
        webbrowser.open(DONATE_URL, False, True)

    def on_show_about(self, widget, data=None):        
        dlg = gtk.AboutDialog()
        dlg.set_name("AutoKey")
        dlg.set_comments("A text expansion and hotkey utility for Linux\nAutoKey has saved you %d keystrokes" % 
                         ConfigurationManager.SETTINGS[INPUT_SAVINGS])
        dlg.set_version(APPLICATION_VERSION)
        p = gtk.gdk.pixbuf_new_from_file(ICON_FILE)
        dlg.set_logo(p)
        dlg.run()
        dlg.destroy()
        
    def on_treeview_clicked(self, widget, event, data=None):
        if not self.__promptToSave():
            # False result indicates user selected Cancel. Stop event propagation
            return True
        else:
            if event.button == 3:
                self.__popupMenu(event)

    def __popupMenu(self, event):
        selection = self.__getTreeSelection()            
        canCreatePhrase = isinstance(selection, phrase.PhraseFolder)
        canCreateSubFolder = canCreatePhrase
        
        menu = gtk.Menu()
        newFolderMenuItem = gtk.ImageMenuItem("New Folder")
        newFolderMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU))
        newFolderMenuItem.set_sensitive(canCreateSubFolder)
        newFolderMenuItem.connect("activate", self.on_new_subfolder)
        
        newPhraseMenuItem = gtk.ImageMenuItem("New Phrase")
        newPhraseMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU))
        newPhraseMenuItem.set_sensitive(canCreatePhrase)
        newPhraseMenuItem.connect("activate", self.on_new_phrase)
        
        deleteMenuItem = gtk.ImageMenuItem("Delete")
        deleteMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU))
        deleteMenuItem.set_sensitive(selection is not None)
        deleteMenuItem.connect("activate", self.on_delete_item)
        
        cutMenuItem = gtk.ImageMenuItem(gtk.STOCK_CUT)
        cutMenuItem.set_sensitive(selection is not None)
        cutMenuItem.connect("activate", self.on_cut_item)
        
        copyMenuItem = gtk.ImageMenuItem(gtk.STOCK_COPY)
        copyMenuItem.set_sensitive(isinstance(selection, phrase.Phrase))
        copyMenuItem.connect("activate", self.on_copy_item)
        
        pasteMenuItem = gtk.ImageMenuItem(gtk.STOCK_PASTE)
        pasteMenuItem.set_sensitive((self.cutCopiedItem is not None) and canCreatePhrase)
        pasteMenuItem.connect("activate", self.on_paste_item)
        
        menu.append(newFolderMenuItem)
        menu.append(newPhraseMenuItem)
        menu.append(deleteMenuItem)
        menu.append(gtk.SeparatorMenuItem())
        menu.append(cutMenuItem)
        menu.append(copyMenuItem)
        menu.append(pasteMenuItem)
        menu.show_all()
        
        menu.popup(None, None, None, event.button, event.time)
        
    def __promptToSave(self):
        selectedObject = self.__getTreeSelection()
        child = self.settingsBox.get_children()[0]
        result = True
 
        if self.dirty:
            if ConfigurationManager.SETTINGS[PROMPT_TO_SAVE]:
                dlg = gtk.MessageDialog(self, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                        "There are unsaved changes. Would you like to save them?")
                dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
                response = dlg.run()
                 
                if response == gtk.RESPONSE_YES:
                    if not isinstance(child, gtk.Label):
                        result = child.save()
                elif response == gtk.RESPONSE_CANCEL:
                    result = False
                
                dlg.destroy()
            else:
                child.save(None)
        
        return result
        
    def __getTreeSelection(self):
        selection = self.treeView.get_selection()
        model, item = selection.get_selected()
        if item is not None:
            return model.get_value(item, 3)
        else:
            return None    
        
class SearchExpander(gtk.Expander):
    
    def __init__(self):
        gtk.Expander.__init__(self, "Search")
        vbox = gtk.VBox()
        self.add(vbox) 

        self.searchColumnCombo = gtk.combo_box_new_text()
        keys = TREEMODEL_COLUMNS.keys()
        keys.sort(reverse=True)
        for value in keys:
            self.searchColumnCombo.append_text(value)
        self.searchColumnCombo.set_active(0)
        vbox.pack_start(self.searchColumnCombo, padding=5)

        self.searchEntry = gtk.Entry()
        vbox.pack_start(self.searchEntry)
        
        
class AdvancedSettingsDialog(gtk.Dialog):
    
    def __init__(self, parent):
        gtk.Dialog.__init__(self, "Advanced Settings", parent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                             (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_has_separator(False)
        self.noteBook = gtk.Notebook()
        self.vbox.add(self.noteBook)
        
        # General settings page
        self.showInTray = gtk.CheckButton("Show a tray icon (requires restart)")
        self.takesFocus = gtk.CheckButton("Allow keyboard navigation of phrase menu")
        self.sortByCount = gtk.CheckButton("Sort phrase menu items by highest usage")
        self.detectUnwanted = gtk.CheckButton("Detect unwanted abbreviation triggers")
        self.promptSave = gtk.CheckButton("Prompt for unsaved changes to folders or phrases")
        
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Suggest phrases after entering "), False)
        self.predictiveLength = gtk.SpinButton(gtk.Adjustment(5, 5, 20, 1))
        hbox.pack_start(self.predictiveLength, False)
        hbox.pack_start(gtk.Label(" characters"), False)
        
        label = gtk.Label("Enable this option if you experience randomly garbled text output in KDE 4.x")
        label.set_alignment(0, 0.5)
        #label.set_line_wrap(True)
        self.useWorkAround = gtk.CheckButton("Enable QT4 workaround")
        
        vbox = gtk.VBox()
        vbox.pack_start(self.showInTray)
        vbox.pack_start(self.takesFocus)
        vbox.pack_start(self.sortByCount)
        vbox.pack_start(self.detectUnwanted)
        vbox.pack_start(self.promptSave)
        vbox.pack_start(hbox, False, False, 5)
        vbox.pack_start(gtk.HSeparator(), padding=10)
        vbox.pack_start(label)
        vbox.pack_start(self.useWorkAround)
        self.add_page(vbox, "General")
        
        # Hotkey settings Page
        self.showConfigSetting = GlobalHotkeySettings(parent, self, "Use a hotkey to show the configuration window")
        self.toggleServiceSetting = GlobalHotkeySettings(parent, self, "Use a hotkey to toggle expansions")
        self.showPopupSettings = GlobalHotkeySettings(parent, self, "Use a hotkey to show the abbreviations popup")
        
        vbox = gtk.VBox()
        vbox.pack_start(self.showConfigSetting)
        vbox.pack_start(self.toggleServiceSetting)
        vbox.pack_start(self.showPopupSettings)
        self.add_page(vbox, "Special Hotkeys")
        
        self.show_all()
        
    def load(self, configManager):
        self.showInTray.set_active(configManager.SETTINGS[SHOW_TRAY_ICON])
        self.takesFocus.set_active(configManager.SETTINGS[MENU_TAKES_FOCUS])
        self.sortByCount.set_active(configManager.SETTINGS[SORT_BY_USAGE_COUNT])
        self.detectUnwanted.set_active(configManager.SETTINGS[DETECT_UNWANTED_ABBR])
        self.promptSave.set_active(configManager.SETTINGS[PROMPT_TO_SAVE])
        self.predictiveLength.set_value(configManager.SETTINGS[PREDICTIVE_LENGTH])
        self.useWorkAround.set_active(configManager.SETTINGS[ENABLE_QT4_WORKAROUND])
        
        self.showConfigSetting.load(configManager.configHotkey)
        self.toggleServiceSetting.load(configManager.toggleServiceHotkey)
        self.showPopupSettings.load(configManager.showPopupHotkey)
        
    def save(self, configManager):
        configManager.SETTINGS[SHOW_TRAY_ICON] = self.showInTray.get_active()
        configManager.SETTINGS[MENU_TAKES_FOCUS] = self.takesFocus.get_active()
        configManager.SETTINGS[SORT_BY_USAGE_COUNT] = self.sortByCount.get_active()
        configManager.SETTINGS[DETECT_UNWANTED_ABBR] = self.detectUnwanted.get_active()
        configManager.SETTINGS[PROMPT_TO_SAVE] = self.promptSave.get_active()
        configManager.SETTINGS[PREDICTIVE_LENGTH] = int(self.predictiveLength.get_value())
        configManager.SETTINGS[ENABLE_QT4_WORKAROUND] = self.useWorkAround.get_active()
        
        self.showConfigSetting.save(configManager.configHotkey)
        self.toggleServiceSetting.save(configManager.toggleServiceHotkey)
        self.showPopupSettings.save(configManager.showPopupHotkey)
        
    def add_page(self, page, pageTitle):
        alignment = gtk.Alignment(xscale=1.0)
        alignment.set_padding(5, 5, 5, 5)
        alignment.add(page)
        self.noteBook.append_page(alignment, gtk.Label(pageTitle))
        
    def set_dirty(self):
        pass


class PhraseFolderSettings(gtk.VBox):
    
    def __init__(self, configWindow):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow
                
        label = gtk.Label("Folder Title")
        label.set_alignment(0, 0.5)
        self.pack_start(label, False)
        
        self.folderTitle = gtk.Entry(50)
        self.folderTitle.connect("changed", self.on_modified)
        self.pack_start(self.folderTitle, False)
        
        self.showInTray = gtk.CheckButton("Show in tray menu")
        self.showInTray.connect("toggled", self.on_modified)
        self.pack_start(self.showInTray, False)
        
        self.saveButton = gtk.Button("Save", gtk.STOCK_SAVE)
        self.revertButton = gtk.Button("Revert", gtk.STOCK_REVERT_TO_SAVED)
        
        self.settingsNoteBook = FolderSettingsNotebook(configWindow, self)
        self.pack_start(self.settingsNoteBook, False, True, 5)
        
        self.pack_start(gtk.Label(""))
        
        buttonBox = gtk.HButtonBox()
        #self.saveButton = gtk.Button("Save", gtk.STOCK_SAVE)
        self.saveButton.connect("clicked", self.on_save)
        #self.revertButton = gtk.Button("Revert", gtk.STOCK_REVERT_TO_SAVED)
        self.revertButton.connect("clicked", self.on_revert)
        buttonBox.pack_end(self.saveButton)
        buttonBox.pack_end(self.revertButton)
        buttonBox.set_layout(gtk.BUTTONBOX_END)
        self.pack_start(buttonBox, False, False, 5)
        
        self.show_all()
        
        #self.dirty = False
        
    def load(self, theFolder):
        self.currentFolder = theFolder
        self.folderTitle.set_text(theFolder.title)
        self.showInTray.set_active(theFolder.showInTrayMenu)
        self.settingsNoteBook.load(theFolder)
        self.folderTitle.grab_focus()
        self.saveButton.set_sensitive(False)
        self.revertButton.set_sensitive(False)        
        
    def set_dirty(self, dirtyState):
        self.saveButton.set_sensitive(dirtyState)
        self.revertButton.set_sensitive(dirtyState)
        self.configWindow.dirty = dirtyState
        
    def on_save(self, widget, data=None):
        self.save()
        
    def save(self):
        if self.validate():
            self.currentFolder.title = self.folderTitle.get_text()
            self.currentFolder.set_modes([])
            self.currentFolder.showInTrayMenu = self.showInTray.get_active()
            self.settingsNoteBook.save(self.currentFolder)
            self.configWindow.refresh_tree(self.currentFolder)
            self.set_dirty(False)
            return True
        else:
            return False
            
    def on_modified(self, widget, data=None):
        self.set_dirty(True)        
                    
    def on_revert(self, widget, data=None):
        self.load(self.currentFolder)
        self.set_dirty(False)

    def validate(self):
        if not validate(not EMPTY_FIELD_REGEX.match(self.folderTitle.get_text()), "Folder title can not be empty",
                         self.folderTitle, self.configWindow):
            return False
        
        if not self.settingsNoteBook.validate(self.currentFolder):
            return False
        
        return True
        

class PhraseSettings(gtk.VBox):
    
    def __init__(self, configWindow):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow
        
        label = gtk.Label("Phrase Description")
        label.set_alignment(0, 0.5)
        self.pack_start(label, False)
        
        self.phraseDescription = gtk.Entry(50)
        self.phraseDescription.connect("changed", self.on_modified)
        self.pack_start(self.phraseDescription, False)
        
        label = gtk.Label("Phrase Contents")
        label.set_alignment(0, 0.5)
        self.pack_start(label, False, False, 5)
        
        self.phraseContents = gtk.TextView()
        self.phraseContents.set_left_margin(3)
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_shadow_type(gtk.SHADOW_IN)
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scrolledWindow.add(self.phraseContents)
        self.pack_start(scrolledWindow)
        
        self.predictive = gtk.CheckButton("Suggest this phrase using predictive mode")
        self.predictive.connect("toggled", self.on_modified)
        self.pack_start(self.predictive, False)
        self.promptBefore = gtk.CheckButton("Always prompt before pasting this phrase")
        self.promptBefore.connect("toggled", self.on_modified)
        self.pack_start(self.promptBefore, False)
        self.showInTray = gtk.CheckButton("Show in tray menu")
        self.showInTray.connect("toggled", self.on_modified)
        self.pack_start(self.showInTray, False)
        
        self.saveButton = gtk.Button("Save", gtk.STOCK_SAVE)
        self.revertButton = gtk.Button("Revert", gtk.STOCK_REVERT_TO_SAVED)
        self.settingsNoteBook = SettingsNotebook(configWindow, self)        
        self.pack_start(self.settingsNoteBook, False, True, 5)
        
        buttonBox = gtk.HButtonBox()
        #self.saveButton = gtk.Button("Save", gtk.STOCK_SAVE)
        self.saveButton.connect("clicked", self.on_save)
        #self.revertButton = gtk.Button("Revert", gtk.STOCK_REVERT_TO_SAVED)
        self.revertButton.connect("clicked", self.on_revert)
        buttonBox.pack_end(self.saveButton)
        buttonBox.pack_end(self.revertButton)
        buttonBox.set_layout(gtk.BUTTONBOX_END)
        self.pack_start(buttonBox, False, False, 5)
        
        self.show_all()
        
        #self.dirty = False
        
    def insert_token(self, token):
        buffer = self.phraseContents.get_buffer()
        buffer.insert_at_cursor(token)
        
    def load(self, thePhrase):
        self.currentPhrase = thePhrase
        self.phraseDescription.set_text(thePhrase.description)
        buffer = gtk.TextBuffer()
        buffer.set_text(thePhrase.phrase)
        buffer.connect("changed", self.on_modified)
        self.phraseContents.set_buffer(buffer)
        self.predictive.set_active(phrase.PhraseMode.PREDICTIVE in thePhrase.modes)
        self.promptBefore.set_active(thePhrase.prompt)
        self.showInTray.set_active(thePhrase.showInTrayMenu)
        self.settingsNoteBook.load(thePhrase)
        self.phraseDescription.grab_focus()
        self.saveButton.set_sensitive(False)
        self.revertButton.set_sensitive(False)        
        
    def set_dirty(self, dirtyState):
        self.saveButton.set_sensitive(dirtyState)
        self.revertButton.set_sensitive(dirtyState)        
        self.configWindow.dirty = dirtyState
        
    def on_save(self, widget, data=None):
        self.save()
        
    def save(self):
        if self.validate():
            self.currentPhrase.description = self.phraseDescription.get_text()
        
            buffer = self.phraseContents.get_buffer()
            self.currentPhrase.phrase = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        
            self.currentPhrase.set_modes([])
            if self.predictive.get_active():
                self.currentPhrase.modes.append(phrase.PhraseMode.PREDICTIVE)
                
            self.currentPhrase.prompt = self.promptBefore.get_active()
            self.currentPhrase.showInTrayMenu = self.showInTray.get_active()
            
            self.settingsNoteBook.save(self.currentPhrase)
            
            self.configWindow.refresh_tree(self.currentPhrase)
            
            self.set_dirty(False)
            return True
        else:
            return False        
            
        
    def on_revert(self, widget, data=None):
        self.load(self.currentPhrase)
        self.set_dirty(False)
        
    def on_modified(self, widget, data=None):
        self.set_dirty(True)
        
    def validate(self):
        if not validate(not EMPTY_FIELD_REGEX.match(self.phraseDescription.get_text()),
                         "Phrase description can not be empty", self.phraseDescription, self.configWindow):
            return False
        
        buffer = self.phraseContents.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        if not validate(not EMPTY_FIELD_REGEX.match(text), "Phrase contents can not be empty", self.phraseContents,
                         self.configWindow):
            return False
        
        if not self.settingsNoteBook.validate(self.currentPhrase):
            return False
        
        return True
      
        
class SettingsNotebook(gtk.Notebook):
    
    def __init__(self, configWindow, settingsPane):
        gtk.Notebook.__init__(self)
        self.settingsPane = settingsPane
        self.abbrSettings = AbbreviationSettings(configWindow, self)
        self.hotKeySettings = HotkeySettings(configWindow, self)
        self.windowFilterSettings = WindowFilterSettings(configWindow, self)
        self.add_page(self.abbrSettings, "Abbreviation")
        self.add_page(self.hotKeySettings, "Hotkey")
        self.add_page(self.windowFilterSettings, "Window Filter")
        
    def load(self, thePhrase):
        self.abbrSettings.load(thePhrase)
        self.hotKeySettings.load(thePhrase)
        self.windowFilterSettings.load(thePhrase)
        
    def set_dirty(self):
        self.settingsPane.set_dirty(True)
        
    def save(self, thePhrase):
        self.abbrSettings.save(thePhrase)
        self.hotKeySettings.save(thePhrase)
        self.windowFilterSettings.save(thePhrase)
        
    def validate(self, targetPhrase):
        if not self.abbrSettings.validate(targetPhrase): return False
        if not self.hotKeySettings.validate(targetPhrase): return False
        if not self.windowFilterSettings.validate(): return False
        return True
    
    def add_page(self, page, pageTitle):
        alignment = gtk.Alignment(xscale=1.0)
        alignment.set_padding(5, 5, 5, 5)
        alignment.add(page)
        self.append_page(alignment, gtk.Label(pageTitle))
        
        
class FolderSettingsNotebook(SettingsNotebook):
    
    def __init__(self, configWindow, settingsPane):
        gtk.Notebook.__init__(self)
        self.settingsPane = settingsPane
        self.abbrSettings = FolderAbbreviationSettings(configWindow, self)
        self.hotKeySettings = HotkeySettings(configWindow, self)
        self.windowFilterSettings = WindowFilterSettings(configWindow, self)
        self.add_page(self.abbrSettings, "Abbreviation")
        self.add_page(self.hotKeySettings, "Hotkey")
        self.add_page(self.windowFilterSettings, "Window Filter")
                

class AbbreviationSettings(gtk.VBox):
    
    def __init__(self, configWindow, noteBook):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow
        self.noteBook = noteBook

        self.useAbbr = gtk.CheckButton("Use an abbreviation")
        self.useAbbr.connect("toggled", self.on_useAbbr_toggled)
        self.useAbbr.connect("toggled", self.on_modified)            
        self.pack_start(self.useAbbr, False)
        
        self.pack_start(gtk.HSeparator(), False, False, 5)
        
        self.abbrText = gtk.Entry(10)
        self.abbrText.connect("changed", self.on_modified)
        hBox = gtk.HBox()
        hBox.pack_start(gtk.Label("Abbreviation "), False)
        hBox.pack_start(self.abbrText, False)
        self.pack_start(hBox, False)
        
        self.removeTyped = self._addCheckButton("Remove typed abbreviation")
        self.removeTyped.connect("toggled", self.on_modified)
        
        self.omitTrigger = self._addCheckButton("Omit trigger character")
        self.omitTrigger.connect("toggled", self.on_modified)
        
        self.matchCase = self._addCheckButton("Match phrase case to typed abbreviation")
        self.matchCase.connect("toggled", self.on_match_case_toggled)
        self.matchCase.connect("toggled", self.on_modified)
        
        self.ignoreCase = self._addCheckButton("Ignore case of typed abbreviation")
        self.ignoreCase.connect("toggled", self.on_ignore_case_toggled)
        self.ignoreCase.connect("toggled", self.on_modified)
        
        self.triggerInside = self._addCheckButton("Trigger when typed as part of a word")
        self.triggerInside.connect("toggled", self.on_modified)
        
        self.immediate = self._addCheckButton("Trigger immediately (don't require a trigger character)")
        self.immediate.connect("toggled", self.on_immediate_toggled)
        self.immediate.connect("toggled", self.on_modified)
        
        self.wordChars = gtk.combo_box_entry_new_text()
        model = self.wordChars.get_model()
        for key in WORD_CHAR_OPTIONS_ORDERED:
            model.append([key])
        self.wordChars.set_active(0)
        self.wordChars.connect("changed", self.on_modified)
        
        hBox = gtk.HBox()
        hBox.pack_start(gtk.Label("Word Characters "), False)
        hBox.pack_start(self.wordChars, False)
        #hBox.set_child_packing()
        self.pack_start(hBox, False, False, 5)
        
        self.useAbbr.emit("toggled")
        
    def load(self, thePhrase):
        
        if thePhrase.abbreviation is not None:
            self.abbrText.set_text(thePhrase.abbreviation)
        else:
            self.abbrText.set_text("")
        self.removeTyped.set_active(thePhrase.backspace)
        self.omitTrigger.set_active(thePhrase.omitTrigger)
        self.matchCase.set_active(thePhrase.matchCase)
        self.ignoreCase.set_active(thePhrase.ignoreCase)
        self.triggerInside.set_active(thePhrase.triggerInside)
        self.immediate.set_active(thePhrase.immediate)
        self._setWordCharRegex(thePhrase.get_word_chars())
        
        self.useAbbr.set_active(phrase.PhraseMode.ABBREVIATION in thePhrase.modes)
        
    def save(self, thePhrase):
        if self.useAbbr.get_active():
            thePhrase.modes.append(phrase.PhraseMode.ABBREVIATION) 
            thePhrase.abbreviation = self.abbrText.get_text()
            thePhrase.backspace = self.removeTyped.get_active()
            thePhrase.omitTrigger = self.omitTrigger.get_active()
            thePhrase.matchCase = self.matchCase.get_active()
            thePhrase.ignoreCase = self.ignoreCase.get_active()
            thePhrase.triggerInside = self.triggerInside.get_active()
            thePhrase.immediate = self.immediate.get_active()
            thePhrase.set_word_chars(self._getWordCharRegex())            
        
    def on_useAbbr_toggled(self, widget, data=None):
        self.foreach(lambda x: x.set_sensitive(widget.get_active()))
        widget.set_sensitive(True)
        self.abbrText.grab_focus()
        
    def on_match_case_toggled(self, widget, data=None):
        if widget.get_active():
            self.ignoreCase.set_active(True)
            
    def on_ignore_case_toggled(self, widget, data=None):
        if not widget.get_active():
            self.matchCase.set_active(False)
            
    def on_immediate_toggled(self, widget, data=None):
        if widget.get_active():
            self.omitTrigger.set_active(False)
            self.omitTrigger.set_sensitive(False)
        else:
            self.omitTrigger.set_sensitive(True)
            
    def on_modified(self, widget, data=None):
        self.noteBook.set_dirty()

    def _addCheckButton(self, label):
        checkButton = gtk.CheckButton(label)
        self.pack_start(checkButton, False)
        return checkButton
    
    def _getWordCharRegex(self):
        text = self.wordChars.child.get_text()
        if text in WORD_CHAR_OPTIONS_ORDERED:
            return WORD_CHAR_OPTIONS[text]
        else:
            return text
    
    def _setWordCharRegex(self, regex):
        matched = False

        for key, value in WORD_CHAR_OPTIONS.iteritems():
            if value == regex:
                matched = True
                self.wordChars.set_active(WORD_CHAR_OPTIONS_ORDERED.index(key))
                
        if not matched:
            self.wordChars.child.set_text(regex)
            
    def validate(self, targetPhrase):
        if self.useAbbr.get_active():
            configManager = self.configWindow.app.service.configManager
            abbrText = self.abbrText.get_text() 
            if not validate(configManager.check_abbreviation_unique(abbrText, targetPhrase),
                             "The abbreviation is already in use.\nAbbreviations must be unique.", self.abbrText,
                             self.configWindow): return False
            
            if not validate(not EMPTY_FIELD_REGEX.match(abbrText), "Abbreviation can not be empty.",
                             self.abbrText, self.configWindow): return False
            
            if not validate(not EMPTY_FIELD_REGEX.match(self._getWordCharRegex()), "Invalid word characters expression.",
                             self.wordChars, self.configWindow): return False
        
        return True
            
            
class FolderAbbreviationSettings(AbbreviationSettings):
    
    def __init__(self, configWindow, noteBook):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow
        self.noteBook = noteBook

        self.useAbbr = gtk.CheckButton("Use an abbreviation")
        self.useAbbr.connect("toggled", self.on_useAbbr_toggled)
        self.useAbbr.connect("toggled", self.on_modified)
        self.pack_start(self.useAbbr, False)
        
        self.pack_start(gtk.HSeparator(), False, False, 5)
        
        self.abbrText = gtk.Entry(10)
        self.abbrText.connect("changed", self.on_modified)
        hBox = gtk.HBox()
        hBox.pack_start(gtk.Label("Abbreviation "), False)
        hBox.pack_start(self.abbrText, False)
        self.pack_start(hBox, False)
        
        self.removeTyped = self._addCheckButton("Remove typed abbreviation")
        self.removeTyped.connect("toggled", self.on_modified)
        self.triggerInside = self._addCheckButton("Trigger when typed as part of a word")
        self.triggerInside.connect("toggled", self.on_modified)
        self.immediate = self._addCheckButton("Trigger immediately (don't require a trigger character)")
        self.immediate.connect("toggled", self.on_modified)
        
        self.wordChars = gtk.combo_box_entry_new_text()
        model = self.wordChars.get_model()
        for key in WORD_CHAR_OPTIONS_ORDERED:
            model.append([key])
        self.wordChars.set_active(0)
        self.wordChars.connect("changed", self.on_modified)
        
        hBox = gtk.HBox()
        hBox.pack_start(gtk.Label("Word Characters "), False)
        hBox.pack_start(self.wordChars, False)
        self.pack_start(hBox, False, False, 5)
        
        self.useAbbr.emit("toggled")
        
    def load(self, theFolder):
        self.useAbbr.set_active(phrase.PhraseMode.ABBREVIATION in theFolder.modes)
        if theFolder.abbreviation is not None:
            self.abbrText.set_text(theFolder.abbreviation)
        else:
            self.abbrText.set_text("")
        self.removeTyped.set_active(theFolder.backspace)
        self.triggerInside.set_active(theFolder.triggerInside)
        self.immediate.set_active(theFolder.immediate)
        self._setWordCharRegex(theFolder.get_word_chars())                
        
    def save(self, theFolder):
        if self.useAbbr.get_active():
            theFolder.modes.append(phrase.PhraseMode.ABBREVIATION) 
            theFolder.abbreviation = self.abbrText.get_text()
            theFolder.backspace = self.removeTyped.get_active()
            theFolder.triggerInside = self.triggerInside.get_active()
            theFolder.immediate = self.immediate.get_active()
            theFolder.set_word_chars(self._getWordCharRegex())            
        
        
class HotkeySettings(gtk.VBox):
    
    KEY_MAP = {
               ' ' : "<space>",
               '\t' : "<tab>",
               '\b' : "<backspace>",
               '\n' : "<enter>" 
               }
    
    REVERSE_KEY_MAP = {}
    
    def __init__(self, configWindow, noteBook, title="Use a hotkey"):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow
        self.noteBook = noteBook
        for key, value in self.KEY_MAP.iteritems():
            self.REVERSE_KEY_MAP[value] = key
            
        self.useHotkey = gtk.CheckButton(title)
        self.useHotkey.connect("toggled", self.on_useHotkey_toggled)
        self.useHotkey.connect("toggled", self.on_modified)
        self.pack_start(self.useHotkey, False, False, 5)
        
        self.pack_start(gtk.HSeparator(), False)
        
        hBox = gtk.HButtonBox()
        hBox.set_layout(gtk.BUTTONBOX_START)
        self.pack_start(hBox, False, False, 5)
        
        self.control = gtk.ToggleButton("Control")
        self.control.connect("toggled", self.on_modified)
        hBox.pack_start(self.control)
        self.alt = gtk.ToggleButton("Alt")
        self.alt.connect("toggled", self.on_modified)
        hBox.pack_start(self.alt)
        self.shift = gtk.ToggleButton("Shift")
        self.shift.connect("toggled", self.on_modified)
        hBox.pack_start(self.shift)
        self.super = gtk.ToggleButton("Super")
        self.super.connect("toggled", self.on_modified)
        hBox.pack_start(self.super)
        
        self.keyLabel = gtk.Label("None")
        hBox.pack_start(self.keyLabel)
        
        self.setKey = gtk.Button("Set key")
        self.setKey.connect("clicked", self.on_set_key)
        hBox.pack_start(self.setKey)
        
        self.useHotkey.emit("toggled")

    def load(self, thePhrase):
        self.useHotkey.set_active(phrase.PhraseMode.HOTKEY in thePhrase.modes)
        self.control.set_active(iomediator.Key.CONTROL in thePhrase.modifiers)
        self.alt.set_active(iomediator.Key.ALT in thePhrase.modifiers)
        self.shift.set_active(iomediator.Key.SHIFT in thePhrase.modifiers)
        self.super.set_active(iomediator.Key.SUPER in thePhrase.modifiers)

        key = str(thePhrase.hotKey)
        if key in self.KEY_MAP:
            keyText = self.KEY_MAP[key]
        else:
            keyText = key
        self.keyLabel.set_label(keyText)

        
    def save(self, thePhrase):
        if self.useHotkey.get_active():
            thePhrase.modes.append(phrase.PhraseMode.HOTKEY)
            
            # Build modifier list
            modifiers = self._buildModifiers()
                
            keyText = self.keyLabel.get_label()
            if keyText in self.REVERSE_KEY_MAP:
                key = self.REVERSE_KEY_MAP[keyText]
            else:
                key = keyText
                
            thePhrase.set_hotkey(modifiers, key)
        
    def on_useHotkey_toggled(self, widget, data=None):
        self.foreach(lambda x: x.set_sensitive(widget.get_active()))
        widget.set_sensitive(True)
        
    def on_set_key(self, widget, data=None):
        #dlg = KeyCaptureDialog(self)
        #dlg.start()
        self.keyLabel.set_label("Press a key")
        self.setKey.set_sensitive(False)
        self.grabber = KeyGrabber(self)
        self.grabber.start()
        

    def on_modified(self, widget, data=None):
        self.noteBook.set_dirty()
        
    def set_key(self, key):
        if self.KEY_MAP.has_key(key):
            key = self.KEY_MAP[key]
        self.keyLabel.set_label(key)
        self.setKey.set_sensitive(True)
        self.noteBook.set_dirty()

    def validate(self, targetPhrase):
        if self.useHotkey.get_active():
            modifiers = self._buildModifiers()
            keyText = self.keyLabel.get_label()
            configManager = self.configWindow.app.service.configManager
            
            if not validate(configManager.check_hotkey_unique(modifiers, keyText, targetPhrase),
                             "The hotkey is already in use.\nHotkeys must be unique.", None,
                             self.configWindow): return False

            if not validate(keyText != "None", "You must specify a key for the Hotkey.", None,
                             self.configWindow): return False
            
            if not validate(len(modifiers) > 0, "You must select at least one modifier for the Hotkey", None,
                             self.configWindow): return False
        
        return True
    
    def _buildModifiers(self):
        modifiers = []
        if self.control.get_active():
            modifiers.append(iomediator.Key.CONTROL) 
        if self.alt.get_active():
            modifiers.append(iomediator.Key.ALT)
        if self.shift.get_active():
            modifiers.append(iomediator.Key.SHIFT)
        if self.super.get_active():
            modifiers.append(iomediator.Key.SUPER)
        
        modifiers.sort()
        return modifiers
    

class GlobalHotkeySettings(HotkeySettings):

    def load(self, theHotkey):
        self.useHotkey.set_active(theHotkey.enabled)
        self.control.set_active(iomediator.Key.CONTROL in theHotkey.modifiers)
        self.alt.set_active(iomediator.Key.ALT in theHotkey.modifiers)
        self.shift.set_active(iomediator.Key.SHIFT in theHotkey.modifiers)
        self.super.set_active(iomediator.Key.SUPER in theHotkey.modifiers)

        key = str(theHotkey.hotKey)
        if key in self.KEY_MAP:
            keyText = self.KEY_MAP[key]
        else:
            keyText = key
        self.keyLabel.set_label(keyText)
    
    def save(self, theHotkey):        
        if self.useHotkey.get_active():
            theHotkey.enabled = True
            
            # Build modifier list
            modifiers = self._buildModifiers()
                
            keyText = self.keyLabel.get_label()
            if keyText in self.REVERSE_KEY_MAP:
                key = self.REVERSE_KEY_MAP[keyText]
            else:
                key = keyText
                
            theHotkey.set_hotkey(modifiers, key)
        else:
            theHotkey.enabled = False


class WindowFilterSettings(gtk.VBox):
    
    def __init__(self, configWindow, noteBook):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow
        self.noteBook = noteBook

        self.alwaysTrigger = gtk.CheckButton("Trigger in all windows")
        self.alwaysTrigger.connect("toggled", self.on_alwaysTrigger_toggled)
        self.alwaysTrigger.connect("toggled", self.on_modified)
        self.pack_start(self.alwaysTrigger, False)
        
        self.pack_start(gtk.HSeparator(), False, False, 5)
        
        label = gtk.Label("Trigger only in windows with title matching")
        label.set_alignment(0, 0.5)
        self.pack_start(label, False, False, 5)
        self.windowFilter = gtk.Entry()
        self.windowFilter.connect("changed", self.on_modified)
        self.pack_start(self.windowFilter, False)
        
    def load(self, thePhrase):
        self.alwaysTrigger.set_active(thePhrase.uses_default_filter())
        self.windowFilter.set_text(thePhrase.get_filter_regex())
        
    def save(self, thePhrase):
        if self.alwaysTrigger.get_active():
            thePhrase.set_window_titles(None)
        else:
            thePhrase.set_window_titles(self.windowFilter.get_text())
        
    def on_alwaysTrigger_toggled(self, widget, data=None):
        self.foreach(lambda x: x.set_sensitive(not widget.get_active()))
        widget.set_sensitive(True)
        self.windowFilter.grab_focus()
        
    def on_modified(self, widget, data=None):
        self.noteBook.set_dirty()
        
    def validate(self):
        if not self.alwaysTrigger.get_active():
            windowFilterText = self.windowFilter.get_text()
            if not validate(not EMPTY_FIELD_REGEX.match(windowFilterText), "Window filter expression can not be empty.",
                             self.windowFilter, self.configWindow):
                return False
            try:
                re.compile(windowFilterText, re.UNICODE)
            except Exception, e:
                return validate(False, "The expression you entered is not a valid regular expression.",
                                self.windowFilter, self.configWindow)
            
        return True


class KeyGrabber:
    
    def __init__(self, parent):
        self.targetParent = parent
        self.mediator = iomediator.IoMediator(self, iomediator.XLIB_INTERFACE)
    
    def start(self):
        self.mediator.initialise()
                 
    def handle_keypress(self, key, windowName=""):
        if not key in iomediator.MODIFIERS:
            self.mediator.shutdown()
            self.targetParent.set_key(key)
            
    def handle_hotkey(self, key, modifiers, windowName):
        pass
    
    def handle_mouseclick(self):
        pass    


class KeyCaptureDialog(gtk.Window):
    
    def __init__(self, parent):
        gtk.Window.__init__(self)
        self.set_title("Key selection")
        self.set_transient_for(parent.get_transient_for())
        vbox = gtk.VBox()
        vbox.add(gtk.Label("Press a key to use for the hotkey"))
        vbox.add(gtk.Entry())
        self.add(vbox)
        self.mediator = iomediator.IoMediator(self, iomediator.XLIB_INTERFACE)
        self.targetParent = parent
        self.show_all()
        self.set_size_request(200, 100)
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        
    def start(self):
        self.mediator.start()
        self.show()
                 
    def handle_keypress(self, key, windowName=""):
        if not key in iomediator.MODIFIERS:
            self.mediator.shutdown()
            self.hide()
            self.targetParent.set_key(key)
            
    def handle_hotkey(self, key, modifiers, windowName):
        pass
    
    def handle_mouseclick(self):
        pass
        
        
class PhraseTreeView(gtk.TreeView):
    
    def __init__(self, folders):
        gtk.TreeView.__init__(self)
        self.set_model(PhraseTreeModel(folders))
        self.set_headers_clickable(True)
        self.set_reorderable(False)
        
        # Treeview columns
        column = gtk.TreeViewColumn("Folders and Phrases")
        iconRenderer = gtk.CellRendererPixbuf()
        textRenderer = gtk.CellRendererText()
        column.pack_start(iconRenderer, False)
        column.pack_end(textRenderer, True)
        column.add_attribute(iconRenderer, "icon-name", 0)
        column.add_attribute(textRenderer, "text", 1)
        column.set_sort_column_id(1)
        column.set_sort_indicator(True)
        self.set_search_column(1)
        self.append_column(column)
        
        # Row double click event handler
        self.connect("row-activated", self.on_row_activated)
        
    def on_row_activated(self, widget, path, viewColumn, data=None):
        self.expand_row(path, False)
         

class PhraseTreeModel(gtk.TreeStore):
    
    OBJECT_COLUMN = 3
    
    def __init__(self, folders):
        gtk.TreeStore.__init__(self, str, str, str, object)
        
        for folder in folders.values():
            iter = self.append(None, folder.get_tuple())
            self.populate_store(iter, folder)
            
        self.folders = folders

    def populate_store(self, parent, parentFolder):
        for folder in parentFolder.folders:
            iter = self.append(parent, folder.get_tuple())
            self.populate_store(iter, folder)
        
        for phrase in parentFolder.phrases:
            self.append(parent, phrase.get_tuple())
            
    def append_item(self, item, parentIter):
        if parentIter is None:
            self.folders[item.title] = item
            return self.append(None, item.get_tuple())
        
        else:
            parentFolder = self.get_value(parentIter, self.OBJECT_COLUMN)
            if isinstance(item, phrase.PhraseFolder):
                parentFolder.add_folder(item)
            else:
                parentFolder.add_phrase(item)
            
            return self.append(parentIter, item.get_tuple())
            
    def remove_item(self, iter):
        item = self.get_value(iter, self.OBJECT_COLUMN)
        if item.parent is None:
            del self.folders[item.title]
        else:
            if isinstance(item, phrase.PhraseFolder):
                item.parent.remove_folder(item)
            else:
                item.parent.remove_phrase(item)
            
        self.remove(iter)
        
    def update_item(self, targetIter, item):
        itemTuple = item.get_tuple()
        updateList = []
        for n in range(len(itemTuple)):
            updateList.append(n)
            updateList.append(itemTuple[n])
        #print repr(updateList)
        self.set(targetIter, *updateList)

               
class Notifier(gobject.GObject):
    """
    Encapsulates all functionality related to the notification icon, notifications, and tray menu.
    """

    __gsignals__ = { "show-notify" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                      (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)) }
    
    def __init__(self, autokeyApp):
        gobject.GObject.__init__(self)
        pynotify.init("AutoKey")
        self.app = autokeyApp
        self.configManager = autokeyApp.service.configManager
        
        if ConfigurationManager.SETTINGS[SHOW_TRAY_ICON]:
            self.icon = gtk.status_icon_new_from_file(ICON_FILE)
            self.icon.set_tooltip("AutoKey")
            self.icon.connect("popup_menu", self.on_popup_menu)
            self.icon.connect("activate", self.on_activate)
            
            self.connect("show-notify", self.on_show_notify)  
            
    def show_notify(self, message, isError=False, details=''):
        if isError:
            self.emit("show-notify", message, details, gtk.STOCK_DIALOG_ERROR)
        else:
            self.emit("show-notify", message, details, gtk.STOCK_DIALOG_INFO)      
        
    # Signal Handlers ----
    
    def on_activate(self, widget, data=None):
        self.app.show_abbr_selector()
        
    def on_popup_menu(self, status_icon, button, activate_time, data=None):
        # Main Menu items
        enableMenuItem = gtk.CheckMenuItem("Enable Expansions")
        enableMenuItem.set_active(self.app.service.is_running())
        
        configureMenuItem = gtk.ImageMenuItem("Configure")
        configureMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_MENU))  
        
        removeMenuItem = gtk.ImageMenuItem("Remove icon")
        removeMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU))        
        
        quitMenuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
                
        # Menu signals
        enableMenuItem.connect("toggled", self.on_enable_toggled)
        configureMenuItem.connect("activate", self.on_show_configure)
        removeMenuItem.connect("activate", self.on_remove_icon)
        quitMenuItem.connect("activate", self.on_destroy_and_exit)
        
        # Get phrase folders to add to main menu
        folders = []
        phrases = []

        for folder in self.configManager.allFolders:
            if folder.showInTrayMenu:
                folders.append(folder)
        
        for phrase in self.configManager.allPhrases:
            if phrase.showInTrayMenu:
                phrases.append(phrase)
                    
        # Construct main menu
        menu = phrasemenu.PhraseMenu(self.app.service, folders, phrases, False)
        if len(phrases) > 0:
            menu.append(gtk.SeparatorMenuItem())
        menu.append(enableMenuItem)
        menu.append(configureMenuItem)
        menu.append(removeMenuItem)
        menu.append(quitMenuItem)
        menu.show_all()        
        menu.popup(None, None, None, button, activate_time)
        
    def on_enable_toggled(self, widget, data=None):
        if widget.active:
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_show_configure(self, widget, data=None):
        self.app.show_configure()
            
    def on_remove_icon(self, widget, data=None):
        self.icon.set_visible(False)
        ConfigurationManager.SETTINGS[SHOW_TRAY_ICON] = False
                
    def on_destroy_and_exit(self, widget, data=None):
        self.app.shutdown()
        gtk.main_quit()
        
    @gthreaded
    def on_show_notify(self, widget, message, details, iconName):
        n = pynotify.Notification("Autokey", message, iconName)
        n.set_urgency(pynotify.URGENCY_LOW)
        if ConfigurationManager.SETTINGS[SHOW_TRAY_ICON]:
            n.attach_to_status_icon(self.icon)
        if details != '':
            n.add_action("details", "Details", self.__notifyClicked, details)
        self.__n = n
        self.__details = details
        n.show()
                    
    # Utility methods ----
    
    @gthreaded
    def __notifyClicked(self, notification, action, details):
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
                                 message_format=details)
        dlg.run()
        dlg.destroy()
        
gobject.type_register(Notifier)

SELECTOR_DIALOG_TITLE = "Type an abbreviation"

class AbbreviationSelectorDialog(gtk.Dialog):
    
    def __init__(self, expansionService):
        gtk.Dialog.__init__(self, SELECTOR_DIALOG_TITLE)
        self.service = expansionService
        self.abbreviations = expansionService.configManager.abbrPhrases
        self.app = expansionService.app
        
        self.entry = gtk.Entry()
        self.entry.connect("activate", self.on_entry_activated)
        self.completion = gtk.EntryCompletion()
        self.entry.set_completion(self.completion)
        model = AbbreviationModel(self.abbreviations)
        self.completion.set_model(model)
        #self.completion.set_match_func(model.match)
        
        self.completion.set_text_column(0)
        
        #abbrCell = gtk.CellRendererText()
        #self.completion.pack_start(abbrCell)
        #self.completion.add_attribute(abbrCell, "text", 0)
        
        descriptionCell = gtk.CellRendererText()
        self.completion.pack_start(descriptionCell)
        self.completion.add_attribute(descriptionCell, "text", 1)
        
        self.completion.set_inline_completion(True)
        self.completion.set_inline_selection(True)
        self.completion.connect("match-selected", self.on_match_selected)
        
        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(20, 20, 50, 50)
        alignment.add(self.entry)
        self.vbox.add(alignment)
        
        self.show_all()
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.set_keep_above(True)
        self.set_focus_on_map(True)
        #self.set_has_separator(False)
        #self.set_title(SELECTOR_DIALOG_TITLE)
        
        self.connect("hide", self.on_close)        
        
    def on_match_selected(self, completion, model, iter, data=None):
        thePhrase = model.get_value(iter, AbbreviationModel.OBJECT_COLUMN)
        self.service.phrase_selected(None, thePhrase)
        self.hide()
        
    def on_entry_activated(self, widget, data=None):
        entered = self.entry.get_text()
        for thePhrase in self.abbreviations:
            if thePhrase.abbreviation == entered:
                self.service.phrase_selected(None, thePhrase)
        self.hide()
    
    def on_close(self, widget, data=None):
        self.destroy()
        self.app.abbrPopup = None
        

class AbbreviationModel(gtk.ListStore):
    
    OBJECT_COLUMN = 2
        
    def __init__(self, abbrPhrases):
        gtk.ListStore.__init__(self, str, str, object)
        
        for thePhrase in abbrPhrases:
            self.append((thePhrase.abbreviation, thePhrase.description, thePhrase))
            
    def match(self, completion, keyString, iter, data=None):
        abbreviation = self.get_value(iter, 0)
        description = self.get_value(iter, 1)
        if abbreviation.startswith(keyString):
            return True
        elif len(keyString) > 1:
            if keyString in description:
                return True

        return False