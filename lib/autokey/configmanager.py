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

import typing
import os
import os.path
import shutil
import logging
import glob
import threading
import re
from pathlib import Path

from autokey import common
from autokey.iomediator.constants import X_RECORD_INTERFACE, MODIFIERS
from autokey.iomediator import key

import json

_logger = logging.getLogger("config-manager")

CONFIG_FILE = os.path.join(common.CONFIG_DIR, "autokey.json")
CONFIG_DEFAULT_FOLDER = os.path.join(common.CONFIG_DIR, "data")
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
from .configmanager_constants import INTERFACE_TYPE
UNDO_USING_BACKSPACE = "undoUsingBackspace"
WINDOW_DEFAULT_SIZE = "windowDefaultSize"
HPANE_POSITION = "hPanePosition"
COLUMN_WIDTHS = "columnWidths"
SHOW_TOOLBAR = "showToolbar"
NOTIFICATION_ICON = "notificationIcon"
WORKAROUND_APP_REGEX = "workAroundApps"
DISABLED_MODIFIERS = "disabledModifiers"
# Added by Trey Blancher (ectospasm) 2015-09-16
TRIGGER_BY_INITIAL = "triggerItemByInitial"

SCRIPT_GLOBALS = "scriptGlobals"

# TODO - Future functionality
#TRACK_RECENT_ENTRY = "trackRecentEntry"
#RECENT_ENTRY_COUNT = "recentEntryCount"
#RECENT_ENTRY_MINLENGTH = "recentEntryMinLength"
#RECENT_ENTRY_SUGGEST = "recentEntrySuggest"

# Used to set or retrieve autostart related settings. These settings are separately handled by .desktop files in the
# user autostart directory in $XDG_DATA_HOME/autostart, typically ~/.local/share/autostart.
AutostartSettings = typing.NamedTuple("AutostartSettings", [
    ("desktop_file_name", typing.Optional[str]), ("switch_show_configure", bool)
])

def get_config_manager(autoKeyApp, hadError=False):
    if not os.path.exists(CONFIG_DEFAULT_FOLDER):
        os.mkdir(CONFIG_DEFAULT_FOLDER)

    try:
        configManager = ConfigManager(autoKeyApp)
    except Exception as e:
        if hadError or not os.path.exists(CONFIG_FILE_BACKUP) or not os.path.exists(CONFIG_FILE):
            _logger.exception("Error while loading configuration. Cannot recover.")
            raise

        _logger.exception("Error while loading configuration. Backup has been restored.")
        os.remove(CONFIG_FILE)
        shutil.copy2(CONFIG_FILE_BACKUP, CONFIG_FILE)
        return get_config_manager(autoKeyApp, True)
    
    _logger.debug("Global settings: %r", ConfigManager.SETTINGS)
    return configManager


def save_config(config_manager):
    _logger.info("Persisting configuration")
    config_manager.app.monitor.suspend()
    # Back up configuration if it exists
    # TODO: maybe use with-statement instead of try-except?
    if os.path.exists(CONFIG_FILE):
        _logger.info("Backing up existing config file")
        shutil.copy2(CONFIG_FILE, CONFIG_FILE_BACKUP)
    try:
        _persist_settings(config_manager)
        _logger.info("Finished persisting configuration - no errors")
    except Exception as e:
        if os.path.exists(CONFIG_FILE_BACKUP):
            shutil.copy2(CONFIG_FILE_BACKUP, CONFIG_FILE)
        _logger.exception("Error while saving configuration. Backup has been restored (if found).")
        raise Exception("Error while saving configuration. Backup has been restored (if found).")
    finally:
        config_manager.app.monitor.unsuspend()


def _persist_settings(config_manager):
    """
    Write the settings, including the persistent global script Store.
    The Store instance might contain arbitrary user data, like function objects, OpenCL contexts, or whatever other
    non-serializable objects, both as keys or values.
    Try to serialize the data, and if it fails, fall back to checking the store and removing all non-serializable
    data.
    """
    serializable_data = config_manager.get_serializable()
    try:
        _try_persist_settings(serializable_data)
    except (TypeError, ValueError):
        # The user added non-serializable data to the store, so remove all non-serializable keys or values.
        _remove_non_serializable_store_entries(serializable_data["settings"][SCRIPT_GLOBALS])
        _try_persist_settings(serializable_data)


def _try_persist_settings(serializable_data: dict):
    """
    Write the settings as JSON to the configuration file
    :raises TypeError: If the user tries to store non-serializable types
    :raises ValueError: If the user tries to store circular referenced (recursive) structures.
    """
    with open(CONFIG_FILE, "w") as json_file:
            json.dump(serializable_data, json_file, indent=4)


def _remove_non_serializable_store_entries(store: dict):
    """
    This function is called if there are non-serializable items in the global script storage.
    This function removes all such items.
    """
    removed_key_list = []
    for key, value in store.items():
        if not (_is_serializable(key) and _is_serializable(value)):
            _logger.info("Remove non-serializable item from the global script store. Key: '{}', Value: '{}'. "
                         "This item cannot be saved and therefore will be lost.".format(key, value))
            removed_key_list.append(key)
    for key in removed_key_list:
        del store[key]


def _is_serializable(data):
    """Check, if data is json serializable."""
    try:
        json.dumps(data)
    except (TypeError, ValueError):
        # TypeError occurs with non-serializable types (type, function, etc.)
        # ValueError occurs when circular references are found. Example: `l=[]; l.append(l)`
        return False
    else:
        return True


def get_autostart() -> AutostartSettings:
    """Returns the autostart settings as read from the system."""
    autostart_file = Path(common.AUTOSTART_DIR) / "autokey.desktop"
    if not autostart_file.exists():
        return AutostartSettings(None, False)
    else:
        return _extract_data_from_desktop_file(autostart_file)


def _extract_data_from_desktop_file(desktop_file: Path) -> AutostartSettings:
    with open(str(desktop_file), "r") as file:
        for line in file.readlines():
            line = line.rstrip("\n")
            if line.startswith("Exec="):
                program_name = line.split("=")[1].split(" ")[0]
                return AutostartSettings(program_name + ".desktop", line.endswith("-c"))
    raise ValueError("Autostart autokey.desktop file does not contain any Exec line. File: {}".format(desktop_file))


def set_autostart_entry(autostart_data: AutostartSettings):
    """
    Activates or deactivates autostarting autokey during user login.
    Autostart is handled by placing a .desktop file into '$XDG_CONFIG_HOME/autostart', typically '~/.config/autostart'
    """
    _logger.info("Save autostart settings: {}".format(autostart_data))
    autostart_file = Path(common.AUTOSTART_DIR) / "autokey.desktop"
    if autostart_data.desktop_file_name is None:  # Choosing None as the GUI signals deleting the entry.
        delete_autostart_entry()
    else:
        autostart_file.parent.mkdir(exist_ok=True)  # make sure that the parent autostart directory exists.
        _create_autostart_entry(autostart_data, autostart_file)


def _create_autostart_entry(autostart_data: AutostartSettings, autostart_file: Path):
    """Create an autostart .desktop file in the autostart directory, if possible."""
    try:
        source_desktop_file = get_source_desktop_file(autostart_data.desktop_file_name)
    except FileNotFoundError:
        _logger.exception("Failed to find a usable .desktop file! Unable to find: {}".format(
            autostart_data.desktop_file_name))
    else:
        _logger.debug("Found source desktop file that will be placed into the autostart directory: {}".format(
            source_desktop_file))
        with open(str(source_desktop_file), "r") as opened_source_desktop_file:
            desktop_file_content = opened_source_desktop_file.read()
        desktop_file_content = "\n".join(_manage_autostart_desktop_file_launch_flags(
            desktop_file_content, autostart_data.switch_show_configure
        )) + "\n"
        with open(str(autostart_file), "w", encoding="UTF-8") as opened_autostart_file:
            opened_autostart_file.write(desktop_file_content)
        _logger.debug("Written desktop file: {}".format(autostart_file))


def delete_autostart_entry():
    """Remove a present autostart entry. If none is found, nothing happens."""
    autostart_file = Path(common.AUTOSTART_DIR) / "autokey.desktop"
    if autostart_file.exists():
        autostart_file.unlink()
        _logger.info("Deleted old autostart entry: {}".format(autostart_file))


def get_source_desktop_file(desktop_file_name: str) -> Path:
    """
    Try to get the source .desktop file with the given name.
    :raises FileNotFoundError: If no desktop file was found in the searched directories.
    """
    possible_paths = (
        # Copy from local installation. Also used if the user explicitely customized the launcher .desktop file.
        Path(common.XDG_DATA_HOME) / "applications",
        # Copy from system-wide installation
        Path("/", "usr", "share", "applications"),
        # Copy from git source tree. This will probably not work when used, because the application won’t be in the PATH
        Path(__file__).parent.parent.parent / "config"
    )
    for possible_path in possible_paths:
        desktop_file = possible_path / desktop_file_name
        if desktop_file.exists():
            return desktop_file
    raise FileNotFoundError("Desktop file for autokey could not be found. Searched paths: {}".format(possible_paths))


def _manage_autostart_desktop_file_launch_flags(desktop_file_content: str, show_configure: bool) -> typing.Iterable[str]:
    """Iterate over the desktop file contents. Yields all lines except for the "Exec=" line verbatim. Modifies
    the Exec line to include the user desired command line switches (currently only one implemented)."""
    for line in desktop_file_content.splitlines(keepends=False):
        if line.startswith("Exec="):
            exec_line = _modify_exec_line(line, show_configure)
            _logger.info("Used 'Exec' line in desktop file: {}".format(exec_line))
            yield exec_line
        else:
            yield line


def _modify_exec_line(line: str, show_configure: bool) -> str:
    if show_configure:
        if line.endswith(" -c"):
            return line
        else:
            return line + " -c"
    else:
        if line.endswith(" -c"):
            return line[:-3]
        else:
            return line


def apply_settings(settings):
    """
    Allows new settings to be added without users having to lose all their configuration
    """
    for key, value in settings.items():
        ConfigManager.SETTINGS[key] = value


def convert_v07_to_v08(configData):
    oldVersion = configData["version"]
    os.rename(CONFIG_FILE, CONFIG_FILE + oldVersion)
    _logger.info("Converting v%s configuration data to v0.80.0", oldVersion)
    for folderData in configData["folders"]:
        _convertFolder(folderData, None)
        
    configData["folders"] = []
    configData["version"] = common.VERSION
    configData["settings"][NOTIFICATION_ICON] = common.ICON_FILE_NOTIFICATION

    # Remove old backup file so we never retry the conversion
    if os.path.exists(CONFIG_FILE_BACKUP):
        os.remove(CONFIG_FILE_BACKUP)
    
    _logger.info("Conversion succeeded")
        
        
def _convertFolder(folderData, parent):
    f = model.Folder("")
    f.inject_json_data(folderData)
    f.parent = parent
    f.persist()    
    
    for subfolder in folderData["folders"]:
        _convertFolder(subfolder, f)
    
    for itemData in folderData["items"]:
        i = None
        if itemData["type"] == "script":
            i = model.Script("", "")
            i.code = itemData["code"]
        elif itemData["type"] == "phrase":
            i = model.Phrase("", "")
            i.phrase = itemData["phrase"]
        
        if i is not None:
            i.inject_json_data(itemData)
            i.parent = f
            i.persist()


def convert_rename_autostart_entries_for_v0_95_3():
    """
    In versions <= 0.95.2, the autostart option in autokey-gtk copied the default autokey-gtk.desktop file into
    $XDG_CONFIG_DIR/autostart (with minor, unrelated modifications).
    For versions >= 0.95.3, the autostart file is renamed to autokey.desktop. In 0.95.3, the autostart functionality
    is implemented for autokey-qt. Thus, it becomes possible to have an autostart file for both GUIs in the autostart
    directory simultaneously. Because of the singleton nature of autokey, this becomes an issue and race-conditions
    determine which GUI starts first. To prevent this, both GUIs will share a single autokey.desktop autostart entry,
    allowing only one GUI to be started during login. This allows for much simpler code.
    """
    old_autostart_file = Path(common.AUTOSTART_DIR) / "autokey-gtk.desktop"
    if old_autostart_file.exists():
        new_file_name = Path(common.AUTOSTART_DIR) / "autokey.desktop"
        _logger.info("Migration task: Found old autostart entry: '{}'. Rename to: '{}'".format(
            old_autostart_file, new_file_name)
        )
        old_autostart_file.rename(new_file_name)


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
                IS_FIRST_RUN: True,
                SERVICE_RUNNING: True,
                MENU_TAKES_FOCUS: False,
                SHOW_TRAY_ICON: True,
                SORT_BY_USAGE_COUNT: True,
                #DETECT_UNWANTED_ABBR: False,
                PROMPT_TO_SAVE:False,
                #PREDICTIVE_LENGTH: 5,
                ENABLE_QT4_WORKAROUND: False,
                INTERFACE_TYPE: X_RECORD_INTERFACE,
                UNDO_USING_BACKSPACE: True,
                WINDOW_DEFAULT_SIZE: (600, 400),
                HPANE_POSITION: 150,
                COLUMN_WIDTHS: [150, 50, 100],
                SHOW_TOOLBAR: True,
                NOTIFICATION_ICON: common.ICON_FILE_NOTIFICATION,
                WORKAROUND_APP_REGEX: ".*VirtualBox.*|krdc.Krdc",
                TRIGGER_BY_INITIAL: False,
                DISABLED_MODIFIERS: [],
                # TODO - Future functionality
                #TRACK_RECENT_ENTRY: True,
                #RECENT_ENTRY_COUNT: 5,
                #RECENT_ENTRY_MINLENGTH: 10,
                #RECENT_ENTRY_SUGGEST: True
                SCRIPT_GLOBALS: {}
                }
                
    def __init__(self, app):
        """
        Create initial default configuration
        """ 
        self.VERSION = self.__class__.CLASS_VERSION
        self.lock = threading.Lock()
        
        self.app = app
        self.folders = []
        self.userCodeDir = None  # type: str
        
        self.configHotkey = GlobalHotkey()
        self.configHotkey.set_hotkey(["<super>"], "k")
        self.configHotkey.enabled = True
        
        self.toggleServiceHotkey = GlobalHotkey()
        self.toggleServiceHotkey.set_hotkey(["<super>", "<shift>"], "k")
        self.toggleServiceHotkey.enabled = True

        # Set the attribute to the default first. Without this, AK breaks, if started for the first time. See #274
        self.workAroundApps = re.compile(self.SETTINGS[WORKAROUND_APP_REGEX])

        app.init_global_hotkeys(self)

        self.load_global_config()
                
        self.app.monitor.add_watch(CONFIG_DEFAULT_FOLDER)
        self.app.monitor.add_watch(common.CONFIG_DIR)
        
        if self.folders:
            return
    
        # --- Code below here only executed if no persisted config data provided
        
        _logger.info("No configuration found - creating new one")       
        
        myPhrases = model.Folder("My Phrases")
        myPhrases.set_hotkey(["<ctrl>"], "<f7>")
        myPhrases.set_modes([model.TriggerMode.HOTKEY])
        myPhrases.persist()

        f = model.Folder("Addresses")
        adr = model.Phrase("Home Address", "22 Avenue Street\nBrisbane\nQLD\n4000")
        adr.set_modes([model.TriggerMode.ABBREVIATION])
        adr.add_abbreviation("adr")
        f.add_item(adr)
        myPhrases.add_folder(f)        
        f.persist()
        adr.persist()

        p = model.Phrase("First phrase", "Test phrase number one!")
        p.set_modes([model.TriggerMode.PREDICTIVE])
        p.set_window_titles(".* - gedit")
        myPhrases.add_item(p)
        
        myPhrases.add_item(model.Phrase("Second phrase", "Test phrase number two!"))
        myPhrases.add_item(model.Phrase("Third phrase", "Test phrase number three!"))
        self.folders.append(myPhrases)
        [p.persist() for p in myPhrases.items]
        
        sampleScripts = model.Folder("Sample Scripts")
        sampleScripts.persist()
        dte = model.Script("Insert Date", "")
        dte.code = """output = system.exec_command("date")
keyboard.send_keys(output)"""
        sampleScripts.add_item(dte)
        
        lMenu = model.Script("List Menu", "")
        lMenu.code = """choices = ["something", "something else", "a third thing"]

retCode, choice = dialog.list_menu(choices)
if retCode == 0:
    keyboard.send_keys("You chose " + choice)"""
        sampleScripts.add_item(lMenu)
        
        sel = model.Script("Selection Test", "")
        sel.code = """text = clipboard.get_selection()
keyboard.send_key("<delete>")
keyboard.send_keys("The text %s was here previously" % text)"""
        sampleScripts.add_item(sel)
        
        abbrc = model.Script("Abbreviation from selection", "")
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
        
        phrasec = model.Script("Phrase from selection", "")
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
        
        win = model.Script("Display window info", "")
        win.code = """# Displays the information of the next window to be left-clicked
import time
mouse.wait_for_click(1)
time.sleep(0.2)
winTitle = window.get_active_title()
winClass = window.get_active_class()
dialog.info_dialog("Window information", 
          "Active window information:\\nTitle: '%s'\\nClass: '%s'" % (winTitle, winClass))"""
        win.show_in_tray_menu = True
        sampleScripts.add_item(win)
        
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
                except Exception as e:
                    _logger.exception("Problem occurred during conversion.")
                    _logger.error("Existing config file has been saved as %s%s",
                                  CONFIG_FILE, version)
                    raise

            if version < "0.95.3":
                convert_rename_autostart_entries_for_v0_95_3()
                
            self.VERSION = data["version"]
            self.userCodeDir = data["userCodeDir"]
            apply_settings(data["settings"])
            self.load_disabled_modifiers()
            
            self.workAroundApps = re.compile(self.SETTINGS[WORKAROUND_APP_REGEX])
            
            for entryPath in glob.glob(CONFIG_DEFAULT_FOLDER + "/*"):
                if os.path.isdir(entryPath):
                    _logger.debug("Loading folder at '%s'", entryPath)
                    f = model.Folder("", path=entryPath)
                    f.load(None)
                    self.folders.append(f)

            for folderPath in data["folders"]:
                f = model.Folder("", path=folderPath)
                f.load()
                self.folders.append(f)

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
            
        elif directory != common.CONFIG_DIR:  # ignore all other changes in top dir
            
            # --- handle directories added
            
            if os.path.isdir(path):
                f = model.Folder("", path=path)
                
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
                        i = model.Phrase("", "", path=path)
                    elif baseName.endswith(".py"):
                        i = model.Script("", "", path=path)
                                 
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
                _logger.warning("No action taken for create/update event at %s", path)
            else:
                self.config_altered(False)
            return loaded
        
    def path_removed(self, path):
        directory, baseName = os.path.split(path)
        deleted = False
        
        if directory == common.CONFIG_DIR: # ignore all deletions in top dir
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
            _logger.warning("No action taken for delete event at %s", path)
        else:
            self.config_altered(False)
        return deleted

    def load_disabled_modifiers(self):
        """
        Load all disabled modifier keys from the configuration file. Called during startup, after the configuration
        is read into the SETTINGS dictionary.
        :return:
        """
        try:
            self.SETTINGS[DISABLED_MODIFIERS] = [key.Key(value) for value in self.SETTINGS[DISABLED_MODIFIERS]]
        except ValueError:
            _logger.error("Unknown value in the disabled modifier list found. Unexpected: {}".format(
                self.SETTINGS[DISABLED_MODIFIERS]))
            self.SETTINGS[DISABLED_MODIFIERS] = []

        for possible_modifier in self.SETTINGS[DISABLED_MODIFIERS]:
            self._check_if_modifier(possible_modifier)
            _logger.info("Disabling modifier key {} based on the stored configuration file.".format(possible_modifier))
            MODIFIERS.remove(possible_modifier)

    @staticmethod
    def is_modifier_disabled(modifier: key.Key) -> bool:
        """Checks, if the given modifier key is disabled. """
        ConfigManager._check_if_modifier(modifier)
        return modifier in ConfigManager.SETTINGS[DISABLED_MODIFIERS]

    @staticmethod
    def disable_modifier(modifier: typing.Union[key.Key, str]):
        """
        Permanently disable a modifier key. This can be used to disable unwanted modifier keys, like CAPSLOCK,
        if the user remapped the physical key to something else.
        :param modifier: Modifier key to disable.
        :return:
        """
        if isinstance(modifier, str):
            modifier = key.Key(modifier)
        ConfigManager._check_if_modifier(modifier)
        try:
            _logger.info("Disabling modifier key {} on user request.".format(modifier))
            MODIFIERS.remove(modifier)
        except ValueError:
            _logger.warning("Disabling already disabled modifier key. Affected key: {}".format(modifier))
        else:
            ConfigManager.SETTINGS[DISABLED_MODIFIERS].append(modifier)

    @staticmethod
    def enable_modifier(modifier: typing.Union[key.Key, str]):
        """
        Enable a previously disabled modifier key.
        :param modifier: Modifier key to re-enable
        :return:
        """
        if isinstance(modifier, str):
            modifier = key.Key(modifier)
        ConfigManager._check_if_modifier(modifier)
        if modifier not in MODIFIERS:
            _logger.info("Re-eabling modifier key {} on user request.".format(modifier))
            MODIFIERS.append(modifier)
            ConfigManager.SETTINGS[DISABLED_MODIFIERS].remove(modifier)
        else:
            _logger.warning("Enabling already enabled modifier key. Affected key: {}".format(modifier))

    @staticmethod
    def _check_if_modifier(modifier: key.Key):
        if not isinstance(modifier, key.Key):
            raise TypeError("The given value must be an AutoKey Key instance, got {}".format(type(modifier)))
        if not modifier in key._ALL_MODIFIERS_:
            raise ValueError("The given key '{}' is not a modifier. Expected one of {}.".format(
                modifier, key._ALL_MODIFIERS_))

    def reload_global_config(self):
        _logger.info("Reloading global configuration")
        with open(CONFIG_FILE, 'r') as pFile:
            data = json.load(pFile)
    
        self.userCodeDir = data["userCodeDir"]
        apply_settings(data["settings"])
        self.workAroundApps = re.compile(self.SETTINGS[WORKAROUND_APP_REGEX])
        
        existingPaths = []
        for folder in self.folders:
            if folder.parent is None and not folder.path.startswith(CONFIG_DEFAULT_FOLDER):
                existingPaths.append(folder.path)

        for folderPath in data["folders"]:
            if folderPath not in existingPaths:             
                f = model.Folder("", path=folderPath)
                f.load()
                self.folders.append(f)

        self.toggleServiceHotkey.load_from_serialized(data["toggleServiceHotkey"])
        self.configHotkey.load_from_serialized(data["configHotkey"])

        self.config_altered(False)
        _logger.info("Successfully reloaded global configuration")
        
    def upgrade(self):
        _logger.info("Checking if upgrade is needed from version %s", self.VERSION)
        
        # Always reset interface type when upgrading
        self.SETTINGS[INTERFACE_TYPE] = X_RECORD_INTERFACE
        _logger.info("Resetting interface type, new type: %s", self.SETTINGS[INTERFACE_TYPE])
        
        if self.VERSION < '0.70.0':
            _logger.info("Doing upgrade to 0.70.0")
            for item in self.allItems:
                if isinstance(item, model.Phrase):
                    item.sendMode = model.SendMode.KEYBOARD

        if self.VERSION < "0.82.3":
            self.SETTINGS[WORKAROUND_APP_REGEX] += "|krdc.Krdc"
            self.workAroundApps = re.compile(self.SETTINGS[WORKAROUND_APP_REGEX])
            self.SETTINGS[SCRIPT_GLOBALS] = {}
        
        self.VERSION = common.VERSION    
        self.config_altered(True)
            
    def config_altered(self, persistGlobal):
        """
        Called when some element of configuration has been altered, to update
        the lists of phrases/folders. 
        
        @param persistGlobal: save the global configuration at the end of the process
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
            if model.TriggerMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)
            
            if not self.app.monitor.has_watch(folder.path):
                self.app.monitor.add_watch(folder.path)
            
            self.__processFolder(folder)
        
        self.globalHotkeys = []
        self.globalHotkeys.append(self.configHotkey)
        self.globalHotkeys.append(self.toggleServiceHotkey)
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
            if model.TriggerMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)
            
            if not self.app.monitor.has_watch(folder.path):
                self.app.monitor.add_watch(folder.path)
            
            self.__processFolder(folder)
            
        for item in parentFolder.items:
            if model.TriggerMode.HOTKEY in item.modes:
                self.hotKeys.append(item)
            if model.TriggerMode.ABBREVIATION in item.modes:
                self.abbreviations.append(item)
            self.allItems.append(item)
            
    # TODO Future functionality
    def add_recent_entry(self, entry):
        if RECENT_ENTRIES_FOLDER not in self.folders:
            folder = model.Folder(RECENT_ENTRIES_FOLDER)
            folder.set_hotkey(["<super>"], "<f7>")
            folder.set_modes([model.TriggerMode.HOTKEY])
            self.folders[RECENT_ENTRIES_FOLDER] = folder
            self.recentEntries = []
        
        folder = self.folders[RECENT_ENTRIES_FOLDER]
        
        if entry not in self.recentEntries:
            self.recentEntries.append(entry)
            while len(self.recentEntries) > self.SETTINGS[RECENT_ENTRY_COUNT]:
                self.recentEntries.pop(0)

            folder.items = []
            
            for theEntry in self.recentEntries:
                if len(theEntry) > 17:
                    description = theEntry[:17] + "..."
                else:
                    description = theEntry
            
                p = model.Phrase(description, theEntry)
                if self.SETTINGS[RECENT_ENTRY_SUGGEST]:
                    p.set_modes([model.TriggerMode.PREDICTIVE])
            
                folder.add_item(p)
                
            self.config_altered(False)
        
    def check_abbreviation_unique(self, abbreviation, newFilterPattern, targetItem):
        """
        Checks that the given abbreviation is not already in use.
        
        @param abbreviation: the abbreviation to check
        @param newFilterPattern:
        @param targetItem: the phrase for which the abbreviation to be used 
        """
        for item in self.allFolders:
            if model.TriggerMode.ABBREVIATION in item.modes:
                if abbreviation in item.abbreviations and item.filter_matches(newFilterPattern):
                    return item is targetItem, item
            
        for item in self.allItems:
            if model.TriggerMode.ABBREVIATION in item.modes:
                if abbreviation in item.abbreviations and item.filter_matches(newFilterPattern):
                    return item is targetItem, item

        return True, None

    """def check_abbreviation_substring(self, abbreviation, targetItem):
        for item in self.allFolders:
            if model.TriggerMode.ABBREVIATION in item.modes:
                if abbreviation in item.abbreviation or item.abbreviation in abbreviation:
                    return item is targetItem, item.title       

        for item in self.allItems:
            if model.TriggerMode.ABBREVIATION in item.modes:
                if abbreviation in item.abbreviation or item.abbreviation in abbreviation:
                    return item is targetItem, item.description

        return True, ""

    def __checkSubstringAbbr(self, item1, item2, abbr):
        # Check if the given abbreviation is a substring match for the given item
        # If it is, check a few other rules to see if it matters
        print ("substring check {} against {}".format(item.abbreviation, abbr))
        try:
            index = item.abbreviation.index(abbr)
            print (index)
            if index == 0 and len(abbr) < len(item.abbreviation):
                return item.immediate
            elif (index + len(abbr)) == len(item.abbreviation):
                return item.triggerInside
            elif len(abbr) != len(item.abbreviation):
                return item.triggerInside and item.immediate
            else:
                return False
        except ValueError:
            return False"""
            
    def check_hotkey_unique(self, modifiers, hotKey, newFilterPattern, targetItem):
        """
        Checks that the given hotkey is not already in use. Also checks the 
        special hotkeys configured from the advanced settings dialog.
        
        @param modifiers: modifiers for the hotkey
        @param hotKey: the hotkey to check
        @param newFilterPattern:
        @param targetItem: the phrase for which the hotKey to be used        
        """
        for item in self.allFolders:
            if model.TriggerMode.HOTKEY in item.modes:
                if item.modifiers == modifiers and item.hotKey == hotKey and item.filter_matches(newFilterPattern):
                    return item is targetItem, item
            
        for item in self.allItems:
            if model.TriggerMode.HOTKEY in item.modes:
                if item.modifiers == modifiers and item.hotKey == hotKey and item.filter_matches(newFilterPattern):
                    return item is targetItem, item

        for item in self.globalHotkeys:
            if item.enabled:
                if item.modifiers == modifiers and item.hotKey == hotKey and item.filter_matches(newFilterPattern):
                    return item is targetItem, item

        return True, None
    
# This import placed here to prevent circular import conflicts
from . import model


class GlobalHotkey(model.AbstractHotkey):
    """
    A global application hotkey, configured from the advanced settings dialog.
    Allows a method call to be attached to the hotkey.
    """
    
    def __init__(self):
        model.AbstractHotkey.__init__(self)
        self.enabled = False
        self.windowInfoRegex = None
        self.isRecursive = False
        self.parent = None

    def get_serializable(self):
        d = {
            "enabled": self.enabled
            }
        d.update(model.AbstractHotkey.get_serializable(self))
        return d

    def load_from_serialized(self, data):
        model.AbstractHotkey.load_from_serialized(self, data)
        self.enabled = data["enabled"]
    
    def set_closure(self, closure):
        """
        Set the callable to be executed when the hotkey is triggered.
        """
        self.closure = closure
        
    def check_hotkey(self, modifiers, key, windowTitle):
        # TODO: Doesn’t this always return False? (as long as no exceptions are thrown)
        if model.AbstractHotkey.check_hotkey(self, modifiers, key, windowTitle) and self.enabled:
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
        
    def __str__(self):
        return "AutoKey global hotkeys"  # TODO: i18n
