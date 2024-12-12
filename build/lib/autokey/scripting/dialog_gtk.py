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

"""Class for creating Gtk Window dialogs"""

import re
import subprocess

from autokey.scripting.common import DialogData, ColourData


class GtkDialog:
    """
    Provides a simple interface for the display of some basic dialogs to collect information from the user.

    This version uses Zenity to integrate well with GNOME. To pass additional arguments to Zenity that are
    not specifically handled, use keyword arguments. For example, to pass the --timeout argument to Zenity
    pass C{timeout="15"} as one of the parameters. All keyword arguments must be given as strings.

    @note: Exit codes: an exit code of 0 indicates that the user clicked OK.
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
