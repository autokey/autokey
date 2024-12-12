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

"""Class for creating Qt dialogs"""

import subprocess

from autokey.scripting.common import DialogData, ColourData


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
