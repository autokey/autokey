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
from autokey.model.triggermode import TriggerMode
import autokey.model.phrase
import autokey.model.script
from autokey.model import key
from autokey import common
from autokey.configmanager.configmanager_constants import CONFIG_FILE, CONFIG_DEFAULT_FOLDER, CONFIG_FILE_BACKUP, \
    RECENT_ENTRIES_FOLDER, IS_FIRST_RUN, SERVICE_RUNNING, MENU_TAKES_FOCUS, SHOW_TRAY_ICON, SORT_BY_USAGE_COUNT, \
    PROMPT_TO_SAVE, ENABLE_QT4_WORKAROUND, UNDO_USING_BACKSPACE, WINDOW_DEFAULT_SIZE, HPANE_POSITION, COLUMN_WIDTHS, \
    SHOW_TOOLBAR, NOTIFICATION_ICON, WORKAROUND_APP_REGEX, TRIGGER_BY_INITIAL, SCRIPT_GLOBALS, INTERFACE_TYPE, \
    DISABLED_MODIFIERS, GTK_THEME, GTK_TREE_VIEW_EXPANDED_ROWS, PATH_LAST_OPEN, KEYBOARD, MOUSE, DEVICES, DELAY
import autokey.configmanager.version_upgrading as version_upgrade
import autokey.configmanager.predefined_user_files
from autokey.iomediator.constants import X_RECORD_INTERFACE
from autokey.model.key import MODIFIERS

logger = __import__("autokey.logger").logger.get_logger(__name__)


def create_config_manager_instance(auto_key_app, had_error=False):
    create_default_folder()
    try:
        config_manager = ConfigManager(auto_key_app)
    except Exception as e:
        _recover_config_backup(had_error, e)
        return create_config_manager_instance(auto_key_app, True)
    logger.debug("Global settings: %r", ConfigManager.SETTINGS)
    return config_manager

def create_default_folder():
    if not os.path.exists(CONFIG_DEFAULT_FOLDER):
        logger.info("Default config dir not found. Default config will be rebuilt.")
        os.mkdir(CONFIG_DEFAULT_FOLDER)


def _recover_config_backup(had_error, error):
    no_config_and_backup_file = \
        not os.path.exists(CONFIG_FILE_BACKUP) and \
        not os.path.exists(CONFIG_FILE)
    if had_error or no_config_and_backup_file:
        logger.exception(
            "Error while loading configuration. Cannot recover.")
        raise error
    logger.exception(
        "Error while loading configuration. Backup has been restored.")
    _restore_backup_config()


def _try_persist_settings(config_manager):
    # TODO: maybe use with-statement instead of try-except?
    try:
        _persist_settings(config_manager)
        logger.info("Finished persisting configuration - no errors")
    except Exception as e:
        # unsure why this originally didn't try to delete the current one. May
        # actually be ok to try deleting current, in which case this func can
        # be altered.
        _restore_backup_config(delete_current=False)
        msg = "Error while saving configuration. Backup has been restored (if found)."
        logger.exception(msg)
        raise Exception(msg)

def save_files(config_manager):
    logger.info("Persisting files")
    for item in config_manager.allItems:
        item.persist()

def save_config(config_manager):
    logger.info("Persisting configuration")
    config_manager.app.monitor.suspend()
    _back_up_config()
    _try_persist_settings(config_manager)
    config_manager.app.monitor.unsuspend()


def _back_up_config():
    if os.path.exists(CONFIG_FILE):
        logger.info("Backing up existing config file")
        shutil.copy2(CONFIG_FILE, CONFIG_FILE_BACKUP)

def _restore_backup_config(delete_current=True):
    if os.path.exists(CONFIG_FILE) and delete_current:
        os.remove(CONFIG_FILE)
    if os.path.exists(CONFIG_FILE_BACKUP):
        shutil.copy2(CONFIG_FILE_BACKUP, CONFIG_FILE)


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
        _write_settings_file(serializable_data)
    except (TypeError, ValueError):
        # The user added non-serializable data to the store, so remove all non-serializable keys or values.
        serializable_data["settings"][SCRIPT_GLOBALS] = _sanitise_serializable_store_entries(
            serializable_data["settings"][SCRIPT_GLOBALS])
        _write_settings_file(serializable_data)


def _write_settings_file(serializable_data: dict):
    """
    Write the settings as JSON to the configuration file
    :raises TypeError: If the user tries to store non-serializable types
    :raises ValueError: If the user tries to store circular referenced (recursive) structures.
    """
    with open(CONFIG_FILE, "w") as json_file:
            json.dump(serializable_data, json_file, indent=4)


def _sanitise_serializable_store_entries(store: dict):
    """
    This function is called if there are non-serializable items in the global script storage.
    This function removes all such items.
    """
    removed_key_list = []
    for key, value in store.items():
        no_serialisable_part = not _is_serializable(key) or not _is_serializable(value)
        if no_serialisable_part:
            logger.info("Remove non-serializable item from the global script store. Key: '{}', Value: '{}'. "
                        "This item cannot be saved and therefore will be lost.".format(key, value))
            removed_key_list.append(key)
    for key in removed_key_list:
        del store[key]
    return store


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
                PATH_LAST_OPEN: "0",
                KEYBOARD: [],
                MOUSE: [],
                DEVICES: [],
                DELAY: 0.5
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

        self.__set_default_global_hotkeys()

        # Set the attribute to the default first. Without this, AK breaks, if started for the first time. See #274
        self.workAroundApps = re.compile(self.SETTINGS[WORKAROUND_APP_REGEX])

        app.init_global_hotkeys(self)

        self.load_global_config()

        self.__watch_config_dirs()

        # if load_global_config found an exiting config to load
        if self.folders:
            return

        # --- Code below here only executed if no persisted config data provided
        self.__create_sample_folders()
        # TODO - future functionality
        self.recentEntries = []
        self.config_altered(True)

    def __set_default_global_hotkeys(self):
        self.configHotkey = GlobalHotkey()
        self.configHotkey.set_hotkey(["<super>"], "k")
        self.configHotkey.enabled = True

        self.toggleServiceHotkey = GlobalHotkey()
        self.toggleServiceHotkey.set_hotkey(["<super>", "<shift>"], "k")
        self.toggleServiceHotkey.enabled = True

    def __watch_config_dirs(self):
        self.app.monitor.add_watch(CONFIG_DEFAULT_FOLDER)
        self.app.monitor.add_watch(common.CONFIG_DIR)

    def __create_sample_folders(self):
        logger.info("No configuration found - creating new one")
        self.folders.append(autokey.configmanager.predefined_user_files.create_my_phrases_folder())
        self.folders.append(autokey.configmanager.predefined_user_files.create_sample_scripts_folder())
        logger.debug("Initial folders generated and populated with example data.")

    def get_serializable(self):
        extraFolders = self.__get_nondefault_config_folders()
        d = {
            "version": self.VERSION,
            "userCodeDir": self.userCodeDir,
            "settings": ConfigManager.SETTINGS,
            "folders": extraFolders,
            "toggleServiceHotkey": self.toggleServiceHotkey.get_serializable(),
            "configHotkey": self.configHotkey.get_serializable()
            }
        return d

    def __get_nondefault_config_folders(self):
        extraFolders = []
        for folder in self.folders:
            if not folder.path.startswith(CONFIG_DEFAULT_FOLDER):
                extraFolders.append(folder.path)
        return extraFolders

    def load_global_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        logger.info("Loading config from existing file: " + CONFIG_FILE)

        with open(CONFIG_FILE, 'r') as pFile:
            data = json.load(pFile)

        version_upgrade.upgrade_configuration_format(self, data)

        self.VERSION = data["version"]
        self.userCodeDir = data["userCodeDir"]
        apply_settings(data["settings"])

        self.load_disabled_modifiers()

        self.workAroundApps = re.compile(self.SETTINGS[WORKAROUND_APP_REGEX])

        self.__load_folders(data)

        self.toggleServiceHotkey.load_from_serialized(data["toggleServiceHotkey"])
        self.configHotkey.load_from_serialized(data["configHotkey"])

        if self.VERSION < self.CLASS_VERSION:
            version_upgrade.upgrade_configuration_after_load(self, data)

        self.config_altered(False)
        logger.info("Successfully loaded configuration")

    def path_created_or_modified(self, path):
        directory, baseName = os.path.split(path)
        loaded = False

        if path == CONFIG_FILE:
            self.reload_global_config()

        elif directory != common.CONFIG_DIR:
            # ignore all other changes in top dir

            if os.path.isdir(path):
                loaded = self.__handle_dir_created_or_modified(
                    path, directory, loaded)
            elif os.path.isfile(path):
                # -- handle txt or py files added or modified
                loaded = self.__handle_file_created_or_modified(
                    path, baseName, directory, loaded)
            if not loaded:
                logger.warning("No action taken for create/update event at %s", path)
            else:
                self.config_altered(False)
            return loaded

    def __load_folders(self, data):
        for path in self.get_all_config_folder_paths(data):
            f = autokey.model.folder.Folder("", path=path)
            f.load()
            logger.debug("Loading folder at '%s'", path)
            self.folders.append(f)


    def get_all_config_folder_paths(self, data):
        for path in glob.glob(CONFIG_DEFAULT_FOLDER + "/*"):
            if os.path.isdir(path):
                yield path
        for path in data["folders"]:
            yield path

    def get_all_folders(self):
        out = []
        for folder in self.folders:
            out.append(folder)
            out.extend(folder.get_child_folders())
        return out

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

    def __handle_dir_created_or_modified(self, path, directory, loaded):
        f = autokey.model.folder.Folder("", path=path)

        if directory == CONFIG_DEFAULT_FOLDER:
            self.folders.append(f)
            f.load()
            loaded = True
        else:
            folder = self.__checkExistingFolder(directory)
            if folder is not None:
                # TODO is this actually doing anything?
                f.load(folder)
                folder.add_folder(f)
                loaded = True
        return loaded

    def __load_folder(self, directory, loaded):
        folder = self.__checkExistingFolder(directory)
        if folder is not None:
            folder.load_from_serialized()
            loaded = True
        return loaded

    def __load_item_matching_path(self, path, loaded):
        for item in self.allItems:
            if item.get_json_path() == path:
                item.load_from_serialized()
                loaded = True
        return loaded

    def __create_item_with_path(self, baseName, path):
        if baseName.endswith(".txt"):
            item_at_path = autokey.model.phrase.Phrase("", "", path=path)
        elif baseName.endswith(".py"):
            item_at_path = autokey.model.script.Script("", "", path=path)
        else:
            item_at_path = None
        return item_at_path

    def __add_item_to_folder(self, directory, item_at_path, isNew, loaded):
        folder = self.__checkExistingFolder(directory)
        if folder is not None:
            # load sets the parent folder and brings in the item data.
            item_at_path.load(folder)
            if isNew: folder.add_item(item_at_path)
            loaded = True
        return loaded

    def __handle_file_created_or_modified(self, path, baseName, directory,
                                          loaded):
        item_at_path = self.__checkExisting(path)
        isNew = False

        if item_at_path is None:
            isNew = True
            item_at_path = self.__create_item_with_path(baseName, path)

        if item_at_path is not None:
            loaded = self.__add_item_to_folder(directory, item_at_path, isNew, loaded)

        # --- handle changes to folder settings
        if baseName == "folder.json":
            loaded = self.__load_folder(directory, loaded)

        # --- handle changes to item settings
        if baseName.endswith(".json"):
            loaded = self.__load_item_matching_path(path, loaded)
        return loaded

    def path_removed(self, path):
        directory, _ = os.path.split(path)
        if directory == common.CONFIG_DIR: # ignore all deletions in top dir
            return

        deleted = self.__remove_entry(path)

        if not deleted:
            logger.warning("No action taken for delete event at %s", path)
        else:
            self.config_altered(False)
        return deleted

    def __remove_entry(self, path):
        folder = self.__checkExistingFolder(path)
        item = self.__checkExisting(path)

        if folder is not None:
            self.__remove_folder(folder)
            return True
        elif item is not None:
            item.parent.remove_item(item)
            return True
        return False

    def __remove_folder(self, folder):
        if folder.parent is None:
            self.folders.remove(folder)
        else:
            folder.parent.remove_folder(folder)


    def load_disabled_modifiers(self):
        """
        Load all disabled modifier keys from the configuration file. Called
        during startup, after the configuration is read into the SETTINGS
        dictionary.
        :return:
        """
        try:
            self.SETTINGS[DISABLED_MODIFIERS] = \
                self.__convert_to_keys(self.SETTINGS[DISABLED_MODIFIERS])
        except ValueError:
            logger.error(
                "Unknown value in the disabled modifier list found. Unexpected: {}" \
                .format(self.SETTINGS[DISABLED_MODIFIERS]))
            self.SETTINGS[DISABLED_MODIFIERS] = []

        self.__disable_modifiers(self.SETTINGS[DISABLED_MODIFIERS])

    def __convert_to_keys(self, modifiers):
        return [key.Key(value) for value in modifiers]

    def __disable_modifiers(self, modifiers):
        for possible_modifier in modifiers:
            self._check_if_modifier(possible_modifier)
            logger.info(
                "Disabling modifier key {} based on the stored configuration file." \
                .format(possible_modifier))
            MODIFIERS.remove(possible_modifier)

    @staticmethod
    def is_modifier_disabled(modifier: key.Key) -> bool:
        """Checks, if the given modifier key is disabled. """
        ConfigManager._check_if_modifier(modifier)
        return modifier in ConfigManager.SETTINGS[DISABLED_MODIFIERS]

    @staticmethod
    def disable_modifier(modifier: typing.Union[key.Key, str]):
        """
        Permanently disable a modifier key. This can be used to disable
        unwanted modifier keys, like CAPSLOCK, if the user remapped the
        physical key to something else.
        :param modifier: Modifier key to disable.
        :return:
        """
        modifier = ConfigManager._ensure_valid_modifier_key(modifier)
        try:
            logger.info("Disabling modifier key {} on user request.".format(modifier))
            MODIFIERS.remove(modifier)
        except ValueError:
            logger.warning("Disabling already disabled modifier key. Affected key: {}".format(modifier))
        else:
            ConfigManager.SETTINGS[DISABLED_MODIFIERS].append(modifier)

    @staticmethod
    def _ensure_valid_modifier_key(modifier):
        if isinstance(modifier, str):
            modifier = key.Key(modifier)
        ConfigManager._check_if_modifier(modifier)
        return modifier

    @staticmethod
    def enable_modifier(modifier: typing.Union[key.Key, str]):
        """
        Enable a previously disabled modifier key.
        :param modifier: Modifier key to re-enable
        :return:
        """
        modifier = ConfigManager._ensure_valid_modifier_key(modifier)
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

        existingPaths = self.__get_existing_nondefault_toplevel_folder_paths()
        self.__load_new_folders_from_paths(data["folders"], existingPaths)

        self.toggleServiceHotkey.load_from_serialized(data["toggleServiceHotkey"])
        self.configHotkey.load_from_serialized(data["configHotkey"])

        self.config_altered(False)
        logger.info("Successfully reloaded global configuration")

    def __load_new_folders_from_paths(self, folderPaths, existingPaths):
        for folderPath in folderPaths:
            if folderPath not in existingPaths:
                self.__load_folder_from_path(folderPath)

    def __get_existing_nondefault_toplevel_folder_paths(self):
        existingPaths = []
        for folder in self.folders:
            if folder.parent is None and not folder.path.startswith(CONFIG_DEFAULT_FOLDER):
                existingPaths.append(folder.path)

        return existingPaths

    def config_altered(self, persistGlobal):
        """
        Called when some element of configuration has been altered, to update
        the lists of phrases/folders.

        :param persistGlobal: save the global configuration at the end of the process
        """
        logger.info("Configuration changed - rebuilding in-memory structures")

        self.lock.acquire()

        self.__clear_loaded_entries()
        for folder in self.folders:
            self.__sort_and_watch_folder(folder)
            self.__processFolder(folder)
        self.__reload_global_hotkeys()
        #_logger.debug("Global hotkeys: %s", self.globalHotkeys)

        #_logger.debug("Hotkey folders: %s", self.hotKeyFolders)
        #_logger.debug("Hotkey phrases: %s", self.hotKeys)
        #_logger.debug("Abbreviation phrases: %s", self.abbreviations)
        #_logger.debug("All folders: %s", self.allFolders)
        #_logger.debug("All phrases: %s", self.allItems)

        if persistGlobal:
            save_config(self)

        self.lock.release()

    def __reload_global_hotkeys(self):
        self.globalHotkeys = []
        self.globalHotkeys.append(self.configHotkey)
        self.globalHotkeys.append(self.toggleServiceHotkey)

    def __clear_loaded_entries(self):
        self.hotKeyFolders = []
        self.hotKeys = []

        self.abbreviations = []

        self.allFolders = []
        self.allItems = []

    def __processFolder(self, parentFolder):
        if not self.app.monitor.has_watch(parentFolder.path):
            self.app.monitor.add_watch(parentFolder.path)

        for folder in parentFolder.folders:
            self.__sort_and_watch_folder(folder)
            self.__processFolder(folder)

        for item in parentFolder.items:
            self.__sort_item(item)

    def __sort_and_watch_folder(self, folder):
        if TriggerMode.HOTKEY in folder.modes:
            self.hotKeyFolders.append(folder)

        self.allFolders.append(folder)

        if not self.app.monitor.has_watch(folder.path):
            self.app.monitor.add_watch(folder.path)

    def __sort_item(self, item):
        if TriggerMode.HOTKEY in item.modes:
            self.hotKeys.append(item)
        if TriggerMode.ABBREVIATION in item.modes:
            self.abbreviations.append(item)
        self.allItems.append(item)

    # TODO Future functionality
    def add_recent_entry(self, entry):
        if RECENT_ENTRIES_FOLDER not in self.folders:
            folder = autokey.model.folder.Folder(RECENT_ENTRIES_FOLDER)
            folder.set_hotkey(["<super>"], "<f7>")
            folder.set_modes([TriggerMode.HOTKEY])
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
                    p.set_modes([TriggerMode.PREDICTIVE])

                folder.add_item(p)

            self.config_altered(False)

    def check_abbreviation_unique(self, abbreviation, filterPattern, targetItem):
        """
        Checks that the given abbreviation is not already in use.

        :param abbreviation: the abbreviation to check
        :param filterPattern: The filter pattern associated with the abbreviation
        :param targetItem: the phrase for which the abbreviation to be used
        """
        for item in itertools.chain(self.allFolders, self.allItems):
            if ConfigManager.item_has_abbreviation(item, abbreviation) and \
                    item.filter_matches(filterPattern):
                    return item is targetItem, item

        return True, None

    @staticmethod
    def item_has_abbreviation(item, abbreviation):
        return TriggerMode.ABBREVIATION in item.modes and \
               abbreviation in item.abbreviations

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

        :param modifiers: modifiers for the hotkey
        :param hotKey: the hotkey to check
        :param newFilterPattern:
        :param targetItem: the phrase for which the hotKey to be used
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

        :param modifiers: modifiers for the hotkey
        :param hotKey: the hotkey to check
        :param newFilterPattern:
        """
        for item in self.globalHotkeys:
            if item.enabled and ConfigManager.item_has_same_hotkey(item,
                                             modifiers,
                                             hotKey,
                                             newFilterPattern):
                return item

        for item in itertools.chain(self.allFolders, self.allItems):
            if TriggerMode.HOTKEY in item.modes and \
                    ConfigManager.item_has_same_hotkey(item,
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

        self.__remove_temp_items_from_folder(searchItems, in_temp_parent)

        for subfolder in searchFolders:
            in_temp_parent = self.__remove_temp_folders_from_subfolder(
                folder, subfolder, searchFolders, in_temp_parent)
            self.remove_all_temporary(subfolder, in_temp_parent)

    def __remove_temp_items_from_folder(self, folder, in_temp_parent):
        for item in folder:
            try:
                if item.temporary or in_temp_parent:
                    self.__deleteHotkeys(item)
                    folder.remove(item)
            # Items created before this update don't have a 'temporary' field.
            except AttributeError:
                pass

    def __remove_temp_folders_from_subfolder(self, folder, subfolder, searchFolders, in_temp_parent):
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
        return in_temp_parent

    def delete_hotkeys(self, removed_item):
        return self.__deleteHotkeys(removed_item)

    def __deleteHotkeys(self, removed_item):
        removed_item.unset_hotkey()
        if TriggerMode.HOTKEY in removed_item.modes:
            self.app.hotkey_removed(removed_item)
        if isinstance(removed_item, autokey.model.folder.Folder):
            self.__delete_hotkeys_from_folder_and_items(removed_item)

    def __delete_hotkeys_from_folder_and_items(self, folder):
        for subFolder in folder.folders:
            self.delete_hotkeys(subFolder)
        for item in folder.items:
            if TriggerMode.HOTKEY in item.modes:
                self.app.hotkey_removed(item)


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
        # TODO: Doesn't this always return False? (as long as no exceptions are thrown)
        if autokey.model.abstract_hotkey.AbstractHotkey.check_hotkey_has_properties(self, modifiers, key, windowTitle) and self.enabled:
            logger.debug("Triggered global hotkey using modifiers: %r key: %r", modifiers, key)
            self.closure()
        return False

    def get_hotkey_string(self, key=None, modifiers=None):
        if key is None and modifiers is None:
            if not self.enabled:
                return ""

            key = self.hotKey
            modifiers = self.modifiers

        return autokey.model.abstract_hotkey.AbstractHotkey.build_hotkey_string(modifiers, key)

    def __str__(self):
        return "AutoKey global hotkeys"  # TODO: i18n
