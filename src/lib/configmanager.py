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

import os, os.path, shutil, logging, pickle, glob, threading
import iomediator, interface, common, monitor

try:
    import json
    l = json.load
except:
    import simplejson as json

_logger = logging.getLogger("config-manager")

CONFIG_DIR = os.path.expanduser("~/.config/autokey")
CONFIG_FILE = os.path.join(CONFIG_DIR, "autokey.json")
CONFIG_DEFAULT_FOLDER = os.path.join(CONFIG_DIR, "data")
CONFIG_FILE_BACKUP = CONFIG_FILE + '~'

DEFAULT_ABBR_FOLDER = "Imported Abbreviations"
RECENT_ENTRIES_FOLDER = "Recently Typed"

IS_FIRST_RUN = "isFirstRun"
SERVICE_RUNNING = "serviceRunning"
MENU_TAKES_FOCUS = "menuTakesFocus"
SHOW_TRAY_ICON = "showTrayIcon"
SORT_BY_USAGE_COUNT = "sortByUsageCount"
#DETECT_UNWANTED_ABBR = "detectUnwanted"
PROMPT_TO_SAVE = "promptToSave"
#PREDICTIVE_LENGTH = "predictiveLength"
INPUT_SAVINGS = "inputSavings"
ENABLE_QT4_WORKAROUND = "enableQT4Workaround"
INTERFACE_TYPE = "interfaceType"
UNDO_USING_BACKSPACE = "undoUsingBackspace"
WINDOW_DEFAULT_SIZE = "windowDefaultSize"
HPANE_POSITION = "hPanePosition"
COLUMN_WIDTHS = "columnWidths"
SHOW_TOOLBAR = "showToolbar"
NOTIFICATION_ICON = "notificationIcon"
WORKAROUND_APP_REGEX = "workAroundApps"

# TODO - Future functionality
#TRACK_RECENT_ENTRY = "trackRecentEntry"
#RECENT_ENTRY_COUNT = "recentEntryCount"
#RECENT_ENTRY_MINLENGTH = "recentEntryMinLength"
#RECENT_ENTRY_SUGGEST = "recentEntrySuggest"

def get_config_manager(autoKeyApp, hadError=False):
    if not os.path.exists(CONFIG_DEFAULT_FOLDER):
        os.mkdir(CONFIG_DEFAULT_FOLDER)

    try:
        configManager = ConfigManager(autoKeyApp)
    except Exception, e:
        if hadError or not os.path.exists(CONFIG_FILE_BACKUP) or not os.path.exists(CONFIG_FILE):
            _logger.error("Error while loading configuration. Cannot recover.")
            raise

        _logger.exception("Error while loading configuration. Backup has been restored.")
        os.remove(CONFIG_FILE)
        shutil.copy2(CONFIG_FILE_BACKUP, CONFIG_FILE)
        return get_config_manager(autoKeyApp, True)
    
    _logger.debug("Global settings: %r", ConfigManager.SETTINGS)
    return configManager

def save_config(configManager):
    _logger.info("Persisting configuration")
    configManager.app.monitor.suspend() 
    # Back up configuration if it exists
    if os.path.exists(CONFIG_FILE):
        _logger.info("Backing up existing config file")
        shutil.copy2(CONFIG_FILE, CONFIG_FILE_BACKUP)
    try:
        outFile = open(CONFIG_FILE, "w")
        json.dump(configManager.get_serializable(), outFile, indent=4)
        _logger.info("Finished persisting configuration - no errors")
    except Exception, e:
        if os.path.exists(CONFIG_FILE_BACKUP):
            shutil.copy2(CONFIG_FILE_BACKUP, CONFIG_FILE)
        _logger.exception("Error while saving configuration. Backup has been restored (if found).")
        raise Exception("Error while saving configuration. Backup has been restored (if found).")
    finally:
        outFile.close()
        configManager.app.monitor.unsuspend() 
        
def apply_settings(settings):
    """
    Allows new settings to be added without users having to lose all their configuration
    """
    for key, value in settings.iteritems():
        ConfigManager.SETTINGS[key] = value
        
def _chooseInterface():
    # Choose a sensible default interface type. Get Xorg version to determine this:
    try:
        f = open("/var/log/Xorg.0.log", "r")
        for x in range(2):
            versionLine = f.readline()
            if "X Server" in versionLine:
                break
        f.close()
        versionLine = versionLine.strip()
        version = versionLine.split(" ")[-1]
        majorVersion, minorVersion, release = [int(i) for i in version.split(".")]
    except:
        minorVersion = None
        release = None
        
    if minorVersion is None:
        return iomediator.X_EVDEV_INTERFACE
    elif interface.HAS_RECORD:
        if minorVersion < 6:
            return iomediator.X_RECORD_INTERFACE
        elif minorVersion == 7 and release > 5:
            return iomediator.X_RECORD_INTERFACE
        elif minorVersion > 7:
            return iomediator.X_RECORD_INTERFACE
        
    
    return iomediator.X_EVDEV_INTERFACE

def convert_v07_to_v08(configData):
    oldVersion = configData["version"]
    os.rename(CONFIG_FILE, CONFIG_FILE + oldVersion)
    _logger.info("Converting v%s configuration data to v0.80.0", oldVersion)
    for folderData in configData["folders"]:
        _convertFolder(folderData, None)
        
    configData["folders"] = []
    configData["version"] = common.VERSION
    configData["settings"][NOTIFICATION_ICON] = common.ICON_FILE

    # Remove old backup file so we never retry the conversion
    if os.path.exists(CONFIG_FILE_BACKUP):
        os.remove(CONFIG_FILE_BACKUP)
    
    _logger.info("Conversion succeeded")
    import gtk
    dlg = gtk.MessageDialog(buttons=gtk.BUTTONS_OK, message_format=_("Configuration upgrade completed"))
    dlg.format_secondary_text(_("Your configuration data has been upgraded. It \
is recommended that you check everything is in order.\n\nYour original configuration\
 has been saved as %s%s") % (CONFIG_FILE, oldVersion))
    dlg.run()
    dlg.destroy()
        
        
def _convertFolder(folderData, parent):
    f = Folder("")
    f.inject_json_data(folderData)
    f.parent = parent
    f.persist()    
    
    for subfolder in folderData["folders"]:
        _convertFolder(subfolder, f)
    
    for itemData in folderData["items"]:
        i = None
        if itemData["type"] == "script":
            i = Script("", "")
            i.code = itemData["code"]
        elif itemData["type"] == "phrase":
            i = Phrase("", "")
            i.phrase = itemData["phrase"]
        
        if i is not None:
            i.inject_json_data(itemData)
            i.parent = f
            i.persist()

class ConfigManager:
    """
    Contains all application configuration, and provides methods for updating and 
    maintaining consistency of the configuration. 
    """

    """
    Static member for global application settings.
    """
    
    CLASS_VERSION = common.VERSION
    
    SETTINGS = {
                IS_FIRST_RUN : True,
                SERVICE_RUNNING : True,
                MENU_TAKES_FOCUS : False,
                SHOW_TRAY_ICON : True,
                SORT_BY_USAGE_COUNT : True,
                #DETECT_UNWANTED_ABBR : False,
                PROMPT_TO_SAVE: True,
                #PREDICTIVE_LENGTH : 5,
                ENABLE_QT4_WORKAROUND : False,
                INTERFACE_TYPE : _chooseInterface(),
                UNDO_USING_BACKSPACE : True,
                WINDOW_DEFAULT_SIZE : (600, 400),
                HPANE_POSITION : 150,
                COLUMN_WIDTHS : [150, 50, 100],
                SHOW_TOOLBAR : True,
                NOTIFICATION_ICON : common.ICON_FILE,
                WORKAROUND_APP_REGEX : ".*VirtualBox.*"
                # TODO - Future functionality
                #TRACK_RECENT_ENTRY : True,
                #RECENT_ENTRY_COUNT : 5,
                #RECENT_ENTRY_MINLENGTH : 10,
                #RECENT_ENTRY_SUGGEST : True
                }
                
    def __init__(self, app):
        """
        Create initial default configuration
        """ 
        self.VERSION = self.__class__.CLASS_VERSION
        self.lock = threading.Lock()
        
        self.app = app
        self.folders = []
        self.userCodeDir = None
        
        self.configHotkey = GlobalHotkey()
        self.configHotkey.set_hotkey(["<super>"], "k")
        self.configHotkey.enabled = True
        
        self.toggleServiceHotkey = GlobalHotkey()
        self.toggleServiceHotkey.set_hotkey(["<super>", "<shift>"], "k")
        self.toggleServiceHotkey.enabled = True    
        
        self.showPopupHotkey = GlobalHotkey()
        self.showPopupHotkey.enabled = False
        
        app.init_global_hotkeys(self)        
        
        self.load_global_config()
                
        self.app.monitor.add_watch(CONFIG_DEFAULT_FOLDER)
        self.app.monitor.add_watch(CONFIG_DIR)
        
        if self.folders:
            return
    
        # --- Code below here only executed if no persisted config data provided
        
        _logger.info("No configuration found - creating new one")       
        
        myPhrases = Folder(u"My Phrases")
        myPhrases.set_hotkey(["<ctrl>"], "<f7>")
        myPhrases.set_modes([TriggerMode.HOTKEY])
        myPhrases.persist()
        
        f = Folder(u"Addresses")
        adr = Phrase(u"Home Address", u"22 Avenue Street\nBrisbane\nQLD\n4000")
        adr.set_modes([TriggerMode.ABBREVIATION])
        adr.set_abbreviation(u"adr")
        f.add_item(adr)
        myPhrases.add_folder(f)        
        f.persist()
        adr.persist()

        p = Phrase(u"First phrase", u"Test phrase number one!")
        p.set_modes([TriggerMode.PREDICTIVE])
        p.set_window_titles(".* - gedit")
        myPhrases.add_item(p)
        
        myPhrases.add_item(Phrase(u"Second phrase", u"Test phrase number two!"))
        myPhrases.add_item(Phrase(u"Third phrase", u"Test phrase number three!"))
        self.folders.append(myPhrases)
        [p.persist() for p in myPhrases.items]
        
        sampleScripts = Folder(u"Sample Scripts")
        sampleScripts.persist()
        dte = Script("Insert Date", "")
        dte.code = """output = system.exec_command("date")
keyboard.send_keys(output)"""
        sampleScripts.add_item(dte)
        
        lMenu = Script("List Menu", "")
        lMenu.code = """choices = ["something", "something else", "a third thing"]

retCode, choice = dialog.list_menu(choices)
if retCode == 0:
    keyboard.send_keys("You chose " + choice)"""
        sampleScripts.add_item(lMenu)
        
        sel = Script("Selection Test", "")
        sel.code = """text = clipboard.get_selection()
keyboard.send_key("<delete>")
keyboard.send_keys("The text %s was here previously" % text)"""
        sampleScripts.add_item(sel)
        
        abbrc = Script("Abbreviation from selection", "")
        abbrc.code = """import time
time.sleep(0.25)
contents = clipboard.get_selection()
retCode, abbr = dialog.input_dialog("New Abbreviation", "Choose an abbreviation for the new phrase")
if retCode == 0:
    if len(contents) > 20:
        title = contents[0:17] + "..."
    else:
        title = contents
    folder = engine.get_folder("My Phrases")
    engine.create_abbreviation(folder, title, abbr, contents)"""
        sampleScripts.add_item(abbrc)
        
        phrasec = Script("Phrase from selection", "")
        phrasec.code = """import time
time.sleep(0.25)
contents = clipboard.get_selection()
if len(contents) > 20:
    title = contents[0:17] + "..."
else:
    title = contents
folder = engine.get_folder("My Phrases")
engine.create_phrase(folder, title, contents)"""
        sampleScripts.add_item(phrasec)
        
        self.folders.append(sampleScripts)
        [s.persist() for s in sampleScripts.items]

        # TODO - future functionality
        self.recentEntries = []
        
        self.config_altered(True)

    def get_serializable(self):
        extraFolders = []
        for folder in self.folders:
            if not folder.path.startswith(CONFIG_DEFAULT_FOLDER):
                extraFolders.append(folder.path)
        
        d = {
            "version": self.VERSION,
            "userCodeDir": self.userCodeDir,
            "settings": ConfigManager.SETTINGS,
            "folders": extraFolders,
            "showPopupHotkey": self.showPopupHotkey.get_serializable(),
            "toggleServiceHotkey": self.toggleServiceHotkey.get_serializable(),
            "configHotkey": self.configHotkey.get_serializable()
            }
        return d

    def load_global_config(self):
        if os.path.exists(CONFIG_FILE):
            _logger.info("Loading config from existing file: " + CONFIG_FILE)
            
            with open(CONFIG_FILE, 'r') as pFile:
                data = json.load(pFile)
                version = data["version"]
                
            if version < "0.80.0":
                try:
                    convert_v07_to_v08(data)
                    self.config_altered(True)
                except Exception, e:
                    _logger.exception("Problem occurred during conversion.")
                    _logger.error("Existing config file has been saved as %s%s",
                                  CONFIG_FILE, version)
                    raise
                
            self.VERSION = data["version"]
            self.userCodeDir = data["userCodeDir"]
            apply_settings(data["settings"])
            
            self.workAroundApps = re.compile(self.SETTINGS[WORKAROUND_APP_REGEX])
            
            for entryPath in glob.glob(CONFIG_DEFAULT_FOLDER + "/*"):
                if os.path.isdir(entryPath):
                    _logger.debug("Loading folder at '%s'", entryPath)
                    f = Folder("", path=entryPath)
                    f.load(None)
                    self.folders.append(f)

            for folderPath in data["folders"]:
                f = Folder("", path=folderPath)
                f.load()
                self.folders.append(f)

            self.showPopupHotkey.load_from_serialized(data["showPopupHotkey"])
            self.toggleServiceHotkey.load_from_serialized(data["toggleServiceHotkey"])
            self.configHotkey.load_from_serialized(data["configHotkey"])
            
            if self.VERSION < self.CLASS_VERSION:
                self.upgrade()

            self.config_altered(False)
            _logger.info("Successfully loaded configuration")
            
    def __checkExisting(self, path):
        # Check if we already know about the path, and return object if found
        for item in self.allItems:
            if item.path == path:
                return item
        
        return None
    
    def __checkExistingFolder(self, path):
        for folder in self.allFolders:
            if folder.path == path:
                return folder
        
        return None
            
    def path_created_or_modified(self, path):
        directory, baseName = os.path.split(path)
        loaded = False
        
        if path == CONFIG_FILE:
            self.reload_global_config()
            
        elif directory != CONFIG_DIR:  # ignore all other changes in top dir
            
            # --- handle directories added
            
            if os.path.isdir(path):
                f = Folder("", path=path)
                
                if directory == CONFIG_DEFAULT_FOLDER:
                    self.folders.append(f)
                    f.load()
                    loaded = True
                else:
                    folder = self.__checkExistingFolder(directory)
                    if folder is not None:
                        f.load(folder)
                        folder.add_folder(f)
                        loaded = True
            
            # -- handle txt or py files added or modified
            
            elif os.path.isfile(path):
                i = self.__checkExisting(path)
                isNew = False
                
                if i is None:
                    isNew = True
                    if baseName.endswith(".txt"):
                        i = Phrase("", "", path=path)
                    elif baseName.endswith(".py"):
                        i = Script("", "", path=path)       
                                 
                if i is not None:
                    folder = self.__checkExistingFolder(directory)
                    if folder is not None:
                        i.load(folder)
                        if isNew: folder.add_item(i)
                        loaded = True
                        
                # --- handle changes to folder settings
                            
                if baseName == ".folder.json":
                    folder = self.__checkExistingFolder(directory)
                    if folder is not None:
                        folder.load_from_serialized()
                        loaded = True
                        
                # --- handle changes to item settings
                
                if baseName.endswith(".json"):
                    for item in self.allItems:
                        if item.get_json_path() == path:
                            item.load_from_serialized()
                            loaded = True
                            
            if not loaded:
                _logger.warn("No action taken for create/update event at %s", path)
            else:
                self.config_altered(False)
            return loaded
        
    def path_removed(self, path):
        directory, baseName = os.path.split(path)
        deleted = False
        
        if directory == CONFIG_DIR: # ignore all deletions in top dir
            return 
        
        folder = self.__checkExistingFolder(path)
        item = self.__checkExisting(path)
        
        if folder is not None:
            if folder.parent is None:
                self.folders.remove(folder)
            else:
                folder.parent.remove_folder(folder)
            deleted = True
                
        elif item is not None:
            item.parent.remove_item(item)
            #item.remove_data()
            deleted = True
            
        if not deleted:
            _logger.warn("No action taken for delete event at %s", path)
        else:
            self.config_altered(False)
        return deleted
            
    def reload_global_config(self):
        _logger.info("Reloading global configuration")
        with open(CONFIG_FILE, 'r') as pFile:
            data = json.load(pFile)
    
        self.userCodeDir = data["userCodeDir"]
        apply_settings(data["settings"])
        
        existingPaths = []
        for folder in self.folders:
            if folder.parent is None and not folder.path.startswith(CONFIG_DEFAULT_FOLDER):
                existingPaths.append(folder.path)

        for folderPath in data["folders"]:
            if folderPath not in existingPaths:             
                f = Folder("", path=folderPath)
                f.load()
                self.folders.append(f)

        self.showPopupHotkey.load_from_serialized(data["showPopupHotkey"])
        self.toggleServiceHotkey.load_from_serialized(data["toggleServiceHotkey"])
        self.configHotkey.load_from_serialized(data["configHotkey"])

        self.config_altered(False)
        _logger.info("Successfully reloaded global configuration")
        
    def upgrade(self):
        _logger.info("Checking if upgrade is needed from version %s", self.VERSION)
        upgradeDone = False
        
        if self.VERSION < '0.70.0':
            _logger.info("Doing upgrade to 0.70.0")
            for item in self.allItems:
                if isinstance(item, Phrase):
                    item.sendMode = SendMode.KEYBOARD
            
        if upgradeDone:
            self.config_altered(True)
            
        self.VERSION = common.VERSION
            
    def config_altered(self, persistGlobal):
        """
        Called when some element of configuration has been altered, to update
        the lists of phrases/folders. 
        
        @param persist: save the global configuration at the end of the process
        """
        _logger.info("Configuration changed - rebuilding in-memory structures")
        
        self.lock.acquire()
        # Rebuild root folder list
        #rootFolders = self.folders
        #self.folders = []
        #for folder in rootFolders:
        #    self.folders.append(folder)
        
        self.hotKeyFolders = []
        self.hotKeys = []
        
        self.abbreviations = []
        
        self.allFolders = []
        self.allItems = []
        
        for folder in self.folders:
            if TriggerMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)
            
            if not self.app.monitor.has_watch(folder.path):
                self.app.monitor.add_watch(folder.path)
            
            self.__processFolder(folder)
        
        self.globalHotkeys = []
        self.globalHotkeys.append(self.configHotkey)
        self.globalHotkeys.append(self.toggleServiceHotkey)
        self.globalHotkeys.append(self.showPopupHotkey)        
        #_logger.debug("Global hotkeys: %s", self.globalHotkeys)
        
        #_logger.debug("Hotkey folders: %s", self.hotKeyFolders)
        #_logger.debug("Hotkey phrases: %s", self.hotKeys)
        #_logger.debug("Abbreviation phrases: %s", self.abbreviations)
        #_logger.debug("All folders: %s", self.allFolders)
        #_logger.debug("All phrases: %s", self.allItems)
        
        if persistGlobal:
            save_config(self)

        self.lock.release()
                    
    def __processFolder(self, parentFolder):        
        if not self.app.monitor.has_watch(parentFolder.path):
            self.app.monitor.add_watch(parentFolder.path)
        
        for folder in parentFolder.folders:
            if TriggerMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)
            
            if not self.app.monitor.has_watch(folder.path):
                self.app.monitor.add_watch(folder.path)
            
            self.__processFolder(folder)
            
        for item in parentFolder.items:
            if TriggerMode.HOTKEY in item.modes:
                self.hotKeys.append(item)
            if TriggerMode.ABBREVIATION in item.modes:
                self.abbreviations.append(item)
            self.allItems.append(item)
            
    # TODO Future functionality
    def add_recent_entry(self, entry):
        if not self.folders.has_key(RECENT_ENTRIES_FOLDER):
            folder = Folder(RECENT_ENTRIES_FOLDER)
            folder.set_hotkey(["<super>"], "<f7>")
            folder.set_modes([TriggerMode.HOTKEY])
            self.folders[RECENT_ENTRIES_FOLDER] = folder
            self.recentEntries = []
        
        folder = self.folders[RECENT_ENTRIES_FOLDER]
        
        
        if not entry in self.recentEntries:
            self.recentEntries.append(entry)
            while len(self.recentEntries) > self.SETTINGS[RECENT_ENTRY_COUNT]:
                self.recentEntries.pop(0)

            folder.items = []
            
            for theEntry in self.recentEntries:
                if len(theEntry) > 17:
                    description = theEntry[:17] + "..."
                else:
                    description = theEntry
            
                p = Phrase(description, theEntry)
                if self.SETTINGS[RECENT_ENTRY_SUGGEST]:
                    p.set_modes([TriggerMode.PREDICTIVE])
            
                folder.add_item(p)
                
            self.config_altered(False)
        
    def check_abbreviation_unique(self, abbreviation, targetItem):
        """
        Checks that the given abbreviation is not already in use.
        
        @param abbreviation: the abbreviation to check
        @param targetPhrase: the phrase for which the abbreviation to be used 
        """
        for item in self.allFolders:
            if TriggerMode.ABBREVIATION in item.modes:
                if item.abbreviation == abbreviation:
                    return item is targetItem, item.title
            
        for item in self.allItems:
            if TriggerMode.ABBREVIATION in item.modes:
                if item.abbreviation == abbreviation:
                    return item is targetItem, item.description

        return True, ""

    """def check_abbreviation_substring(self, abbreviation, targetItem):
        for item in self.allFolders:
            if TriggerMode.ABBREVIATION in item.modes:
                if abbreviation in item.abbreviation or item.abbreviation in abbreviation:
                    return item is targetItem, item.title       

        for item in self.allItems:
            if TriggerMode.ABBREVIATION in item.modes:
                if abbreviation in item.abbreviation or item.abbreviation in abbreviation:
                    return item is targetItem, item.description

        return True, ""

    def __checkSubstringAbbr(self, item1, item2, abbr):
        # Check if the given abbreviation is a substring match for the given item
        # If it is, check a few other rules to see if it matters
        print "substring check %s against %s" % (item.abbreviation, abbr)
        try:
            index = item.abbreviation.index(abbr)
            print index
            if index == 0 and len(abbr) < len(item.abbreviation):
                return item.immediate
            elif (index + len(abbr)) == len(item.abbreviation):
                return item.triggerInside
            elif len(abbr) != len(item.abbreviation):
                return item.triggerInside and item.immediate
            else:
                return False
        except ValueError:
            return False

    def __buildErrorMsg(self, conflictItem, msg):
        if isinstance(conflictItem, Folder):
            return msg % ("folder", conflictItem.title)
        elif isinstance(conflictItem, Phrase):
            return msg % ("phrase", conflictItem.description)
        else:
            return msg % ("script", conflictItem.description)"""
            
    def check_hotkey_unique(self, modifiers, hotKey, targetPhrase):
        """
        Checks that the given hotkey is not already in use. Also checks the 
        special hotkeys configured from the advanced settings dialog.
        
        @param modifiers: modifiers for the hotkey
        @param hotKey: the hotkey to check
        @param targetPhrase: the phrase for which the hotKey to be used        
        """
        for item in self.allFolders:
            if TriggerMode.HOTKEY in item.modes:
                if item.modifiers == modifiers and item.hotKey == hotKey:
                    return item is targetPhrase, item.title
            
        for item in self.allItems:
            if TriggerMode.HOTKEY in item.modes:
                if item.modifiers == modifiers and item.hotKey == hotKey:
                    return item is targetPhrase, item.description

        for item in self.globalHotkeys:
            if item.enabled:
                if item.modifiers == modifiers and item.hotKey == hotKey:
                    return item is targetPhrase, "a global hotkey"

        return True, ""
    
# This import placed here to prevent circular import conflicts
from model import *

class GlobalHotkey(AbstractHotkey):
    """
    A global application hotkey, configured from the advanced settings dialog.
    Allows a method call to be attached to the hotkey.
    """
    
    def __init__(self):
        AbstractHotkey.__init__(self)
        self.enabled = False
        self.windowTitleRegex = None

    def get_serializable(self):
        d = {
            "enabled": self.enabled
            }
        d.update(AbstractHotkey.get_serializable(self))
        return d

    def load_from_serialized(self, data):
        AbstractHotkey.load_from_serialized(self, data)
        self.enabled = data["enabled"]
    
    def set_closure(self, closure):
        """
        Set the callable to be executed when the hotkey is triggered.
        """
        self.closure = closure
        
    def check_hotkey(self, modifiers, key, windowTitle):
        if AbstractHotkey.check_hotkey(self, modifiers, key, windowTitle) and self.enabled:
            _logger.debug("Triggered global hotkey using modifiers: %r key: %r", modifiers, key)
            self.closure()
        return False

    def get_hotkey_string(self, key=None, modifiers=None):
        if key is None and modifiers is None:
            if not self.enabled:
                return ""

            key = self.hotKey
            modifiers = self.modifiers

        ret = ""

        for modifier in modifiers:
            ret += modifier
            ret += "+"

        if key == ' ':
            ret += "<space>"
        else:
            ret += key

        return ret
