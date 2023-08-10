# Copyright (C) 2023 sebastiansam55
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
"""
Abstract interface for dialog interactions.
This is an abstraction layer for platform dependent dialog handling.
It unifies dialog handling for Qt, GTK and headless autokey UIs.
"""

from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path

logger = __import__("autokey.logger").logger.get_logger(__name__)

class AbstractDialog(ABC):
    __metaclass__ = ABCMeta
    """
    Abstract interface for dialog interactions.
    This is an abstraction layer for platform dependent dialog handling.
    It unifies dialog handling for Qt, GTK and headless autokey UIs.
    """

    def send_notification(self, title, message, icon="autokey", timeout="10", **kwargs):
        """
        Sends a passive popup (notification) using C{kdialog}

        @param title: Title to be used in the notification
        @param message: Message to be displayed in the notification
        @param icon: Icon to be used in the notification (Defaults to "autokey")
        @param timeout: How long the notification will be on screen (Defaults to 10)
        @return: A tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        return

    def info_dialog(self, title="Information", message="", **kwargs):
        """
        Show an information dialog

        Usage: C{dialog.info_dialog(title="Information", message="", **kwargs)}

        @param title: window title for the dialog
        @param message: message displayed in the dialog
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        return

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
        return

    def password_dialog(self, title="Enter password", message="Enter password", **kwargs):
        """
        Show a password input dialog

        Usage: C{dialog.password_dialog(title="Enter password", message="Enter password", **kwargs)}

        @param title: window title for the dialog
        @param message: message displayed above the password input box
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        return

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
        return

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
        return

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
        return

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
        return
    
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
        return


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
        return

    def choose_colour(self, title="Select Colour", **kwargs):
        """
        Show a Colour Chooser dialog

        Usage: C{dialog.choose_colour(title="Select Colour")}

        @param title: window title for the dialog
        @return: a tuple containing the exit code and colour
        @rtype: C{DialogData(int, str)}
        """
        return

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
        return
