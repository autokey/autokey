# -*- coding: utf-8 -*-

# Copyright (C) 2008 Chris Dekter

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

import os, os.path, shutil, logging, pickle
import iomediator

_logger = logging.getLogger("config-manager")

CONFIG_FILE = os.path.expanduser("~/.config/autokey/autokey.bin")
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
SHOW_TOOLBAR = "showToolbar"

# TODO - Future functionality
#TRACK_RECENT_ENTRY = "trackRecentEntry"
#RECENT_ENTRY_COUNT = "recentEntryCount"
#RECENT_ENTRY_MINLENGTH = "recentEntryMinLength"
#RECENT_ENTRY_SUGGEST = "recentEntrySuggest"

REPLACE_STRINGS = [("iautokey.configurationmanager", "iautokey.configmanager"),
                  ("ConfigurationManager", "ConfigManager"),
                  ("iautokey.phrase", "iautokey.model"),
                  ("PhraseFolder", "Folder"),
                  ("S'phrases'", "S'items'"),
                  ("S'allPhrases'", "S'allItems'"),
                  ("S'hotKeyPhrases'", "S'hotKeys'"),
                  ("S'abbrPhrases'", "S'abbreviations'")]

def get_config_manager(autoKeyApp, hadError=False):
    if os.path.exists(CONFIG_FILE):
        _logger.info("Loading config from existing file: " + CONFIG_FILE)
        pFile = open(CONFIG_FILE, 'rb')
        
        try:
            settings, configManager = pickle.load(pFile)
        except EOFError:
            if hadError:
                _logger.error("Error while loading configuration. Cannot recover.")
                raise
            
            _logger.error("Error while loading configuration. Backup has been restored.")
            os.remove(CONFIG_FILE)
            shutil.copy(CONFIG_FILE_BACKUP, CONFIG_FILE)
            return get_config_manager(autoKeyApp, True)
        except ImportError:
            pFile.close()
            upgrade_config_file()
            return get_config_manager(autoKeyApp)
        
        pFile.close()    
        apply_settings(settings)
        configManager.app = autoKeyApp
        
        autoKeyApp.init_global_hotkeys(configManager)
        
        _logger.info("Successfully loaded configuration file")
        _logger.debug("Global settings: %r", ConfigManager.SETTINGS)
        return configManager
    else:
        _logger.info("No configuration file found - creating new one")
        _logger.debug("Global settings: %r", ConfigManager.SETTINGS)
        return ConfigManager(autoKeyApp)

def save_config(configManager):
    _logger.info("Persisting configuration") 
    configManager.configHotkey.set_closure(None)
    configManager.toggleServiceHotkey.set_closure(None)

    autoKeyApp = configManager.app
    configManager.app = None

    # Back up configuration if it exists
    if os.path.exists(CONFIG_FILE):
        _logger.info("Backing up existing config file")
        shutil.copy(CONFIG_FILE, CONFIG_FILE_BACKUP)
    try:
        outFile = open(CONFIG_FILE, "wb")
        pickle.dump([ConfigManager.SETTINGS, configManager], outFile)
    except pickle.PickleError, pe:
        if os.path.exists(CONFIG_FILE_BACKUP):
            shutil.copy(CONFIG_FILE_BACKUP, CONFIG_FILE)
        _logger.exception("Error while saving configuration. Backup has been restored (if found).")
        raise Exception("Error while saving configuration. Backup has been restored (if found).")
    else:
        autoKeyApp.init_global_hotkeys(configManager)
        configManager.app = autoKeyApp
        _logger.info("Finished persisting configuration - no errors")
    finally:
        outFile.close()
        
def upgrade_config_file():
    """
    Upgrade a v0.5x config file to v0.6x
    """
    _logger.info("Upgrading v0.5x config file to v0.6x")
    shutil.move(CONFIG_FILE, CONFIG_FILE + "-0.5x")
    infile = open(CONFIG_FILE + "-0.5x", 'rb')
    outfile = open(CONFIG_FILE, 'wb')
    
    for line in infile:
        if len(line) > 5:
            for s, t in REPLACE_STRINGS:
                line = line.replace(s, t)
        outfile.write(line)
        
    infile.close()
    outfile.close()
    
    
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
        minorVersion = version.split(".")[1]
    except:
        minorVersion = None
        
    if minorVersion is None:
        return iomediator.X_EVDEV_INTERFACE
    elif minorVersion < 6:
        return iomediator.X_RECORD_INTERFACE
    else:
        return iomediator.X_EVDEV_INTERFACE

class ImportException(Exception):
    """
    Exception raised when an error occurs during the import of an abbreviations file.
    """
    pass
    

class ConfigManager:
    """
    Contains all application configuration, and provides methods for updating and 
    maintaining consistency of the configuration. 
    """

    """
    Static member for global application settings.
    """
    SETTINGS = {
                IS_FIRST_RUN : True,
                SERVICE_RUNNING : True,
                MENU_TAKES_FOCUS : False,
                SHOW_TRAY_ICON : True,
                SORT_BY_USAGE_COUNT : True,
                #DETECT_UNWANTED_ABBR : False,
                PROMPT_TO_SAVE: True,
                #PREDICTIVE_LENGTH : 5,
                INPUT_SAVINGS : 0,
                ENABLE_QT4_WORKAROUND : False,
                INTERFACE_TYPE : _chooseInterface(),
                UNDO_USING_BACKSPACE : True,
                WINDOW_DEFAULT_SIZE : (600, 400),
                HPANE_POSITION : 150,
                SHOW_TOOLBAR : True
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
        self.app = app
        self.folders = {}
        self.configHotkey = GlobalHotkey()
        self.configHotkey.set_hotkey(["<ctrl>"], "k")
        self.configHotkey.enabled = True
        
        self.toggleServiceHotkey = GlobalHotkey()
        self.toggleServiceHotkey.set_hotkey(["<ctrl>", "<shift>"], "k")
        self.toggleServiceHotkey.enabled = True    
        
        myPhrases = Folder(u"My Phrases")
        myPhrases.set_hotkey(["<ctrl>"], "<f7>")
        myPhrases.set_modes([TriggerMode.HOTKEY])
        
        f = Folder(u"Addresses")
        adr = Phrase(u"Home Address", u"22 Avenue Street\nBrisbane\nQLD\n4000")
        adr.set_modes([TriggerMode.ABBREVIATION])
        adr.set_abbreviation(u"adr")
        f.add_item(adr)
        myPhrases.add_folder(f)        

        p = Phrase(u"First phrase", u"Test phrase number one!")
        p.set_modes([TriggerMode.PREDICTIVE])
        p.set_window_titles(".* - gedit")
        myPhrases.add_item(p)
        
        myPhrases.add_item(Phrase(u"Second phrase", u"Test phrase number two!"))
        myPhrases.add_item(Phrase(u"Third phrase", u"Test phrase number three!"))
        self.folders[myPhrases.title] = myPhrases
        
        sampleScripts = Folder(u"Sample Scripts")
        dte = Script("Insert Date", "")
        dte.code = """output = system.exec_command("date")
keyboard.send_keys(output)"""
        sampleScripts.add_item(dte)
        
        lMenu = Script("List Menu", "")
        lMenu.code = """choices = ["something", "something else", "a third thing"]

retCode, choice = dialog.combo_menu(choices)
if retCode == 0:
    keyboard.send_keys("You chose " + choice)"""
        sampleScripts.add_item(lMenu)
        
        sel = Script("Selection Test", "")
        sel.code = """text = clipboard.get_selection()
keyboard.send_key("<delete>")
keyboard.send_keys("The text %s was here previously" % text)"""
        sampleScripts.add_item(sel)
        
        self.folders[sampleScripts.title] = sampleScripts
        
        # TODO - future functionality
        self.recentEntries = []
        
        self.config_altered()
            
    def config_altered(self):
        """
        Called when some element of configuration has been altered, to update
        the lists of phrases/folders. 
        """
        _logger.info("Configuration changed - rebuilding in-memory structures")
        # Rebuild root folder list
        rootFolders = self.folders.values()
        self.folders.clear()
        for folder in rootFolders:
            self.folders[folder.title] = folder
        
        self.hotKeyFolders = []
        self.hotKeys = []
        
        self.abbreviations = []
        
        self.allFolders = []
        self.allItems = []
        
        for folder in self.folders.values():
            if TriggerMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)
            
            self.__processFolder(folder)
        
        self.globalHotkeys = []
        self.globalHotkeys.append(self.configHotkey)
        self.globalHotkeys.append(self.toggleServiceHotkey)
        _logger.debug("Global hotkeys: %s", self.globalHotkeys)
        
        _logger.debug("Hotkey folders: %s", self.hotKeyFolders)
        _logger.debug("Hotkey phrases: %s", self.hotKeys)
        _logger.debug("Abbreviation phrases: %s", self.abbreviations)
        _logger.debug("All folders: %s", self.allFolders)
        _logger.debug("All phrases: %s", self.allItems)
        
        save_config(self)
                    
    def __processFolder(self, parentFolder):
        for folder in parentFolder.folders:
            if TriggerMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)
            
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
                
            self.config_altered()
        
    def import_legacy_settings(self, configFilePath):
        """
        Import an abbreviations settings file from v0.4x.x.
        
        @param configFilePath: full path to the abbreviations file
        """
        importer = LegacyImporter()
        importer.load_config(configFilePath)        
        folder = Folder(DEFAULT_ABBR_FOLDER)
        
        # Check phrases for unique abbreviations
        for phrase in importer.phrases:
            if not self.check_abbreviation_unique(phrase.abbreviation, phrase):
                raise ImportException("The abbreviation '" + phrase.abbreviation + "' is already in use.")
        return (folder, importer.phrases)
    
    def check_abbreviation_unique(self, abbreviation, targetPhrase):
        """
        Checks that the given abbreviation is not already in use.
        
        @param abbreviation: the abbreviation to check
        @param targetPhrase: the phrase for which the abbreviation to be used 
        """
        for item in self.allFolders:
            if TriggerMode.ABBREVIATION in item.modes:
                if item.abbreviation == abbreviation:
                    return item is targetPhrase
            
        for item in self.allItems:
            if TriggerMode.ABBREVIATION in item.modes:
                if item.abbreviation == abbreviation:
                    return item is targetPhrase
        
        return True
            
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
                    return item is targetPhrase
            
        for item in self.allItems:
            if TriggerMode.HOTKEY in item.modes:
                if item.modifiers == modifiers and item.hotKey == hotKey:
                    return item is targetPhrase     

        for item in self.globalHotkeys:
            if item.enabled:
                if item.modifiers == modifiers and item.hotKey == hotKey:
                    return False

        return True
    
# Legacy Importer ----

# Legacy configuration sections
CONFIG_SECTION = "config"
DEFAULTS_SECTION = "defaults"
ABBR_SECTION = "abbr"

# Legacy configuration parameters

WORD_CHARS_REGEX_OPTION = "wordchars"
IMMEDIATE_OPTION = "immediate"
IGNORE_CASE_OPTION = "ignorecase"
MATCH_CASE_OPTION = "matchcase"
BACKSPACE_OPTION = "backspace"
OMIT_TRIGGER_OPTION = "omittrigger"
TRIGGER_INSIDE_OPTION = "triggerinside"

ABBREVIATION_OPTIONS = [
                        WORD_CHARS_REGEX_OPTION,
                        IMMEDIATE_OPTION,
                        IGNORE_CASE_OPTION,
                        MATCH_CASE_OPTION,
                        BACKSPACE_OPTION,
                        OMIT_TRIGGER_OPTION,
                        TRIGGER_INSIDE_OPTION
                        ]

class LegacyImporter:
    
    def load_config(self, configFilePath):
        try:
            config = configobj.ConfigObj(configFilePath, list_values=False)
        except Exception, e:
            raise ImportException(str(e))
        abbrDefinitions = config[ABBR_SECTION]
        
        definitions = abbrDefinitions.keys()
        definitions.sort()        

        # Import default settings
        #defaultSettings = dict(p.items(DEFAULTS_SECTION))
        defaultSettings = config[DEFAULTS_SECTION]
        defaultSettings[WORD_CHARS_REGEX_OPTION] = re.compile(defaultSettings[WORD_CHARS_REGEX_OPTION], re.UNICODE)
        
        self.__applyBooleanOption(IMMEDIATE_OPTION, defaultSettings)        
        self.__applyBooleanOption(IGNORE_CASE_OPTION, defaultSettings)
        self.__applyBooleanOption(MATCH_CASE_OPTION, defaultSettings)   
        self.__applyBooleanOption(BACKSPACE_OPTION, defaultSettings)    
        self.__applyBooleanOption(OMIT_TRIGGER_OPTION, defaultSettings)
        self.__applyBooleanOption(TRIGGER_INSIDE_OPTION, defaultSettings)        
        
        # Import user-defined abbreviations as phrases        
        self.phrases = []
        
        while len(definitions) > 0:

            # Flush any unused options that weren't matched with an abbreviation definition
            while '.' in definitions[0]:
                isOption = False
                for option in ABBREVIATION_OPTIONS:
                    if definitions[0].endswith(option):
                        definitions.pop(0)
                        isOption = True
                        break

                if len(definitions) == 0:
                    break # leave the flushing loop if no definitions remaining
                if len(definitions) == 1 and not isOption:
                    break # leave the flushing loop if the last remaining definition is not an option
                    

            if len(definitions) > 0:
                self.phrases.append(self.__buildPhrase(definitions, abbrDefinitions, defaultSettings))                 

    def __buildPhrase(self, definitions, abbrDefinitions, defaults):
        """
        Create a new Phrase instance for the abbreviation definition at the start of the list
        
        @param definitions: list of definitions yet to be processed, with the abbreviation definition
        to be instantiated at the start of the list
        @param abbrDefinitions: dictionary of all abbreviation and config definitions
        """
        ownSettings = {}
        definition = definitions.pop(0)
        phraseText = abbrDefinitions[definition]
        startString = definition + '.'
        offset = len(startString)

        while len(definitions) > 0:
            key = definitions[0]
            if key.startswith(startString):
                ownSettings[key[offset:]] = abbrDefinitions[key]
                definitions.pop(0)
            else:
                # no more options for me - leave loop
                break
        
        if ownSettings.has_key(WORD_CHARS_REGEX_OPTION):
            ownSettings[WORD_CHARS_REGEX_OPTION] = re.compile(ownSettings[WORD_CHARS_REGEX_OPTION], re.UNICODE)
        
        self.__applyBooleanOption(IMMEDIATE_OPTION, ownSettings)        
        self.__applyBooleanOption(IGNORE_CASE_OPTION, ownSettings)
        self.__applyBooleanOption(MATCH_CASE_OPTION, ownSettings)   
        self.__applyBooleanOption(BACKSPACE_OPTION, ownSettings)    
        self.__applyBooleanOption(OMIT_TRIGGER_OPTION, ownSettings)
        self.__applyBooleanOption(TRIGGER_INSIDE_OPTION, ownSettings)
        
        #if result._getSetting(IGNORE_CASE_OPTION):
        #    result.abbreviation = result.abbreviation.lower()
        
        # Apply options to final phrase
        phraseDescription = phraseText[:20].replace('\n', ' ')
        result = Phrase(phraseDescription, phraseText)
        result.set_abbreviation(definition)
        result.set_modes([TriggerMode.ABBREVIATION])
        result.wordChars = self.__getDefaultOrCustom(defaults, ownSettings, WORD_CHARS_REGEX_OPTION)
        result.immediate = self.__getDefaultOrCustom(defaults, ownSettings, IMMEDIATE_OPTION)
        result.ignoreCase = self.__getDefaultOrCustom(defaults, ownSettings, IGNORE_CASE_OPTION)
        result.matchCase = self.__getDefaultOrCustom(defaults, ownSettings, MATCH_CASE_OPTION)
        result.backspace = self.__getDefaultOrCustom(defaults, ownSettings, BACKSPACE_OPTION)
        result.omitTrigger = self.__getDefaultOrCustom(defaults, ownSettings, OMIT_TRIGGER_OPTION)
        result.triggerInside = self.__getDefaultOrCustom(defaults, ownSettings, TRIGGER_INSIDE_OPTION)
        return result
            
    def __applyBooleanOption(self, optionName, settings):
        if settings.has_key(optionName):
            settings[optionName] = (settings[optionName].lower()[0] == 't')
            
    def __getDefaultOrCustom(self, defaults, ownSettings, optionName):
        if ownSettings.has_key(optionName):
            return ownSettings[optionName]
        else:
            return defaults[optionName]

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
    
    def set_closure(self, closure):
        """
        Set the callable to be executed when the hotkey is triggered.
        """
        self.closure = closure
        
    def check_hotkey(self, modifiers, key, windowTitle):
        if AbstractHotkey.check_hotkey(self, modifiers, key, windowTitle) and self.enabled:
            _logger.debug("Triggered global hotkey using modifiers: %s key: %s" % (repr(modifiers), key))
            self.closure()
        return False

