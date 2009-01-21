import gtk, gobject, pynotify, re
import phrase, phrasemenu, iomediator
from configurationmanager import *

UI_DESCRIPTION_FILE = "../../config/menus.xml"
ICON_FILE = "../../config/autokeyicon.svg"
CONFIG_WINDOW_TITLE = "AutoKey Configuration"

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
                   ("New Folder", gtk.STOCK_NEW, "New _Folder", "", "Create a new phrase folder", self.on_new_folder),
                   ("New Phrase", gtk.STOCK_NEW, "New _Phrase", "", "Create a new phrase", self.on_new_phrase),
                   ("Delete", gtk.STOCK_DELETE, "_Delete", None, "Delete the selected item", self.on_delete_item),
                   ("Import Settings", None, "_Import Settings", None, "Import settings from AutoKey 0.40", self.on_import_settings),                   
                   ("Close", gtk.STOCK_CLOSE, "_Close window", None, "Close the configuration window", self.on_close),
                   ("Quit", gtk.STOCK_QUIT, "_Quit AutoKey", None, "Completely exit AutoKey", self.on_destroy_and_exit ),
                   ("Settings", None, "_Settings", None, None, self.on_show_settings),
                   ("Help", None, "_Help"),
                   ("About", gtk.STOCK_ABOUT, "About AutoKey", None, "Show program information", self.on_show_about)
                   ]
        actionGroup.add_actions(actions)
        
        toggleActions = [
                         ("Enable Expansions", None, "_Enable Expansions", None, "Toggle expansions on/off", self.on_expansions_toggled)
                         ]
        actionGroup.add_toggle_actions(toggleActions)
                
        self.uiManager.insert_action_group(actionGroup, 0)
        self.uiManager.add_ui_from_file(UI_DESCRIPTION_FILE)        
        vbox.pack_start(self.uiManager.get_widget("/MenuBar"), False, False, 7)
        
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
        treeViewScrolledWindow.add(self.treeView)
        
        # Search expander
        expander = SearchExpander()
        treeViewVbox.pack_start(expander, False, False, 5)
        self.treeView.set_search_entry(expander.searchEntry)
        expander.searchColumnCombo.connect("changed", self.on_combo_selection_changed)
        
        self.add(vbox)
        self.connect("hide", self.on_close)
        self.show_all()
        self.treeView.get_selection().select_path(0)
        self.on_tree_selection_changed(self.treeView)
        
    def refresh_tree(self, item):
        self.app.service.configManager.config_altered()
        model, iter = self.treeView.get_selection().get_selected()
        model.update_item(iter, item)
        
    def on_show_file(self, widget, data=None):
        selection = self.__getTreeSelection()
        canCreate = isinstance(selection, phrase.PhraseFolder)
        self.uiManager.get_widget("/MenuBar/File/New Folder").set_sensitive(canCreate)
        self.uiManager.get_widget("/MenuBar/File/New Phrase").set_sensitive(canCreate)
        self.uiManager.get_widget("/MenuBar/File/Delete").set_sensitive(selection is not None)
        
    def on_show_settings(self, widget, data=None):
        self.toggleExpansionsMenuItem.set_active(ConfigurationManager.SETTINGS[SERVICE_RUNNING])
        
    def on_close(self, widget, data=None):
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
        
        else:    
            self.settingsBox.remove(child)
            self.settingsBox.add(gtk.Label(""))  
    
    def on_new_folder(self, widget, data=None):
        model, parentIter = self.treeView.get_selection().get_selected()
        parentFolder = self.__getTreeSelection()
        newFolder = phrase.PhraseFolder("New Folder")
        parentFolder.add_folder(newFolder)
        newIter = model.append(parentIter, newFolder.get_tuple())
        self.treeView.expand_to_path(model.get_path(newIter))
        self.treeView.get_selection().select_iter(newIter)
        self.on_tree_selection_changed(self.treeView)
        
    def on_new_phrase(self, widget, data=None):
        model, parentIter = self.treeView.get_selection().get_selected()
        parentFolder = self.__getTreeSelection()
        newPhrase = phrase.Phrase("New Phrase", "Enter phrase contents")
        parentFolder.add_phrase(newPhrase)
        newIter = model.append(parentIter, newPhrase.get_tuple())
        self.treeView.expand_to_path(model.get_path(newIter))
        self.treeView.get_selection().select_iter(newIter)
        self.on_tree_selection_changed(self.treeView)        
        
    def on_delete_item(self, widget, data=None):
        selection = self.treeView.get_selection()
        model, item = selection.get_selected()
        
        # Prompt for removal of a folder with phrases
        if model.iter_n_children(item) > 0:
            dlg = gtk.MessageDialog(self, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                    "Are you sure you want to delete this folder and all the phrases in it?")
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
            dlg.destroy()
            try:
                folder, phrases = self.app.service.configManager.import_legacy_settings(fileName)
            except ImportException, ie:
                self.app.show_error_dialog("Unable to import the configuration file:\n" + str(ie))
            else:
                model = self.treeView.get_model()
                
                iter = model.append_item(folder, None)
                for phrase in phrases:
                    model.append_item(phrase, iter)

        
        self.app.service.configManager.config_altered()
        
    def on_expansions_toggled(self, widget, data=None):
        if self.toggleExpansionsMenuItem.active:
            self.app.unpause_service()
        else:
            self.app.pause_service()        

    def on_show_about(self, widget, data=None):        
        dlg = gtk.AboutDialog()
        dlg.set_name("AutoKey")
        dlg.set_comments("A text expansion and hotkey utility for Linux\nAutoKey has saved you %d keystrokes" % 
                         ConfigurationManager.SETTINGS[INPUT_SAVINGS])
        dlg.set_version("0.50.0")
        p = gtk.gdk.pixbuf_new_from_file(ICON_FILE)
        dlg.set_logo(p)
        dlg.run()
        dlg.destroy()
        
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


class PhraseFolderSettings(gtk.VBox):
    
    def __init__(self, configWindow):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow
                
        label = gtk.Label("Folder Title")
        label.set_alignment(0, 0.5)
        self.pack_start(label, False)
        
        self.folderTitle = gtk.Entry(50)
        self.pack_start(self.folderTitle, False)
        
        self.showInTray = gtk.CheckButton("Show in tray menu")
        self.pack_start(self.showInTray, False)
        
        self.settingsNoteBook = FolderSettingsNotebook(configWindow)
        self.pack_start(self.settingsNoteBook, False, True, 5)
        
        self.pack_start(gtk.Label(""))
        
        buttonBox = gtk.HButtonBox()
        saveButton = gtk.Button("Save", gtk.STOCK_SAVE)
        saveButton.connect("clicked", self.on_save)
        revertButton = gtk.Button("Revert", gtk.STOCK_REVERT_TO_SAVED)
        revertButton.connect("clicked", self.on_revert)
        buttonBox.pack_end(saveButton)
        buttonBox.pack_end(revertButton)
        buttonBox.set_layout(gtk.BUTTONBOX_END)
        self.pack_start(buttonBox, False, False, 5)
        
        self.show_all()
        
    def load(self, theFolder):
        self.currentFolder = theFolder
        self.folderTitle.set_text(theFolder.title)
        self.showInTray.set_active(theFolder.showInTrayMenu)
        self.settingsNoteBook.load(theFolder)
        self.folderTitle.grab_focus()
        
    def on_save(self, widget, data=None):
        if self.validate():
            self.currentFolder.title = self.folderTitle.get_text()
            self.currentFolder.set_modes([])
            self.currentFolder.showInTrayMenu = self.showInTray.get_active()
            self.settingsNoteBook.save(self.currentFolder)
            self.configWindow.refresh_tree(self.currentFolder)
        
    def on_revert(self, widget, data=None):
        self.load(self.currentFolder)

    def validate(self):
        if not validate(not EMPTY_FIELD_REGEX.match(self.folderTitle.get_text()), "Folder title can not be empty",
                         self.folderTitle, self.configWindow):
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
        self.pack_start(self.predictive, False)
        self.promptBefore = gtk.CheckButton("Always prompt before pasting this phrase")
        self.pack_start(self.promptBefore, False)
        self.showInTray = gtk.CheckButton("Show in tray menu")
        self.pack_start(self.showInTray, False)
        
        self.settingsNoteBook = SettingsNotebook(configWindow)        
        self.pack_start(self.settingsNoteBook, False, True, 5)
        
        buttonBox = gtk.HButtonBox()
        saveButton = gtk.Button("Save", gtk.STOCK_SAVE)
        saveButton.connect("clicked", self.on_save)
        revertButton = gtk.Button("Revert", gtk.STOCK_REVERT_TO_SAVED)
        revertButton.connect("clicked", self.on_revert)
        buttonBox.pack_end(saveButton)
        buttonBox.pack_end(revertButton)
        buttonBox.set_layout(gtk.BUTTONBOX_END)
        self.pack_start(buttonBox, False, False, 5)
        
        self.show_all()
        
    def load(self, thePhrase):
        self.currentPhrase = thePhrase
        self.phraseDescription.set_text(thePhrase.description)
        buffer = gtk.TextBuffer()
        buffer.set_text(thePhrase.phrase)
        self.phraseContents.set_buffer(buffer)
        self.predictive.set_active(phrase.PhraseMode.PREDICTIVE in thePhrase.modes)
        self.promptBefore.set_active(thePhrase.prompt)
        self.showInTray.set_active(thePhrase.showInTrayMenu)
        self.settingsNoteBook.load(thePhrase)
        self.phraseDescription.grab_focus()
        
    def on_save(self, widget, data=None):
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
        
    def on_revert(self, widget, data=None):
        self.load(self.currentPhrase)
        
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
    
    def __init__(self, configWindow):
        gtk.Notebook.__init__(self)
        self.abbrSettings = AbbreviationSettings(configWindow)
        self.hotKeySettings = HotkeySettings(configWindow)
        self.windowFilterSettings = WindowFilterSettings(configWindow)   
        self.add_page(self.abbrSettings, "Abbreviation")
        self.add_page(self.hotKeySettings, "Hotkey")
        self.add_page(self.windowFilterSettings, "Window Filter")
        
    def load(self, thePhrase):
        self.abbrSettings.load(thePhrase)
        self.hotKeySettings.load(thePhrase)
        self.windowFilterSettings.load(thePhrase)
        
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
    
    def __init__(self, configWindow):
        gtk.Notebook.__init__(self)
        self.abbrSettings = FolderAbbreviationSettings(configWindow)
        self.hotKeySettings = HotkeySettings(configWindow)
        self.windowFilterSettings = WindowFilterSettings(configWindow)   
        self.add_page(self.abbrSettings, "Abbreviation")
        self.add_page(self.hotKeySettings, "Hotkey")
        self.add_page(self.windowFilterSettings, "Window Filter")
                

class AbbreviationSettings(gtk.VBox):
    
    def __init__(self, configWindow):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow

        self.useAbbr = gtk.CheckButton("Use an abbreviation")
        self.useAbbr.connect("toggled", self.on_useAbbr_toggled)        
        self.pack_start(self.useAbbr, False)
        
        self.pack_start(gtk.HSeparator(), False, False, 5)
        
        self.abbrText = gtk.Entry(10)
        hBox = gtk.HBox()
        hBox.pack_start(gtk.Label("Abbreviation "), False)
        hBox.pack_start(self.abbrText, False)
        self.pack_start(hBox, False)
        
        self.removeTyped = self._addCheckButton("Remove typed abbreviation")
        self.omitTrigger = self._addCheckButton("Omit trigger character")
        self.matchCase = self._addCheckButton("Match phrase case to typed abbreviation")
        self.matchCase.connect("toggled", self.on_match_case_toggled)
        self.ignoreCase = self._addCheckButton("Ignore case of typed abbreviation")
        self.ignoreCase.connect("toggled", self.on_ignore_case_toggled)
        self.triggerInside = self._addCheckButton("Trigger when typed as part of a word")
        self.immediate = self._addCheckButton("Trigger immediately (don't require a trigger character)")
        self.immediate.connect("toggled", self.on_immediate_toggled)
        
        self.wordChars = gtk.combo_box_entry_new_text()
        model = self.wordChars.get_model()
        for key in WORD_CHAR_OPTIONS_ORDERED:
            model.append([key])
        self.wordChars.set_active(0)
        
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
    
    def __init__(self, configWindow):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow

        self.useAbbr = gtk.CheckButton("Use an abbreviation")
        self.useAbbr.connect("toggled", self.on_useAbbr_toggled)
        self.pack_start(self.useAbbr, False)
        
        self.pack_start(gtk.HSeparator(), False, False, 5)
        
        self.abbrText = gtk.Entry(10)
        hBox = gtk.HBox()
        hBox.pack_start(gtk.Label("Abbreviation "), False)
        hBox.pack_start(self.abbrText, False)
        self.pack_start(hBox, False)
        
        self.removeTyped = self._addCheckButton("Remove typed abbreviation")
        self.triggerInside = self._addCheckButton("Trigger when typed as part of a word")
        self.immediate = self._addCheckButton("Trigger immediately (don't require a trigger character)")
        
        self.wordChars = gtk.combo_box_entry_new_text()
        model = self.wordChars.get_model()
        for key in WORD_CHAR_OPTIONS_ORDERED:
            model.append([key])
        self.wordChars.set_active(0)
        
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
    
    def __init__(self, configWindow):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow
        for key, value in self.KEY_MAP.iteritems():
            self.REVERSE_KEY_MAP[value] = key
            
        self.useHotkey = gtk.CheckButton("Use a hotkey")
        self.useHotkey.connect("toggled", self.on_useHotkey_toggled)
        self.pack_start(self.useHotkey, False, False, 5)
        
        self.pack_start(gtk.HSeparator(), False)
        
        hBox = gtk.HButtonBox()
        hBox.set_layout(gtk.BUTTONBOX_START)
        self.pack_start(hBox, False, False, 5)
        
        self.control = gtk.ToggleButton("Control")
        hBox.pack_start(self.control)
        self.alt = gtk.ToggleButton("Alt")
        hBox.pack_start(self.alt)
        self.shift = gtk.ToggleButton("Shift")
        hBox.pack_start(self.shift)
        self.super = gtk.ToggleButton("Super")
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
        self.keyLabel.set_label(str(thePhrase.hotKey))
        
        
    def save(self, thePhrase):
        if self.useHotkey.get_active():
            thePhrase.modes.append(phrase.PhraseMode.HOTKEY)
            
            # Build modifier list
            modifiers = self.__buildModifiers()
                
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
        dlg = KeyCaptureDialog(self)
        dlg.start()
        
    def set_key(self, key):
        if key in self.KEY_MAP.keys():
            key = self.KEY_MAP[key]
        self.keyLabel.set_label(key)

    def validate(self, targetPhrase):
        if self.useHotkey.get_active():
            modifiers = self.__buildModifiers()
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
    
    def __buildModifiers(self):
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
        

class WindowFilterSettings(gtk.VBox):
    
    def __init__(self, configWindow):
        gtk.VBox.__init__(self)
        self.configWindow = configWindow

        self.alwaysTrigger = gtk.CheckButton("Trigger in all windows")
        self.alwaysTrigger.connect("toggled", self.on_alwaysTrigger_toggled)
        self.pack_start(self.alwaysTrigger, False)
        
        self.pack_start(gtk.HSeparator(), False, False, 5)
        
        label = gtk.Label("Trigger only in windows with title matching")
        label.set_alignment(0, 0.5)
        self.pack_start(label, False, False, 5)
        self.windowFilter = gtk.Entry()
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
        
    def validate(self):
        if not self.alwaysTrigger.get_active():
            return validate(not EMPTY_FIELD_REGEX.match(self.windowFilter.get_text()), "Window filter expression can not be empty.",
                             self.windowFilter, self.configWindow)
        return True
        
class KeyCaptureDialog(gtk.Window):
    
    def __init__(self, parent):
        gtk.Window.__init__(self)
        self.set_title("Key selection")
        vbox = gtk.VBox()
        vbox.add(gtk.Label("Press a key to use for the hotkey"))
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
        self.set_reorderable(True)
        
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
         

class PhraseTreeModel(gtk.TreeStore):
    
    OBJECT_COLUMN = 3
    
    def __init__(self, folders):
        gtk.TreeStore.__init__(self, str, str, str, object)
        
        for folder in folders.values():
            iter = self.append(None, folder.get_tuple())
            self.__buildTreeStore(iter, folder)
            
        self.folders = folders

    def __buildTreeStore(self, parent, parentFolder):
        for folder in parentFolder.folders:
            iter = self.append(parent, folder.get_tuple())
            self.__buildTreeStore(iter, folder)
        
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
            
            self.connect("show-notify", self.on_show_notify)  
            
    def show_notify(self, message, isError=False, details=''):
        if isError:
            self.emit("show-notify", message, details, gtk.STOCK_DIALOG_ERROR)
        else:
            self.emit("show-notify", message, details, gtk.STOCK_DIALOG_INFO)      
        
    # Signal Handlers ----
        
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
        # This doesn't seem to work at all. Bug in pynotify???

        n.show()
                    
    # Utility methods ----
    
    def __notifyClicked(self, notification, action, details):
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
                                 message_format=details)
        dlg.connect("close", lambda x: x.destroy())
        dlg.show()
        
gobject.type_register(Notifier)                

class FolderChoiceDialog(gtk.Dialog):
    # TODO Probably not going to use this
    
    def __init__(self, parent, forFolder=True):
        """
        @param parent: parent window of the dialog
        @param forFolder: whether the choice is for a folder or a phrase
        """
        gtk.Dialog.__init__(self, "Choose a folder", parent, gtk.DIALOG_MODAL,
                             (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        configManager = parent.app.service.configManager
        self.combo = gtk.combo_box_new_text()
        if forFolder:
            self.combo.append_text("(Root)")
        for folder in configManager.allFolders:
            self.combo.append_text(folder.title)
        self.combo.set_active(0)
        
        if forFolder:
            self.vbox.pack_start(gtk.Label("Create new folder under"))
        else:
            self.vbox.pack_start(gtk.Label("Create new phrase under"))
        self.vbox.pack_start(self.combo, padding=10)
        self.show_all()
        
    def get_choice(self):
        return self.combo.get_active_text()