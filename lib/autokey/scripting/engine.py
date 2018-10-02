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

from typing import Tuple, Optional

from autokey import model


class Engine:
    """
    Provides access to the internals of AutoKey.

    Note that any configuration changes made using this API while the configuration window
    is open will not appear until it is closed and re-opened.
    """

    def __init__(self, configManager, runner):
        self.configManager = configManager
        self.runner = runner
        self.monitor = configManager.app.monitor
        self.__returnValue = ''
        self._triggered_abbreviation = None  # type: Optional[str]

    def get_folder(self, title):
        """
        Retrieve a folder by its title

        Usage: C{engine.get_folder(title)}

        Note that if more than one folder has the same title, only the first match will be
        returned.
        """
        for folder in self.configManager.allFolders:
            if folder.title == title:
                return folder
        return None

    def create_phrase(self, folder, description, contents):
        """
        Create a text phrase

        Usage: C{engine.create_phrase(folder, description, contents)}

        A new phrase with no abbreviation or hotkey is created in the specified folder

        @param folder: folder to place the abbreviation in, retrieved using C{engine.get_folder()}
        @param description: description for the phrase
        @param contents: the expansion text
        """
        self.monitor.suspend()
        p = model.Phrase(description, contents)
        folder.add_item(p)
        p.persist()
        self.monitor.unsuspend()
        self.configManager.config_altered(False)

    def create_abbreviation(self, folder, description, abbr, contents):
        """
        Create a text abbreviation

        Usage: C{engine.create_abbreviation(folder, description, abbr, contents)}

        When the given abbreviation is typed, it will be replaced with the given
        text.

        @param folder: folder to place the abbreviation in, retrieved using C{engine.get_folder()}
        @param description: description for the phrase
        @param abbr: the abbreviation that will trigger the expansion
        @param contents: the expansion text
        @raise Exception: if the specified abbreviation is not unique
        """
        if not self.configManager.check_abbreviation_unique(abbr, None, None):
            raise Exception("The specified abbreviation is already in use")

        self.monitor.suspend()
        p = model.Phrase(description, contents)
        p.modes.append(model.TriggerMode.ABBREVIATION)
        p.abbreviations = [abbr]
        folder.add_item(p)
        p.persist()
        self.monitor.unsuspend()
        self.configManager.config_altered(False)

    def create_hotkey(self, folder, description, modifiers, key, contents):
        """
        Create a text hotkey

        Usage: C{engine.create_hotkey(folder, description, modifiers, key, contents)}

        When the given hotkey is pressed, it will be replaced with the given
        text. Modifiers must be given as a list of strings, with the following
        values permitted:

        <ctrl>
        <alt>
        <super>
        <hyper>
        <meta>
        <shift>

        The key must be an unshifted character (i.e. lowercase)

        @param folder: folder to place the abbreviation in, retrieved using C{engine.get_folder()}
        @param description: description for the phrase
        @param modifiers: modifiers to use with the hotkey (as a list)
        @param key: the hotkey
        @param contents: the expansion text
        @raise Exception: if the specified hotkey is not unique
        """
        modifiers.sort()
        if not self.configManager.check_hotkey_unique(modifiers, key, None, None):
            raise Exception("The specified hotkey and modifier combination is already in use")

        self.monitor.suspend()
        p = model.Phrase(description, contents)
        p.modes.append(model.TriggerMode.HOTKEY)
        p.set_hotkey(modifiers, key)
        folder.add_item(p)
        p.persist()
        self.monitor.unsuspend()
        self.configManager.config_altered(False)

    def run_script(self, description):
        """
        Run an existing script using its description to look it up

        Usage: C{engine.run_script(description)}

        @param description: description of the script to run
        @raise Exception: if the specified script does not exist
        """
        targetScript = None
        for item in self.configManager.allItems:
            if item.description == description and isinstance(item, model.Script):
                targetScript = item

        if targetScript is not None:
            self.runner.run_subscript(targetScript)
        else:
            raise Exception("No script with description '%s' found" % description)

    def run_script_from_macro(self, args):
        """
        Used internally by AutoKey for phrase macros
        """
        self.__macroArgs = args["args"].split(',')

        try:
            self.run_script(args["name"])
        except Exception as e:
            self.set_return_value("{ERROR: %s}" % str(e))

    def get_macro_arguments(self):
        """
        Get the arguments supplied to the current script via its macro

        Usage: C{engine.get_macro_arguments()}

        @return: the arguments
        @rtype: C{list(str())}
        """
        return self.__macroArgs

    def set_return_value(self, val):
        """
        Store a return value to be used by a phrase macro

        Usage: C{engine.set_return_value(val)}

        @param val: value to be stored
        """
        self.__returnValue = val

    def get_return_value(self):
        """
        Used internally by AutoKey for phrase macros
        """
        ret = self.__returnValue
        self.__returnValue = ''
        return ret

    def _set_triggered_abbreviation(self, abbreviation: str, trigger_character: str):
        """
        Used internally by AutoKey to provide the abbreviation and trigger that caused the script to execute.
        @param abbreviation: Abbreviation that caused the script to execute
        @param trigger_character: Possibly empty "trigger character". As defined in the abbreviation configuration.
        """
        self._triggered_abbreviation = abbreviation
        self._triggered_character = trigger_character

    def get_triggered_abbreviation(self) -> Tuple[Optional[str], Optional[str]]:
        """
        This function can be queried by a script to get the abbreviation text that triggered it’s execution.

        If a script is triggered by an abbreviation, this function returns a tuple containing two strings. First element
        is the abbreviation text. The second element is the trigger character that finally caused the execution. It is
        typically some whitespace character, like ' ', '\t' or a newline character. It is empty, if the abbreviation was
        configured to "trigger immediately".

        If the script execution was triggered by a hotkey, a call to the DBus interface, the tray icon, the "Run"
        button in the main window or any other means, this function returns a tuple containing two None values.

        Usage: C{abbreviation, trigger_character = engine.get_triggered_abbreviation()}
        You can determine if the script was triggered by an abbreviation by simply testing the truth value of the first
        returned value.

        @return: Abbreviation that triggered the script execution, if any.
        @rtype: C{Tuple[Optional[str], Optional[str]]}
        """
        return self._triggered_abbreviation, self._triggered_character
