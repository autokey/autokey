# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>
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

import os
import os.path
import shutil
import glob
import threading
import typing
import re
import json
import itertools

import autokey.model.abstract_hotkey
import autokey.model.folder
import autokey.model.helpers
import autokey.model.phrase
import autokey.model.script
from autokey.model import key
from autokey import common
from autokey.configmanager.configmanager_constants import CONFIG_FILE, CONFIG_DEFAULT_FOLDER, CONFIG_FILE_BACKUP, \
    RECENT_ENTRIES_FOLDER, IS_FIRST_RUN, SERVICE_RUNNING, MENU_TAKES_FOCUS, SHOW_TRAY_ICON, SORT_BY_USAGE_COUNT, \
    PROMPT_TO_SAVE, ENABLE_QT4_WORKAROUND, UNDO_USING_BACKSPACE, WINDOW_DEFAULT_SIZE, HPANE_POSITION, COLUMN_WIDTHS, \
    SHOW_TOOLBAR, NOTIFICATION_ICON, WORKAROUND_APP_REGEX, TRIGGER_BY_INITIAL, SCRIPT_GLOBALS, INTERFACE_TYPE, \
    DISABLED_MODIFIERS, GTK_THEME, GTK_TREE_VIEW_EXPANDED_ROWS, PATH_LAST_OPEN
import autokey.configmanager.version_upgrading as version_upgrade
import autokey.configmanager.predefined_user_files
from autokey.iomediator.constants import X_RECORD_INTERFACE
from autokey.model.key import MODIFIERS

logger = __import__("autokey.logger").logger.get_logger(__name__)


def create_config_manager_instance(auto_key_app, had_error=False):
    if not os.path.exists(CONFIG_DEFAULT_FOLDER):
        os.mkdir(CONFIG_DEFAULT_FOLDER)
    try:
        config_manager = ConfigManager(auto_key_app)
    except Exception as e:
        if had_error or not os.path.exists(CONFIG_FILE_BACKUP) or not os.path.exists(CONFIG_FILE):
            logger.exception("Error while loading configuration. Cannot recover.")
            raise

        logger.exception("Error while loading configuration. Backup has been restored.")
        os.remove(CONFIG_FILE)
        shutil.copy2(CONFIG_FILE_BACKUP, CONFIG_FILE)
        return create_config_manager_instance(auto_key_app, True)

    logger.debug("Global settings: %r", ConfigManager.SETTINGS)
    return config_manager


def save_config(config_manager):
    logger.info("Persisting configuration")
    config_manager.app.monitor.suspend()
    # Back up configuration if it exists
    # TODO: maybe use with-statement instead of try-except?
    if os.path.exists(CONFIG_FILE):
        logger.info("Backing up existing config file")
        shutil.copy2(CONFIG_FILE, CONFIG_FILE_BACKUP)
    try:
        _persist_settings(config_manager)
        logger.info("Finished persisting configuration - no errors")
    except Exception as e:
        if os.path.exists(CONFIG_FILE_BACKUP):
            shutil.copy2(CONFIG_FILE_BACKUP, CONFIG_FILE)
        logger.exception("Error while saving configuration. Backup has been restored (if found).")
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
            logger.info("Remove non-serializable item from the global script store. Key: '{}', Value: '{}'. "
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


def apply_settings(settings):
    """
    Allows new settings to be added without users having to lose all their configuration
    """
    for key, value in settings.items():
        ConfigManager.SETTINGS[key] = value


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
                # RECENT_ENTRY_COUNT: 5,
                #RECENT_ENTRY_MINLENGTH: 10,
                #RECENT_ENTRY_SUGGEST: True
                SCRIPT_GLOBALS: {},
                GTK_THEME: "classic",
                GTK_TREE_VIEW_EXPANDED_ROWS: [],
                PATH_LAST_OPEN: "0"
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

        logger.info("No configuration found - creating new one")
        self.folders.append(autokey.configmanager.predefined_user_files.create_my_phrases_folder())
        self.folders.append(autokey.configmanager.predefined_user_files.create_sample_scripts_folder())
        logger.debug("Initial folders generated and populated with example data.")

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
            logger.info("Loading config from existing file: " + CONFIG_FILE)

            with open(CONFIG_FILE, 'r') as pFile:
                data = json.load(pFile)

            version_upgrade.upgrade_configuration_format(self, data)


            self.VERSION = data["version"]
            self.userCodeDir = data["userCodeDir"]
            apply_settings(data["settings"])

            self.load_disabled_modifiers()

            self.workAroundApps = re.compile(self.SETTINGS[WORKAROUND_APP_REGEX])

            for entryPath in glob.glob(CONFIG_DEFAULT_FOLDER + "/*"):
                if os.path.isdir(entryPath):
                    logger.debug("Loading folder at '%s'", entryPath)
                    f = autokey.model.folder.Folder("", path=entryPath)
                    f.load(None)
                    self.folders.append(f)

            for folderPath in data["folders"]:
                f = autokey.model.folder.Folder("", path=folderPath)
                f.load()
                self.folders.append(f)

            self.toggleServiceHotkey.load_from_serialized(data["toggleServiceHotkey"])
            self.configHotkey.load_from_serialized(data["configHotkey"])

            if self.VERSION < self.CLASS_VERSION:
                version_upgrade.upgrade_configuration_after_load(self, data)

            self.config_altered(False)
            logger.info("Successfully loaded configuration")

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
                f = autokey.model.folder.Folder("", path=path)

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
                        i = autokey.model.phrase.Phrase("", "", path=path)
                    elif baseName.endswith(".py"):
                        i = autokey.model.script.Script("", "", path=path)

                if i is not None:
                    folder = self.__checkExistingFolder(directory)
                    if folder is not None:
                        i.load(folder)
                        if isNew: folder.add_item(i)
                        loaded = True

                # --- handle changes to folder settings

                if baseName == "folder.json":
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
                logger.warning("No action taken for create/update event at %s", path)
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
            logger.warning("No action taken for delete event at %s", path)
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
            logger.error("Unknown value in the disabled modifier list found. Unexpected: {}".format(
                self.SETTINGS[DISABLED_MODIFIERS]))
            self.SETTINGS[DISABLED_MODIFIERS] = []

        for possible_modifier in self.SETTINGS[DISABLED_MODIFIERS]:
            self._check_if_modifier(possible_modifier)
            logger.info("Disabling modifier key {} based on the stored configuration file.".format(possible_modifier))
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
            logger.info("Disabling modifier key {} on user request.".format(modifier))
            MODIFIERS.remove(modifier)
        except ValueError:
            logger.warning("Disabling already disabled modifier key. Affected key: {}".format(modifier))
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
            logger.info("Re-eabling modifier key {} on user request.".format(modifier))
            MODIFIERS.append(modifier)
            ConfigManager.SETTINGS[DISABLED_MODIFIERS].remove(modifier)
        else:
            logger.warning("Enabling already enabled modifier key. Affected key: {}".format(modifier))

    @staticmethod
    def _check_if_modifier(modifier: key.Key):
        if not isinstance(modifier, key.Key):
            raise TypeError("The given value must be an AutoKey Key instance, got {}".format(type(modifier)))
        if not modifier in key._ALL_MODIFIERS_:
            raise ValueError("The given key '{}' is not a modifier. Expected one of {}.".format(
                modifier, key._ALL_MODIFIERS_))

    def reload_global_config(self):
        logger.info("Reloading global configuration")
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
                f = autokey.model.folder.Folder("", path=folderPath)
                f.load()
                self.folders.append(f)

        self.toggleServiceHotkey.load_from_serialized(data["toggleServiceHotkey"])
        self.configHotkey.load_from_serialized(data["configHotkey"])

        self.config_altered(False)
        logger.info("Successfully reloaded global configuration")

    def config_altered(self, persistGlobal):
        """
        Called when some element of configuration has been altered, to update
        the lists of phrases/folders.

        @param persistGlobal: save the global configuration at the end of the process
        """
        logger.info("Configuration changed - rebuilding in-memory structures")

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
            if autokey.model.helpers.TriggerMode.HOTKEY in folder.modes:
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
            if autokey.model.helpers.TriggerMode.HOTKEY in folder.modes:
                self.hotKeyFolders.append(folder)
            self.allFolders.append(folder)

            if not self.app.monitor.has_watch(folder.path):
                self.app.monitor.add_watch(folder.path)

            self.__processFolder(folder)

        for item in parentFolder.items:
            if autokey.model.helpers.TriggerMode.HOTKEY in item.modes:
                self.hotKeys.append(item)
            if autokey.model.helpers.TriggerMode.ABBREVIATION in item.modes:
                self.abbreviations.append(item)
            self.allItems.append(item)

    # TODO Future functionality
    def add_recent_entry(self, entry):
        if RECENT_ENTRIES_FOLDER not in self.folders:
            folder = autokey.model.folder.Folder(RECENT_ENTRIES_FOLDER)
            folder.set_hotkey(["<super>"], "<f7>")
            folder.set_modes([autokey.model.helpers.TriggerMode.HOTKEY])
            self.folders[RECENT_ENTRIES_FOLDER] = folder
            self.recentEntries = []

        folder = self.folders[RECENT_ENTRIES_FOLDER]

        if entry not in self.recentEntries:
            self.recentEntries.append(entry)
            while len(self.recentEntries) > self.SETTINGS[RECENT_ENTRY_COUNT]: # noqa: F821
                self.recentEntries.pop(0)

            folder.items = []

            for theEntry in self.recentEntries:
                if len(theEntry) > 17:
                    description = theEntry[:17] + "..."
                else:
                    description = theEntry

                p = autokey.model.phrase.Phrase(description, theEntry)
                if self.SETTINGS[RECENT_ENTRY_SUGGEST]: # noqa: F821
                    p.set_modes([autokey.model.helpers.TriggerMode.PREDICTIVE])

                folder.add_item(p)

            self.config_altered(False)

    def check_abbreviation_unique(self, abbreviation, filterPattern, targetItem):
        """
        Checks that the given abbreviation is not already in use.

        @param abbreviation: the abbreviation to check
        @param filterPattern: The filter pattern associated with the abbreviation
        @param targetItem: the phrase for which the abbreviation to be used
        """
        for item in itertools.chain(self.allFolders, self.allItems):
            if ConfigManager.item_has_abbreviation(item, abbreviation) and \
                    item.filter_matches(filterPattern):
                    return item is targetItem, item

        return True, None

    @staticmethod
    def item_has_abbreviation(item, abbreviation):
        return autokey.model.helpers.TriggerMode.ABBREVIATION in item.modes and \
               abbreviation in item.abbreviations

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
        item = self.get_item_with_hotkey(modifiers, hotKey, newFilterPattern)
        if item:
            return item is targetItem, item
        else:
            return True, None

    def get_item_with_hotkey(self, modifiers, hotKey, newFilterPattern=None):
        """
        Gets first item with the specified hotkey. Also checks the
        special hotkeys configured from the advanced settings dialog.
        Checks folders first, then phrases, then special hotkeys.

        @param modifiers: modifiers for the hotkey
        @param hotKey: the hotkey to check
        @param newFilterPattern:
        """
        for item in itertools.chain(self.allFolders, self.allItems):
            if autokey.model.helpers.TriggerMode.HOTKEY in item.modes and \
                    ConfigManager.item_has_same_hotkey(item,
                                              modifiers,
                                              hotKey,
                                              newFilterPattern):
                return item

        for item in self.globalHotkeys:
            if item.enabled and ConfigManager.item_has_same_hotkey(item,
                                             modifiers,
                                             hotKey,
                                             newFilterPattern):
                return item
        return None

    @staticmethod
    def item_has_same_hotkey(item, modifiers, hotKey, newFilterPattern):
        return item.modifiers == modifiers and item.hotKey == hotKey and item.filter_matches(newFilterPattern)


    def remove_all_temporary(self, folder=None, in_temp_parent=False):
        """
        Removes all temporary folders and phrases, as well as any within temporary folders.
        Useful for rc-style scripts that want to change a set of keys.
        """
        if folder is None:
            searchFolders = self.allFolders
            searchItems = self.allItems
        else:
            searchFolders = folder.folders
            searchItems = folder.items

        for item in searchItems:
            try:
                if item.temporary or in_temp_parent:
                    self.__deleteHotkeys(item)
                    searchItems.remove(item)
            # Items created before this update don't have a 'temporary' field.
            except AttributeError:
                pass

        for subfolder in searchFolders:
            self.__deleteHotkeys(subfolder)
            try:
                if subfolder.temporary or in_temp_parent:
                    in_temp_parent = True
                    if folder is not None:
                        folder.remove_folder(subfolder)
                    else:
                        searchFolders.remove(subfolder)
            # Items created before this update don't have a 'temporary' field.
            except AttributeError:
                pass
            self.remove_all_temporary(subfolder, in_temp_parent)

    def delete_hotkeys(self, removed_item):
        return self.__deleteHotkeys(removed_item)

    def __deleteHotkeys(self, removed_item):
        removed_item.unset_hotkey()
        app = self.app
        if autokey.model.helpers.TriggerMode.HOTKEY in removed_item.modes:
            app.hotkey_removed(removed_item)

        if isinstance(removed_item, autokey.model.folder.Folder):
            for subFolder in removed_item.folders:
                self.delete_hotkeys(subFolder)

            for item in removed_item.items:
                if autokey.model.helpers.TriggerMode.HOTKEY in item.modes:
                    app.hotkey_removed(item)


class GlobalHotkey(autokey.model.abstract_hotkey.AbstractHotkey):
    """
    A global application hotkey, configured from the advanced settings dialog.
    Allows a method call to be attached to the hotkey.
    """

    def __init__(self):
        autokey.model.abstract_hotkey.AbstractHotkey.__init__(self)
        self.enabled = False
        self.windowInfoRegex = None
        self.isRecursive = False
        self.parent = None
        self.modes = []

    def get_serializable(self):
        d = {
            "enabled": self.enabled
            }
        d.update(autokey.model.abstract_hotkey.AbstractHotkey.get_serializable(self))
        return d

    def load_from_serialized(self, data):
        autokey.model.abstract_hotkey.AbstractHotkey.load_from_serialized(self, data)
        self.enabled = data["enabled"]

    def set_closure(self, closure):
        """
        Set the callable to be executed when the hotkey is triggered.
        """
        self.closure = closure

    def check_hotkey(self, modifiers, key, windowTitle):
        # TODO: Doesn’t this always return False? (as long as no exceptions are thrown)
        if autokey.model.abstract_hotkey.AbstractHotkey.check_hotkey(self, modifiers, key, windowTitle) and self.enabled:
            logger.debug("Triggered global hotkey using modifiers: %r key: %r", modifiers, key)
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
