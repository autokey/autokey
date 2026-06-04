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

"""Engine backend for Autokey"""

import pathlib

from collections.abc import Iterable

from typing import Tuple, Optional, List, Union

import autokey.model.folder
import autokey.model.helpers
import autokey.model.phrase
import autokey.model.script
from autokey import configmanager
from autokey.model.key import Key

from autokey.scripting.system import System

logger = __import__("autokey.logger").logger.get_logger(__name__)

class Engine:
    """
    Provides access to the internals of AutoKey.

    Note that any configuration changes made using this API while the configuration window
    is open will not appear until it is closed and re-opened.
    """
    SendMode = autokey.model.phrase.SendMode
    Key = Key

    def __init__(self, config_manager, runner):
        """
        """
        self.configManager = config_manager
        self.runner = runner
        self.monitor = config_manager.app.monitor
        self._macro_args = []
        self._script_args = []
        self._script_kwargs = {}
        self._return_value = ''
        self._triggered_abbreviation = None  # type: Optional[str]

    def get_folder(self, title: str):
        """
        Retrieve a folder by its title

        Usage: C{engine.get_folder(title)}

        Note that if more than one folder has the same title, only the first match will be
        returned.
        """
        validateType(title, "title", str)
        for folder in self.configManager.allFolders:
            if folder.title == title:
                return folder
        return None

    def create_folder(self, title: str, parent_folder=None, temporary=False):
        """
        Create and return a new folder.

        Usage: C{engine.create_folder("new folder"), parent_folder=folder, temporary=True}

        Descriptions for the optional arguments:

        :param parent_folder: Folder to make this folder a subfolder of. If
            passed as a folder, it will be that folder within AutoKey.
            If passed as pathlib.Path, it will be created or added at that path.
            Paths expand ~ to $HOME.
        :param temporary: Folders created with temporary=True are
            not persisted.
            Used for single-source rc-style scripts.
            Cannot be used if parent_folder is a Path.

        If a folder of that name already exists, this will return it unchanged.
        If the folder wasn't already added to autokey, it will be.
        The 'temporary' property is not touched to avoid deleting an existing
        folder.
        Note that if more than one folder has the same title, only the first match will be
        returned.
        """
        validateType(title, "title", str)
        validateType(parent_folder, "parent_folder",
                     [autokey.model.folder.Folder, pathlib.Path])
        validateType(temporary, "temporary", bool)
        # XXX Doesn't check if a folder already exists at this path in autokey.
        if isinstance(parent_folder, pathlib.Path):
            if temporary:
                raise ValueError("Parameter 'temporary' is True, but a path \
                        was given as the parent folder. Temporary folders \
                        cannot use absolute paths.")
            path = parent_folder.expanduser() / title
            path.mkdir(parents=True, exist_ok=True)
            new_folder = autokey.model.folder.Folder(title, path=str(path.resolve()))
            self.configManager.allFolders.append(new_folder)
            return new_folder
        # TODO: Convert this to use get_folder, when we change to specifying
        # the exact folder by more than just title.
        if parent_folder is None:
            parent_folders = self.configManager.allFolders
        elif isinstance(parent_folder, autokey.model.folder.Folder):
            parent_folders = parent_folder.folders
        else:
            # Input is previously validated, must match one of the above.
            pass

        for folder in parent_folders:
            if folder.title == title:
                return folder
        else:
            new_folder = autokey.model.folder.Folder(title)
            if parent_folder is None:
                self.configManager.allFolders.append(new_folder)
            else:
                parent_folder.add_folder(new_folder)
                if not temporary and parent_folder.temporary:
                    raise ValueError("Parameter 'temporary' is False, but parent folder is a temporary one. \
Folders created within temporary folders must themselves be set temporary")

            if not temporary:
                new_folder.persist()
            else:
                new_folder.temporary = True
            return new_folder


    def create_phrase(self, folder, name: str, contents: str,
                      abbreviations: Union[str, List[str]]=None,
                      hotkey: Tuple[List[Union[Key, str]], Union[Key, str]]=None,
                      send_mode: autokey.model.phrase.SendMode = autokey.model.phrase.SendMode.CB_CTRL_V, window_filter: str=None,
                      show_in_system_tray: bool=False, always_prompt: bool=False,
                      temporary=False, replace_existing_hotkey=False):
        """
        Create a new text phrase inside the given folder. Use C{engine.get_folder(folder_name)} to retrieve the folder
        you wish to create the Phrase in. If the folder is a temporary
        one, the phrase will be created as temporary.

        The first three arguments (folder, name and contents) are required. All further arguments are optional and
        considered to be keyword-argument only. Do not rely on the order of the optional arguments.
        The optional parameters can be used to configure the newly created Phrase.

        Usage (minimal example): C{engine.create_phrase(folder, name, contents)}

        Further concrete examples:
        C{
        engine.create_phrase(folder, "My new Phrase", "This is the Phrase content", abbreviations=["abc", "def"],
        hotkey=([engine.Key.SHIFT], engine.Key.NP_DIVIDE), send_mode=engine.SendMode.CB_CTRL_SHIFT_V,
        window_filter="konsole\\.Konsole", show_in_system_tray=True)
        }

        Descriptions for the optional arguments:

        abbreviations may be a single string or a list of strings. Each given string is assigned as an abbreviation
        to the newly created phrase.

        hotkey parameter: The hotkey parameter accepts a 2-tuple, consisting of a list of modifier keys in the first
        element and an unshifted (lowercase) key as the second element.
        Modifier keys must be given as a list of strings (or Key enum instances), with the following
        values permitted:
        
        - <ctrl>
        - <alt>
        - <super>
        - <hyper>
        - <meta>
        - <shift>

        The key must be an unshifted character (i.e. lowercase) or a Key enum instance. Modifier keys from the list
        above are NOT allowed here. Example: (["<ctrl>", "<alt>"], "9") to assign "<Ctrl>+<Alt>+9" as a hotkey.
        The Key enum contains objects representing various special keys and is available as an attribute of the "engine"
        object, named "Key". So to access a function key, you can use the string "<f12>" or engine.Key.F12
        See the AutoKey Wiki for an overview of all available keys in the enumeration.

        send_mode: This parameter configures how AutoKey sends the phrase content, for example by typing or by pasting
        using the clipboard. It accepts items from the SendMode enumeration, which is also available from the engine
        object as engine.SendMode. The parameter defaults to
        engine.SendMode.KEYBOARD. Available send modes are:

        - KEYBOARD
        - CB_CTRL_V
        - CB_CTRL_SHIFT_V
        - CB_SHIFT_INSERT
        - SELECTION

        To paste the Phrase using "<shift>+<insert>, set send_mode=engine.SendMode.CB_SHIFT_INSERT

        window_filter: Accepts a string which will be used as a regular expression to match window titles or
        applications using the WM_CLASS attribute.

        :param folder: folder to place the abbreviation in, retrieved using C{engine.get_folder()}
        :param name: Name/description for the phrase.
        :param contents: the expansion text
        :param abbreviations: Can be a single string or a list (or other iterable) of strings. Assigned to the Phrase
        :param hotkey: A tuple containing a keyboard combination that will be assigned as a hotkey.
            First element is a list of modifiers, second element is the key.
        :param send_mode: The pasting mode that will be used to expand the Phrase.
            Used to configure, how the Phrase is expanded. Defaults to typing using the "CTRL+V" method.
        :param window_filter: A string containing a regular expression that will be used as the window filter.
        :param show_in_system_tray: A boolean defaulting to False.
            If set to True, the new Phrase will be shown in the tray icon context menu.
        :param always_prompt: A boolean defaulting to False. If set to True,
            the Phrase expansion has to be manually confirmed, each time it is triggered.
        :param temporary: Hotkeys created with temporary=True are
            not persisted as .jsons, and are replaced if the description is not
            unique within the folder.
            Used for single-source rc-style scripts.
        :param replace_existing_hotkey: If true, instead of warning if the hotkey
            is already in use by another phrase or folder, it removes the hotkey
            from those clashes and keeps this phrase's hotkey.
        :raise ValueError: If a given abbreviation or hotkey is already in use or parameters are otherwise invalid
        :return: The created Phrase object. This object is NOT considered part of the public API and exposes the raw
            internals of AutoKey. Ignore it, if you don't need it or don't know what to do with it.
            It can be used for _really_ advanced use cases, where further customizations are desired. Use at your own
            risk. No guarantees are made about the object's structure. Read the AutoKey source code for details.
        """

        validateArguments(folder, name, contents,
                          abbreviations, hotkey, send_mode, window_filter,
                          show_in_system_tray, always_prompt, temporary,
                               replace_existing_hotkey)

        if abbreviations and isinstance(abbreviations, str):
            abbreviations = [abbreviations]
        check_abbreviation_unique(self.configManager, abbreviations, window_filter)

        if not replace_existing_hotkey:
            check_hotkey_unique(self.configManager, hotkey, window_filter)
        else:
            # XXX If something causes the phrase creation to fail after this,
            # this will unset the hotkey without replacing it.
            self.__clear_existing_hotkey(hotkey, window_filter)



        self.monitor.suspend()
        try:
            p = autokey.model.phrase.Phrase(name, contents)
            if send_mode in autokey.model.phrase.SendMode:
                p.sendMode = send_mode
            if abbreviations:
                p.add_abbreviations(abbreviations)
            if hotkey:
                p.set_hotkey(*hotkey)
            if window_filter:
                p.set_window_titles(window_filter)
            p.show_in_tray_menu = show_in_system_tray
            p.prompt = always_prompt
            p.temporary = temporary

            folder.add_item(p)
            # Don't save a json if it is a temporary hotkey. Won't persist across
            # reloads.
            if not temporary:
                p.persist()
            return p
        finally:
            self.monitor.unsuspend()
            self.configManager.config_altered(False)


    def __clear_existing_hotkey(self, hotkey, window_filter):
        existing_item = self.get_item_with_hotkey(hotkey)
        if existing_item and not isinstance(existing_item, configmanager.configmanager.GlobalHotkey):
            if existing_item.filter_matches(window_filter):
                existing_item.unset_hotkey()

    def create_abbreviation(self, folder, description, abbr, contents):
        """
        DEPRECATED. Use engine.create_phrase() with appropriate keyword arguments instead.
        Create a new text phrase inside the given folder and assign the abbreviation given.

        Usage: C{engine.create_abbreviation(folder, description, abbr, contents)}

        When the given abbreviation is typed, it will be replaced with the given
        text.

        :param folder: folder to place the abbreviation in, retrieved using C{engine.get_folder()}
        :param description: description for the phrase
        :param abbr: the abbreviation that will trigger the expansion
        :param contents: the expansion text
        :raise Exception: if the specified abbreviation is not unique
        """
        if not self.configManager.check_abbreviation_unique(abbr, None, None)[0]:
            raise Exception("The specified abbreviation is already in use")

        self.monitor.suspend()
        p = autokey.model.phrase.Phrase(description, contents)
        p.modes.append(autokey.model.helpers.TriggerMode.ABBREVIATION)
        p.abbreviations = [abbr]
        folder.add_item(p)
        p.persist()
        self.monitor.unsuspend()
        self.configManager.config_altered(False)

    def create_hotkey(self, folder, description, modifiers, key, contents):
        """
        DEPRECATED. Use engine.create_phrase() with appropriate keyword arguments instead.
        Create a text hotkey

        Usage: C{engine.create_hotkey(folder, description, modifiers, key, contents)}

        When the given hotkey is pressed, it will be replaced with the given
        text. Modifiers must be given as a list of strings, with the following
        values permitted:

        - <ctrl>
        - <alt>
        - <super>
        - <hyper>
        - <meta>
        - <shift>

        The key must be an unshifted character (i.e. lowercase)

        :param folder: folder to place the abbreviation in, retrieved using C{engine.get_folder()}
        :param description: description for the phrase
        :param modifiers: modifiers to use with the hotkey (as a list)
        :param key: the hotkey
        :param contents: the expansion text
        :raise Exception: if the specified hotkey is not unique
        """
        modifiers.sort()
        if not self.configManager.check_hotkey_unique(modifiers, key, None, None)[0]:
            raise Exception("The specified hotkey and modifier combination is already in use")

        self.monitor.suspend()
        p = autokey.model.phrase.Phrase(description, contents)
        p.modes.append(autokey.model.helpers.TriggerMode.HOTKEY)
        p.set_hotkey(modifiers, key)
        folder.add_item(p)
        p.persist()
        self.monitor.unsuspend()
        self.configManager.config_altered(False)

    def run_script(self, description, *args, **kwargs):
        """
        Run an existing script using its description or path to look it up

        Usage: C{engine.run_script(description, 'foo', 'bar', foobar='foobar'})}

        :param description: description of the script to run. If parsable as
            an absolute path to an existing file, that will be run instead.
        :raise Exception: if the specified script does not exist
        """
        self._script_args = args
        self._script_kwargs = kwargs
        path = pathlib.Path(description)
        path = path.expanduser()
        # Check if absolute path.
        if pathlib.PurePath(path).is_absolute() and path.exists():
            self.runner.run_subscript(path)
        else:
            target_script = None
            for item in self.configManager.allItems:
                if item.description == description and isinstance(item, autokey.model.script.Script):
                    target_script = item

            if target_script is not None:
                self.runner.run_subscript(target_script)
            else:
                raise Exception("No script with description '%s' found" % description)
        return self._return_value

    def run_script_from_macro(self, args):
        """
        Used internally by AutoKey for phrase macros
        """
        self._macro_args = args["args"].split(',')

        try:
            self.run_script(args["name"])
        except Exception as e:
            # TODO: Log more information here, instead of setting the return
            # value.
            self.set_return_value("{ERROR: %s}" % str(e))

    def run_system_command_from_macro(self, args):
        """
        Used internally by AutoKey for system macros
        """

        try:
            self._return_value = System.exec_command(args["command"], getOutput=True)
        except Exception as e:
            self.set_return_value("{ERROR: %s}" % str(e))

    def get_script_arguments(self):
        """
        Get the arguments supplied to the current script via the scripting api

        Usage: C{engine.get_script_arguments()}

        :return: the arguments
        :rtype: C{list[Any]}
        """
        return self._script_args

    def get_script_keyword_arguments(self):
        """
        Get the arguments supplied to the current script via the scripting api
        as keyword args.

        Usage: C{engine.get_script_keyword_arguments()}

        :return: the arguments
        :rtype: C{Dict[str, Any]}
        """
        return self._script_kwargs

    def get_macro_arguments(self):
        """
        Get the arguments supplied to the current script via its macro

        Usage: C{engine.get_macro_arguments()}

        :return: the arguments
        :rtype: C{list(str())}
        """
        return self._macro_args

    def set_return_value(self, val):
        """
        Store a return value to be used by a phrase macro

        Usage: C{engine.set_return_value(val)}

        :param val: value to be stored
        """
        self._return_value = val

    def _get_return_value(self):
        """
        Used internally by AutoKey for phrase macros
        """
        ret = self._return_value
        self._return_value = ''
        return ret

    def _set_triggered_abbreviation(self, abbreviation: str, trigger_character: str):
        """
        Used internally by AutoKey to provide the abbreviation and trigger that caused the script to execute.
        :param abbreviation: Abbreviation that caused the script to execute
        :param trigger_character: Possibly empty "trigger character". As defined in the abbreviation configuration.
        """
        self._triggered_abbreviation = abbreviation
        self._triggered_character = trigger_character

    def get_triggered_abbreviation(self) -> Tuple[Optional[str], Optional[str]]:
        """
        This function can be queried by a script to get the abbreviation text that triggered it's execution.

        If a script is triggered by an abbreviation, this function returns a tuple containing two strings. First element
        is the abbreviation text. The second element is the trigger character that finally caused the execution. It is
        typically some whitespace character, like ' ', '\t' or a newline character. It is empty, if the abbreviation was
        configured to "trigger immediately".

        If the script execution was triggered by a hotkey, a call to the DBus interface, the tray icon, the "Run"
        button in the main window or any other means, this function returns a tuple containing two None values.

        Usage: C{abbreviation, trigger_character = engine.get_triggered_abbreviation()}
        You can determine if the script was triggered by an abbreviation by simply testing the truth value of the first
        returned value.

        :return: Abbreviation that triggered the script execution, if any.
        :rtype: C{Tuple[Optional[str], Optional[str]]}
        """
        return self._triggered_abbreviation, self._triggered_character


    def remove_all_temporary(self, folder=None,
            in_temp_parent=False):
        """
        Removes all temporary folders and phrases, as well as any within
        temporary folders.
        Useful for rc-style scripts that want to change a set of keys.
        """
        self.configManager.remove_all_temporary(folder,
                in_temp_parent)

    def get_item_with_hotkey(self, hotkey):
        if not hotkey:
            return
        modifiers = sorted(hotkey[0])
        return self.configManager.get_item_with_hotkey(modifiers, hotkey[1])


def validateAbbreviations(abbreviations):
    """
    Checks if the given abbreviations are a list/iterable of strings

    :param abbreviations: Abbreviations list to be validated
    :raise ValueError: Raises C{ValueError} if C{abbreviations} is anything other than C{str} or C{Iterable}
    """
    if abbreviations is None:
        return
    fail=False
    if not isinstance(abbreviations, str):
        fail=True
        if isinstance(abbreviations, Iterable):
            fail=False
            for item in abbreviations:
                if not isinstance(item, str):
                    fail=True
    if fail:
        raise ValueError("Expected abbreviations to be a single string or a list/iterable of strings, not {}".format(
            type(abbreviations))
            )


def check_abbreviation_unique(configmanager, abbreviations, window_filter):
    """
    Checks if the given abbreviations are unique

    :param configmanager: ConfigManager Instance to check abbrevations
    :param abbreviations: List of abbreviations to be checked
    :param window_filter: Window filter that the abbreviation will apply to.
    :raise ValueError: Raises C{ValueError} if an abbreviation is already in use.
    """
    if not abbreviations:
        return
    for abbr in abbreviations:
        if not configmanager.check_abbreviation_unique(abbr, window_filter, None)[0]:
            raise ValueError("The specified abbreviation '{}' is already in use.".format(abbr))


def check_hotkey_unique(configmanager, hotkey, window_filter):
    """
    Checks if the given hotkey is unique

    :param configmanager: ConfigManager Instance used to check hotkey
    :param hotkey: hotkey to be check if unique
    :param window_filter: Window filter to be applied to the hotkey
    """
    if not hotkey:
        return
    modifiers = sorted(hotkey[0])
    if not configmanager.check_hotkey_unique(modifiers, hotkey[1], window_filter, None)[0]:
        raise ValueError("The specified hotkey and modifier combination is already in use: {}".format(hotkey))


def isValidHotkeyType(item):
    """
    Checks if the hotkey is valid.

    :param item: Hotkey to be checked
    :return: Returns C{True} if hotkey is valid, C{False} otherwise
    """
    fail=False
    if isinstance(item, Key):
        fail=False
    elif isinstance(item, str):
        if len(item) == 1:
            fail=False
        else:
            fail = not Key.is_key(item)
    else:
        fail=True
    return not fail


def validateHotkey(hotkey):
    """

    """
    failmsg = "Expected hotkey to be a tuple of modifiers then keys, as lists of Key or str, not {}".format(type(hotkey))
    if hotkey is None:
        return
    fail=False
    if not isinstance(hotkey, tuple):
        fail=True
    else:
        if len(hotkey) != 2:
            fail=True
        else:
            # First check modifiers is list of valid hotkeys.
            if isinstance(hotkey[0], list):
                for item in hotkey[0]:
                    if not isValidHotkeyType(item):
                        fail=True
                        failmsg = "Hotkey is not a valid modifier: {}".format(item)
            else:
                fail=True
                failmsg = "Hotkey modifiers is not a list"
            # Then check second element is a key or str
            if not isValidHotkeyType(hotkey[1]):
                fail=True
                failmsg = "Hotkey is not a valid key: {}".format(hotkey[1])
    if fail:
        raise ValueError(failmsg)


def validateArguments(folder, name, contents,
                          abbreviations, hotkey, send_mode, window_filter,
                          show_in_system_tray, always_prompt, temporary,
                          replace_existing_hotkey):
    if folder is None:
        raise ValueError("Parameter 'folder' is None. Check the folder is a valid autokey folder")
    validateType(folder, "folder", autokey.model.folder.Folder)
    # For when we allow pathlib.Path
    # validateType(folder, "folder",
    #         [model.Folder, pathlib.Path])
    validateType(name, "name", str)
    validateType(contents, "contents", str)
    validateAbbreviations(abbreviations)
    validateHotkey(hotkey)
    validateType(send_mode, "send_mode", autokey.model.phrase.SendMode)
    validateType(window_filter, "window_filter", str)
    validateType(show_in_system_tray, "show_in_system_tray", bool)
    validateType(always_prompt, "always_prompt", bool)
    validateType(temporary, "temporary", bool)
    validateType(replace_existing_hotkey, "replace_existing_hotkey", bool)
    # TODO: The validation should be done by some controller functions in the model base classes.

    if folder.temporary and not temporary:
        raise ValueError("Parameter 'temporary' is False, but parent folder is a temporary one. \
    Phrases created within temporary folders must themselves be explicitly set temporary")


def validateType(item, name, type_):
    """ type_ may be a list, in which case if item matches
    any type, no error is raised.
    """
    if item is None:
        return
    if isinstance(type_, list):
        failed=True
        for type__ in type_:
            if isinstance(item, type__):
                failed=False
        if failed:
            raise ValueError("Expected {} to be one of {}, not {}".format(
                name,
                type_,
                type(item)))
    else:
        if not isinstance(item, type_):
            raise ValueError("Expected {} to be {}, not {}".format(
                name,
                type_,
                type(item)))
