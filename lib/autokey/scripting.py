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

import subprocess
import threading
import time
import re
from typing import NamedTuple, Union, List

from autokey import common, model
from autokey import iomediator

if common.USING_QT:
    from PyQt5.QtGui import QClipboard
    from PyQt5.QtWidgets import QApplication
else:
    from gi.repository import Gtk, Gdk


class ColourData(NamedTuple("ColourData", (("r", int), ("g", int), ("b", int)))):
    """Colour data type for colour chooser dialogs."""
    @property
    def hex_code(self) -> str:
        return "{0:02x}{1:02x}{2:02x}".format(self.r, self.g, self.b)

    @property
    def html_code(self) -> str:
        """Converts the ColourData into a HTML-style colour, equivalent to the KDialog output."""
        return "#" + self.hex_code

    @property
    def zenity_tuple_str(self) -> str:
        """Converts the ColourData into a tuple-like string, equivalent to the Zenity output. ("rgb(R, G, B)")"""
        return "rgb({})".format(",".join(map(str,self)))

    @staticmethod
    def from_html(html_style_colour_str: str):
        """
        Parser for KDialog output, which outputs a HTML style hex code like #55aa00
        @param html_style_colour_str: HTML style hex string encoded colour. (#rrggbb)
        @return: ColourData instance
        @rtype: ColourData
        """
        html_style_colour_str = html_style_colour_str.lstrip("#")
        components = list(map("".join, zip(*[iter(html_style_colour_str)]*2)))
        return ColourData(*(int(colour, 16) for colour in components))

    @staticmethod
    def from_zenity_tuple_str(zenity_tuple_str: str):
        """
        Parser for Zenity output, which outputs a named tuple-like string: "rgb(R, G, B)", where R, G, B are base10
        integers.
        @param zenity_tuple_str: tuple-like string: "rgb(r, g, b), where r, g, b are base10 integers.
        @return: ColourData instance
        @rtype: ColourData
        """
        components = zenity_tuple_str.strip("rgb()").split(",")
        return ColourData(*map(int, components))


class DialogData(NamedTuple("DialogData", (("return_code", int), ("data", Union[ColourData, str, List[str], None])))):
    """"""
    @property
    def successful(self) -> bool:
        """
        Returns True, if the dialog execution was successful, i.e. KDialog or Zenity exited with a zero return value.
        This includes:
        - Command line parameters are correct
        - Execution is otherwise successful (Can open X Display, load shared libraries, etc.)
        - The user clicked on OK or otherwise 'accepted' the dialog.
        """
        return self.return_code == 0


class Keyboard:
    """
    Provides access to the keyboard for event generation.
    """
    
    def __init__(self, mediator):
        self.mediator = mediator
        
    def send_keys(self, keyString):
        """
        Send a sequence of keys via keyboard events
        
        Usage: C{keyboard.send_keys(keyString)}
        
        @param keyString: string of keys (including special keys) to send
        """
        assert type(keyString) is str
        self.mediator.interface.begin_send()
        try:
            self.mediator.send_string(keyString)
        finally:
            self.mediator.interface.finish_send()
        
    def send_key(self, key, repeat=1):
        """
        Send a keyboard event
        
        Usage: C{keyboard.send_key(key, repeat=1)}
        
        @param key: they key to be sent (e.g. "s" or "<enter>")
        @param repeat: number of times to repeat the key event
        """        
        for _ in range(repeat):
            self.mediator.send_key(key)
        self.mediator.flush()
        
    def press_key(self, key):
        """
        Send a key down event
        
        Usage: C{keyboard.press_key(key)}
        
        The key will be treated as down until a matching release_key() is sent.
        @param key: they key to be pressed (e.g. "s" or "<enter>")
        """
        self.mediator.press_key(key)
        
    def release_key(self, key):
        """
        Send a key up event
        
        Usage: C{keyboard.release_key(key)}
        
        If the specified key was not made down using press_key(), the event will be 
        ignored.
        @param key: they key to be released (e.g. "s" or "<enter>")
        """
        self.mediator.release_key(key)

    def fake_keypress(self, key, repeat=1):
        """
        Fake a keypress

        Usage: C{keyboard.fake_keypress(key, repeat=1)}

        Uses XTest to 'fake' a keypress. This is useful to send keypresses to some
        applications which won't respond to keyboard.send_key()

        @param key: they key to be sent (e.g. "s" or "<enter>")
        @param repeat: number of times to repeat the key event
        """
        for _ in range(repeat):
            self.mediator.fake_keypress(key)
            
    def wait_for_keypress(self, key, modifiers: list=None, timeOut=10.0):
        """
        Wait for a keypress or key combination
        
        Usage: C{keyboard.wait_for_keypress(self, key, modifiers=[], timeOut=10.0)}
        
        Note: this function cannot be used to wait for modifier keys on their own

        @param key: they key to wait for
        @param modifiers: list of modifiers that should be pressed with the key
        @param timeOut: maximum time, in seconds, to wait for the keypress to occur
        """
        if modifiers is None:
            modifiers = []
        w = iomediator.Waiter(key, modifiers, None, timeOut)
        return w.wait()
        

class Mouse:
    """
    Provides access to send mouse clicks
    """
    def __init__(self, mediator: iomediator.IoMediator):
        self.mediator = mediator
        self.interface = mediator.interface
    
    def click_relative(self, x, y, button):
        """
        Send a mouse click relative to the active window
        
        Usage: C{mouse.click_relative(x, y, button)}
        
        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        @param button: mouse button to simulate (left=1, middle=2, right=3)
        """
        self.interface.send_mouse_click(x, y, button, True)
        
    def click_relative_self(self, x, y, button):
        """
        Send a mouse click relative to the current mouse position
        
        Usage: C{mouse.click_relative_self(x, y, button)}
        
        @param x: x-offset in pixels, relative to current mouse position
        @param y: y-offset in pixels, relative to current mouse position
        @param button: mouse button to simulate (left=1, middle=2, right=3)
        """
        self.interface.send_mouse_click_relative(x, y, button)
        
    def click_absolute(self, x, y, button):
        """
        Send a mouse click relative to the screen (absolute)
        
        Usage: C{mouse.click_absolute(x, y, button)}
        
        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        @param button: mouse button to simulate (left=1, middle=2, right=3)
        """
        self.interface.send_mouse_click(x, y, button, False)
        
    def wait_for_click(self, button, timeOut=10.0):
        """
        Wait for a mouse click
        
        Usage: C{mouse.wait_for_click(self, button, timeOut=10.0)}

        @param button: they mouse button click to wait for as a button number, 1-9
        @param timeOut: maximum time, in seconds, to wait for the keypress to occur
        """
        button = int(button)
        w = iomediator.Waiter(None, None, button, timeOut)
        w.wait()


class QtDialog:
    """
    Provides a simple interface for the display of some basic dialogs to collect information from the user.
    
    This version uses KDialog to integrate well with KDE. To pass additional arguments to KDialog that are 
    not specifically handled, use keyword arguments. For example, to pass the --geometry argument to KDialog
    to specify the desired size of the dialog, pass C{geometry="700x400"} as one of the parameters. All
    keyword arguments must be given as strings.

    A note on exit codes: an exit code of 0 indicates that the user clicked OK.
    """
    
    def _run_kdialog(self, title, args, kwargs) -> DialogData:
        for k, v in kwargs.items():
            args.append("--" + k)
            args.append(v)

        with subprocess.Popen(
                ["kdialog", "--title", title] + args,
                stdout=subprocess.PIPE,
                universal_newlines=True) as p:
            output = p.communicate()[0][:-1]  # type: str # Drop trailing newline
            return_code = p.returncode
        
        return DialogData(return_code, output)

    def info_dialog(self, title="Information", message="", **kwargs):
        """
        Show an information dialog

        Usage: C{dialog.info_dialog(title="Information", message="", **kwargs)}

        @param title: window title for the dialog
        @param message: message displayed in the dialog
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        return self._run_kdialog(title, ["--msgbox", message], kwargs)
        
    def input_dialog(self, title="Enter a value", message="Enter a value", default="", **kwargs):
        """
        Show an input dialog
        
        Usage: C{dialog.input_dialog(title="Enter a value", message="Enter a value", default="", **kwargs)}
        
        @param title: window title for the dialog
        @param message: message displayed above the input box
        @param default: default value for the input box
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        return self._run_kdialog(title, ["--inputbox", message, default], kwargs)
        
    def password_dialog(self, title="Enter password", message="Enter password", **kwargs):
        """
        Show a password input dialog
        
        Usage: C{dialog.password_dialog(title="Enter password", message="Enter password", **kwargs)}
        
        @param title: window title for the dialog
        @param message: message displayed above the password input box
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        return self._run_kdialog(title, ["--password", message], kwargs)
        
    def combo_menu(self, options, title="Choose an option", message="Choose an option", **kwargs):
        """
        Show a combobox menu
        
        Usage: C{dialog.combo_menu(options, title="Choose an option", message="Choose an option", **kwargs)}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the combobox
        @return: a tuple containing the exit code and user choice
        @rtype: C{DialogData(int, str)}
        """
        return self._run_kdialog(title, ["--combobox", message] + options, kwargs)
        
    def list_menu(self, options, title="Choose a value", message="Choose a value", default=None, **kwargs):
        """
        Show a single-selection list menu
        
        Usage: C{dialog.list_menu(options, title="Choose a value", message="Choose a value", default=None, **kwargs)}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the list
        @param default: default value to be selected
        @return: a tuple containing the exit code and user choice
        @rtype: C{DialogData(int, str)}
        """
        
        choices = []
        optionNum = 0
        for option in options:
            choices.append(str(optionNum))
            choices.append(option)
            if option == default:
                choices.append("on")
            else:
                choices.append("off")
            optionNum += 1
            
        return_code, result = self._run_kdialog(title, ["--radiolist", message] + choices, kwargs)
        choice = options[int(result)]
        
        return DialogData(return_code, choice)
        
    def list_menu_multi(self, options, title="Choose one or more values", message="Choose one or more values",
                        defaults: list=None, **kwargs):
        """
        Show a multiple-selection list menu
        
        Usage: C{dialog.list_menu_multi(options, title="Choose one or more values", message="Choose one or more values", defaults=[], **kwargs)}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the list
        @param defaults: list of default values to be selected
        @return: a tuple containing the exit code and user choice
        @rtype: C{DialogData(int, List[str])}
        """

        if defaults is None:
            defaults = []
        choices = []
        optionNum = 0
        for option in options:
            choices.append(str(optionNum))
            choices.append(option)
            if option in defaults:
                choices.append("on")
            else:
                choices.append("off")
            optionNum += 1
            
        return_code, output = self._run_kdialog(title, ["--separate-output", "--checklist", message] + choices, kwargs)
        results = output.split()

        choices = [options[int(choice_index)] for choice_index in results]
        
        return DialogData(return_code, choices)
        
    def open_file(self, title="Open File", initialDir="~", fileTypes="*|All Files", rememberAs=None, **kwargs):
        """
        Show an Open File dialog
        
        Usage: C{dialog.open_file(title="Open File", initialDir="~", fileTypes="*|All Files", rememberAs=None, **kwargs)}
        
        @param title: window title for the dialog
        @param initialDir: starting directory for the file dialog
        @param fileTypes: file type filter expression
        @param rememberAs: gives an ID to this file dialog, allowing it to open at the last used path next time
        @return: a tuple containing the exit code and file path
        @rtype: C{DialogData(int, str)}
        """
        if rememberAs is not None:
            return self._run_kdialog(title, ["--getopenfilename", initialDir, fileTypes, ":" + rememberAs], kwargs)
        else:
            return self._run_kdialog(title, ["--getopenfilename", initialDir, fileTypes], kwargs)
        
    def save_file(self, title="Save As", initialDir="~", fileTypes="*|All Files", rememberAs=None, **kwargs):
        """
        Show a Save As dialog
        
        Usage: C{dialog.save_file(title="Save As", initialDir="~", fileTypes="*|All Files", rememberAs=None, **kwargs)}
        
        @param title: window title for the dialog
        @param initialDir: starting directory for the file dialog
        @param fileTypes: file type filter expression
        @param rememberAs: gives an ID to this file dialog, allowing it to open at the last used path next time
        @return: a tuple containing the exit code and file path
        @rtype: C{DialogData(int, str)}
        """
        if rememberAs is not None:
            return self._run_kdialog(title, ["--getsavefilename", initialDir, fileTypes, ":" + rememberAs], kwargs)
        else:
            return self._run_kdialog(title, ["--getsavefilename", initialDir, fileTypes], kwargs)

    def choose_directory(self, title="Select Directory", initialDir="~", rememberAs=None, **kwargs):
        """
        Show a Directory Chooser dialog
        
        Usage: C{dialog.choose_directory(title="Select Directory", initialDir="~", rememberAs=None, **kwargs)}
        
        @param title: window title for the dialog
        @param initialDir: starting directory for the directory chooser dialog
        @param rememberAs: gives an ID to this file dialog, allowing it to open at the last used path next time
        @return: a tuple containing the exit code and chosen path
        @rtype: C{DialogData(int, str)}
        """
        if rememberAs is not None:
            return self._run_kdialog(title, ["--getexistingdirectory", initialDir, ":" + rememberAs], kwargs)
        else:
            return self._run_kdialog(title, ["--getexistingdirectory", initialDir], kwargs)
        
    def choose_colour(self, title="Select Colour", **kwargs):
        """
        Show a Colour Chooser dialog
        
        Usage: C{dialog.choose_colour(title="Select Colour")}
        
        @param title: window title for the dialog
        @return: a tuple containing the exit code and colour
        @rtype: C{DialogData(int, str)}
        """
        return_data = self._run_kdialog(title, ["--getcolor"], kwargs)
        if return_data.successful:
            return DialogData(return_data.return_code, ColourData.from_html(return_data.data))
        else:
            return DialogData(return_data.return_code, None)

    def calendar(self, title="Choose a date", format_str="%Y-%m-%d", date="today", **kwargs):
        """
        Show a calendar dialog

        Usage: C{dialog.calendar_dialog(title="Choose a date", format="%Y-%m-%d", date="YYYY-MM-DD", **kwargs)}

        Note: the format and date parameters are not currently used

        @param title: window title for the dialog
        @param format_str: format of date to be returned
        @param date: initial date as YYYY-MM-DD, otherwise today
        @return: a tuple containing the exit code and date
        @rtype: C{DialogData(int, str)}
        """
        return self._run_kdialog(title, ["--calendar", title], kwargs)
        
        
class System:
    """
    Simplified access to some system commands.
    """    
    
    def exec_command(self, command, getOutput=True):
        """
        Execute a shell command
        
        Usage: C{system.exec_command(command, getOutput=True)}

        Set getOutput to False if the command does not exit and return immediately. Otherwise
        AutoKey will not respond to any hotkeys/abbreviations etc until the process started
        by the command exits.
        
        @param command: command to be executed (including any arguments) - e.g. "ls -l"
        @param getOutput: whether to capture the (stdout) output of the command
        @raise subprocess.CalledProcessError: if the command returns a non-zero exit code
        """
        if getOutput:
            with subprocess.Popen(
                    command,
                    shell=True,
                    bufsize=-1,
                    stdout=subprocess.PIPE,
                    universal_newlines=True) as p:
                output = p.communicate()[0]
                if output.endswith("\n"):
                    # Most shell output has a new line at the end, which we
                    # don't want. Drop the trailing newline character,
                    # if the command output something that ends on "\n"
                    output = output[:-1]
                if p.returncode:
                    raise subprocess.CalledProcessError(p.returncode, output)
                return output
        else:
            subprocess.Popen(command, shell=True, bufsize=-1)
    
    def create_file(self, fileName, contents=""):
        """
        Create a file with contents
        
        Usage: C{system.create_file(fileName, contents="")}
        
        @param fileName: full path to the file to be created
        @param contents: contents to insert into the file
        """
        with open(fileName, "w") as written_file:
            written_file.write(contents)


class GtkDialog:
    """
    Provides a simple interface for the display of some basic dialogs to collect information from the user.
    
    This version uses Zenity to integrate well with GNOME. To pass additional arguments to Zenity that are 
    not specifically handled, use keyword arguments. For example, to pass the --timeout argument to Zenity
    pass C{timeout="15"} as one of the parameters. All keyword arguments must be given as strings.

    A note on exit codes: an exit code of 0 indicates that the user clicked OK.
    """
    
    def _run_zenity(self, title, args, kwargs) -> DialogData:
        for k, v in kwargs.items():
            args.append("--" + k)
            args.append(v)

        with subprocess.Popen(
                        ["zenity", "--title", title] + args,
                        stdout=subprocess.PIPE,
                        universal_newlines=True) as p:
            output = p.communicate()[0][:-1]  # type: str # Drop trailing newline
            return_code = p.returncode

        return DialogData(return_code, output)
    
    def info_dialog(self, title="Information", message="", **kwargs):
        """
        Show an information dialog
        
        Usage: C{dialog.info_dialog(title="Information", message="", **kwargs)}
        
        @param title: window title for the dialog
        @param message: message displayed in the dialog
        @return: a tuple containing the exit code and user input
        @rtype: C{tuple(int, str)}
        """
        return self._run_zenity(title, ["--info", "--text", message], kwargs)
        
    def input_dialog(self, title="Enter a value", message="Enter a value", default="", **kwargs):
        """
        Show an input dialog
        
        Usage: C{dialog.input_dialog(title="Enter a value", message="Enter a value", default="", **kwargs)}
        
        @param title: window title for the dialog
        @param message: message displayed above the input box
        @param default: default value for the input box
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        return self._run_zenity(title, ["--entry", "--text", message, "--entry-text", default], kwargs)
        
    def password_dialog(self, title="Enter password", message="Enter password", **kwargs):
        """
        Show a password input dialog
        
        Usage: C{dialog.password_dialog(title="Enter password", message="Enter password")}
        
        @param title: window title for the dialog
        @param message: message displayed above the password input box
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        return self._run_zenity(title, ["--entry", "--text", message, "--hide-text"], kwargs)
        
    #def combo_menu(self, options, title="Choose an option", message="Choose an option"):
        """
        Show a combobox menu - not supported by zenity
        
        Usage: C{dialog.combo_menu(options, title="Choose an option", message="Choose an option")}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the combobox      
        """
        #return self._run_zenity(title, ["--combobox", message] + options)
        
    def list_menu(self, options, title="Choose a value", message="Choose a value", default=None, **kwargs):
        """
        Show a single-selection list menu
        
        Usage: C{dialog.list_menu(options, title="Choose a value", message="Choose a value", default=None, **kwargs)}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the list
        @param default: default value to be selected
        @return: a tuple containing the exit code and user choice
        @rtype: C{DialogData(int, str)}
        """
        
        choices = []
        for option in options:
            if option == default:
                choices.append("TRUE")
            else:
                choices.append("FALSE")
                
            choices.append(option)

        return self._run_zenity(
            title,
            ["--list", "--radiolist", "--text", message, "--column", " ", "--column", "Options"] + choices,
            kwargs)
        
    def list_menu_multi(self, options, title="Choose one or more values", message="Choose one or more values",
                        defaults: list=None, **kwargs):
        """
        Show a multiple-selection list menu
        
        Usage: C{dialog.list_menu_multi(options, title="Choose one or more values", message="Choose one or more values", defaults=[], **kwargs)}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the list
        @param defaults: list of default values to be selected
        @return: a tuple containing the exit code and user choice
        @rtype: C{DialogData(int, List[str])}
        """

        if defaults is None:
            defaults = []
        choices = []
        for option in options:
            if option in defaults:
                choices.append("TRUE")
            else:
                choices.append("FALSE")
                
            choices.append(option)
        return_code, output = self._run_zenity(
            title,
            ["--list", "--checklist", "--text", message, "--column", " ", "--column", "Options"] + choices,
            kwargs)
        results = output.split('|')

        return DialogData(return_code, results)
        
    def open_file(self, title="Open File", **kwargs):
        """
        Show an Open File dialog
        
        Usage: C{dialog.open_file(title="Open File", **kwargs)}
        
        @param title: window title for the dialog
        @return: a tuple containing the exit code and file path
        @rtype: C{DialogData(int, str)}
        """
        #if rememberAs is not None:
        #    return self._run_zenity(title, ["--getopenfilename", initialDir, fileTypes, ":" + rememberAs])
        #else:
        return self._run_zenity(title, ["--file-selection"], kwargs)
        
    def save_file(self, title="Save As", **kwargs):
        """
        Show a Save As dialog
        
        Usage: C{dialog.save_file(title="Save As", **kwargs)}
        
        @param title: window title for the dialog
        @return: a tuple containing the exit code and file path
        @rtype: C{DialogData(int, str)}
        """
        #if rememberAs is not None:
        #    return self._run_zenity(title, ["--getsavefilename", initialDir, fileTypes, ":" + rememberAs])
        #else:
        return self._run_zenity(title, ["--file-selection", "--save"], kwargs)
        
    def choose_directory(self, title="Select Directory", initialDir="~", **kwargs):
        """
        Show a Directory Chooser dialog
        
        Usage: C{dialog.choose_directory(title="Select Directory", **kwargs)}
        
        @param title: window title for the dialog
        @param initialDir:
        @return: a tuple containing the exit code and path
        @rtype: C{DialogData(int, str)}
        """
        #if rememberAs is not None:
        #    return self._run_zenity(title, ["--getexistingdirectory", initialDir, ":" + rememberAs])
        #else:
        return self._run_zenity(title, ["--file-selection", "--directory"], kwargs)

    def choose_colour(self, title="Select Colour", **kwargs):
        """
        Show a Colour Chooser dialog
        
        Usage: C{dialog.choose_colour(title="Select Colour")}
        
        @param title: window title for the dialog
        @return:
        @rtype: C{DialogData(int, Optional[ColourData])}
        """
        return_data = self._run_zenity(title, ["--color-selection"], kwargs)
        if return_data.successful:
            converted_colour = ColourData.from_zenity_tuple_str(return_data.data)
            return DialogData(return_data.return_code, converted_colour)
        else:
            return DialogData(return_data.return_code, None)
        
    def calendar(self, title="Choose a date", format_str="%Y-%m-%d", date="today", **kwargs):
        """
        Show a calendar dialog
        
        Usage: C{dialog.calendar_dialog(title="Choose a date", format="%Y-%m-%d", date="YYYY-MM-DD", **kwargs)}
        
        @param title: window title for the dialog
        @param format_str: format of date to be returned
        @param date: initial date as YYYY-MM-DD, otherwise today
        @return: a tuple containing the exit code and date
        @rtype: C{DialogData(int, str)}
        """
        if re.match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date):
            year = date[0:4]
            month = date[5:7]
            day = date[8:10]
            date_args = ["--year=" + year, "--month=" + month, "--day=" + day]
        else:
            date_args = []
        return self._run_zenity(title, ["--calendar", "--date-format=" + format_str] + date_args, kwargs)

    
class QtClipboard:
    """
    Read/write access to the X selection and clipboard - QT version
    """
    
    def __init__(self, app):
        self.clipBoard = QApplication.clipboard()
        self.app = app
        
    def fill_selection(self, contents):
        """
        Copy text into the X selection
        
        Usage: C{clipboard.fill_selection(contents)}
        
        @param contents: string to be placed in the selection
        """
        self.__execAsync(self.__fillSelection, contents)
        
    def __fillSelection(self, string):
        self.clipBoard.setText(string, QClipboard.Selection)
        self.sem.release()
        
    def get_selection(self):
        """
        Read text from the X selection
        
        Usage: C{clipboard.get_selection()}

        @return: text contents of the mouse selection
        @rtype: C{str}
        """
        self.__execAsync(self.__getSelection)
        return str(self.text)
        
    def __getSelection(self):
        self.text = self.clipBoard.text(QClipboard.Selection)
        self.sem.release()
        
    def fill_clipboard(self, contents):
        """
        Copy text into the clipboard
        
        Usage: C{clipboard.fill_clipboard(contents)}
        
        @param contents: string to be placed in the selection
        """
        self.__execAsync(self.__fillClipboard, contents)
        
    def __fillClipboard(self, string):
        self.clipBoard.setText(string, QClipboard.Clipboard)
        self.sem.release()        
        
    def get_clipboard(self):
        """
        Read text from the clipboard
        
        Usage: C{clipboard.get_clipboard()}

        @return: text contents of the clipboard
        @rtype: C{str}
        """
        self.__execAsync(self.__getClipboard)
        return str(self.text)
        
    def __getClipboard(self):
        self.text = self.clipBoard.text(QClipboard.Clipboard)
        self.sem.release()
        
    def __execAsync(self, callback, *args):
        self.sem = threading.Semaphore(0)
        self.app.exec_in_main(callback, *args)
        self.sem.acquire()        
        
        
class GtkClipboard:
    """
    Read/write access to the X selection and clipboard - GTK version
    """
    
    def __init__(self, app):
        self.clipBoard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.selection = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        self.app = app
        
    def fill_selection(self, contents):
        """
        Copy text into the X selection
        
        Usage: C{clipboard.fill_selection(contents)}
        
        @param contents: string to be placed in the selection
        """
        #self.__execAsync(self.__fillSelection, contents)
        self.__fillSelection(contents)
        
    def __fillSelection(self, string):
        Gdk.threads_enter()
        self.selection.set_text(string, -1)
        Gdk.threads_leave()
        #self.sem.release()
        
    def get_selection(self):
        """
        Read text from the X selection
        
        Usage: C{clipboard.get_selection()}

        @return: text contents of the mouse selection
        @rtype: C{str}
        @raise Exception: if no text was found in the selection
        """
        Gdk.threads_enter()
        text = self.selection.wait_for_text()
        Gdk.threads_leave()
        if text is not None:
            return text
        else:
            raise Exception("No text found in X selection")
        
    def fill_clipboard(self, contents):
        """
        Copy text into the clipboard
        
        Usage: C{clipboard.fill_clipboard(contents)}
        
        @param contents: string to be placed in the selection
        """
        Gdk.threads_enter()
        if Gtk.get_major_version() >= 3:
            self.clipBoard.set_text(contents, -1)
        else:
            self.clipBoard.set_text(contents)
        Gdk.threads_leave()      
        
    def get_clipboard(self):
        """
        Read text from the clipboard
        
        Usage: C{clipboard.get_clipboard()}

        @return: text contents of the clipboard
        @rtype: C{str}
        @raise Exception: if no text was found on the clipboard
        """
        Gdk.threads_enter()
        text = self.clipBoard.wait_for_text()
        Gdk.threads_leave()
        if text is not None:
            return text
        else:
            raise Exception("No text found on clipboard")

        
class Window:
    """
    Basic window management using wmctrl
    
    Note: in all cases where a window title is required (with the exception of wait_for_focus()), 
    two special values of window title are permitted:
    
    :ACTIVE: - select the currently active window
    :SELECT: - select the desired window by clicking on it
    """
    
    def __init__(self, mediator):
        self.mediator = mediator
        
    def wait_for_focus(self, title, timeOut=5):
        """
        Wait for window with the given title to have focus
        
        Usage: C{window.wait_for_focus(title, timeOut=5)}
        
        If the window becomes active, returns True. Otherwise, returns False if
        the window has not become active by the time the timeout has elapsed.
        
        @param title: title to match against (as a regular expression)
        @param timeOut: period (seconds) to wait before giving up
        @rtype: boolean
        """
        regex = re.compile(title)
        waited = 0
        while waited <= timeOut:
            if regex.match(self.mediator.interface.get_window_title()):
                return True
            
            if timeOut == 0:
                break  # zero length timeout, if not matched go straight to end
                
            time.sleep(0.3)
            waited += 0.3
            
        return False
        
    def wait_for_exist(self, title, timeOut=5):
        """
        Wait for window with the given title to be created
        
        Usage: C{window.wait_for_exist(title, timeOut=5)}

        If the window is in existence, returns True. Otherwise, returns False if
        the window has not been created by the time the timeout has elapsed.
        
        @param title: title to match against (as a regular expression)
        @param timeOut: period (seconds) to wait before giving up
        @rtype: boolean
        """
        regex = re.compile(title)
        waited = 0
        while waited <= timeOut:
            retCode, output = self._run_wmctrl(["-l"])
            for line in output.split('\n'):
                if regex.match(line[14:].split(' ', 1)[-1]):
                    return True
                    
            if timeOut == 0:
                break  # zero length timeout, if not matched go straight to end

            time.sleep(0.3)
            waited += 0.3
            
        return False
        
    def activate(self, title, switchDesktop=False, matchClass=False):
        """
        Activate the specified window, giving it input focus

        Usage: C{window.activate(title, switchDesktop=False, matchClass=False)}
        
        If switchDesktop is False (default), the window will be moved to the current desktop
        and activated. Otherwise, switch to the window's current desktop and activate it there.
        
        @param title: window title to match against (as case-insensitive substring match)
        @param switchDesktop: whether or not to switch to the window's current desktop
        @param matchClass: if True, match on the window class instead of the title
        """
        if switchDesktop:
            args = ["-a", title]
        else:
            args = ["-R", title]
        if matchClass:
            args += ["-x"]
        self._run_wmctrl(args)
        
    def close(self, title, matchClass=False):
        """
        Close the specified window gracefully
        
        Usage: C{window.close(title, matchClass=False)}
        
        @param title: window title to match against (as case-insensitive substring match)
        @param matchClass: if True, match on the window class instead of the title
        """
        if matchClass:
            self._run_wmctrl(["-c", title, "-x"])
        else:
            self._run_wmctrl(["-c", title])
        
    def resize_move(self, title, xOrigin=-1, yOrigin=-1, width=-1, height=-1, matchClass=False):
        """
        Resize and/or move the specified window
        
        Usage: C{window.close(title, xOrigin=-1, yOrigin=-1, width=-1, height=-1, matchClass=False)}

        Leaving and of the position/dimension values as the default (-1) will cause that
        value to be left unmodified.
        
        @param title: window title to match against (as case-insensitive substring match)
        @param xOrigin: new x origin of the window (upper left corner)
        @param yOrigin: new y origin of the window (upper left corner)
        @param width: new width of the window
        @param height: new height of the window
        @param matchClass: if True, match on the window class instead of the title
        """
        mvArgs = ["0", str(xOrigin), str(yOrigin), str(width), str(height)]
        if matchClass:
            xArgs = ["-x"]
        else:
            xArgs = []
        self._run_wmctrl(["-r", title, "-e", ','.join(mvArgs)] + xArgs)
        
    def move_to_desktop(self, title, deskNum, matchClass=False):
        """
        Move the specified window to the given desktop
        
        Usage: C{window.move_to_desktop(title, deskNum, matchClass=False)}
        
        @param title: window title to match against (as case-insensitive substring match)
        @param deskNum: desktop to move the window to (note: zero based)
        @param matchClass: if True, match on the window class instead of the title
        """
        if matchClass:
            xArgs = ["-x"]
        else:
            xArgs = []
        self._run_wmctrl(["-r", title, "-t", str(deskNum)] + xArgs)

    def switch_desktop(self, deskNum):
        """
        Switch to the specified desktop
        
        Usage: C{window.switch_desktop(deskNum)}
        
        @param deskNum: desktop to switch to (note: zero based)
        """
        self._run_wmctrl(["-s", str(deskNum)])
        
    def set_property(self, title, action, prop, matchClass=False):
        """
        Set a property on the given window using the specified action

        Usage: C{window.set_property(title, action, prop, matchClass=False)}
        
        Allowable actions: C{add, remove, toggle}
        Allowable properties: C{modal, sticky, maximized_vert, maximized_horz, shaded, skip_taskbar,
        skip_pager, hidden, fullscreen, above}
       
        @param title: window title to match against (as case-insensitive substring match)
        @param action: one of the actions listed above
        @param prop: one of the properties listed above
        @param matchClass: if True, match on the window class instead of the title
        """
        if matchClass:
            xArgs = ["-x"]
        else:
            xArgs = []
        self._run_wmctrl(["-r", title, "-b" + action + ',' + prop] + xArgs)
        
    def get_active_geometry(self):
        """
        Get the geometry of the currently active window
        
        Usage: C{window.get_active_geometry()}
        
        @return: a 4-tuple containing the x-origin, y-origin, width and height of the window (in pixels)
        @rtype: C{tuple(int, int, int, int)}
        """
        active = self.mediator.interface.get_window_title()
        result, output = self._run_wmctrl(["-l", "-G"])
        matchingLine = None
        for line in output.split('\n'):
            if active in line[34:].split(' ', 1)[-1]:
                matchingLine = line
                
        if matchingLine is not None:
            output = matchingLine.split()[2:6]
            # return [int(x) for x in output]
            return list(map(int, output))
        else:
            return None

    def get_active_title(self):
        """
        Get the visible title of the currently active window
        
        Usage: C{window.get_active_title()}
        
        @return: the visible title of the currentle active window
        @rtype: C{str}
        """
        return self.mediator.interface.get_window_title()
    
    def get_active_class(self):
        """
        Get the class of the currently active window
        
        Usage: C{window.get_active_class()}
        
        @return: the class of the currentle active window
        @rtype: C{str}
        """
        return self.mediator.interface.get_window_class()
        
    def _run_wmctrl(self, args):
        try:
            with subprocess.Popen(["wmctrl"] + args, stdout=subprocess.PIPE) as p:
                output = p.communicate()[0].decode()[:-1]  # Drop trailing newline
                returncode = p.returncode
        except FileNotFoundError:
            return 1, 'ERROR: Please install wmctrl'

        return returncode, output
        
        
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
