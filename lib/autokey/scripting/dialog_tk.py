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

import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

from tkcalendar import Calendar, DateEntry


from autokey.scripting.common import DialogData, ColourData

from autokey.scripting.abstract_dialog import AbstractDialog


class TkDialog(AbstractDialog):
    """
    Provides a simple interface for the display of some basic dialogs to collect information from the user.

    This version uses KDialog to integrate well with KDE. To pass additional arguments to KDialog that are
    not specifically handled, use keyword arguments. For example, to pass the --geometry argument to KDialog
    to specify the desired size of the dialog, pass C{geometry="700x400"} as one of the parameters. All
    keyword arguments must be given as strings.

    A note on exit codes: an exit code of 0 indicates that the user clicked OK.
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
        #TODO/RFC tk does not offer a notification system, should this be a window or use a different library?
        TkNotification(title, message, icon)
        #raise NotImplementedError

    def info_dialog(self, title="Information", message="", **kwargs):
        """
        Show an information dialog

        Usage: C{dialog.info_dialog(title="Information", message="", **kwargs)}

        @param title: window title for the dialog
        @param message: message displayed in the dialog
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """

        messagebox.showinfo(title, message)

    

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

        result = simpledialog.askstring(title, message, initialvalue=default)
        if result is not None:
            return (1, result)
        else:
            return (0, "")
        

        

    def password_dialog(self, title="Enter password", message="Enter password", **kwargs):
        """
        Show a password input dialog

        Usage: C{dialog.password_dialog(title="Enter password", message="Enter password", **kwargs)}

        @param title: window title for the dialog
        @param message: message displayed above the password input box
        @return: a tuple containing the exit code and user input
        @rtype: C{DialogData(int, str)}
        """
        result = simpledialog.askstring(title, message, show="*")
        if result is not None:
            return (1, result)
        else:
            return (0, "")

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
        raise NotImplementedError

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

        raise NotImplementedError

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

        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError

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
        return (0, filedialog.askdirectory(title=title, initialdir=initialDir))

    def choose_colour(self, title="Select Colour", **kwargs):
        """
        Show a Colour Chooser dialog

        Usage: C{dialog.choose_colour(title="Select Colour")}

        @param title: window title for the dialog
        @return: a tuple containing the exit code and colour
        @rtype: C{DialogData(int, str)}
        """
        raise NotImplementedError

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
        cal = TkCalendar()
        return cal.get_date()


class TkCalendar:
    def __init__(self):
        self.root = tk.Tk()
        self.result = None

        cal = Calendar(self.root, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.pack()

        self.date_entry = DateEntry(self.root, width=12, background='darkblue',
                       foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_entry.pack(pady=10)

        # add an "OK" button to the window
        button_ok = tk.Button(self.root, text="OK", command=self.on_ok)
        button_ok.pack(pady=10)

        self.root.mainloop()

    def on_ok(self):
        self.result = self.date_entry.get()
        self.root.destroy()

    def get_date(self):
        return self.result
    
class TkColorChooser:
    def __init__(self):
        pass

class TkNotification:
    def __init__(self, title="Notification", message="Notification Message", icon=None):
        # Create the main window
        root = tk.Tk()
        root.title(title)

        # Set the window size and position it in the center of the screen
        #TODO handle multiple monitors?
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        x = (width - 400) // 2
        y = (height - 200) // 2
        root.geometry('400x200+{}+{}'.format(x, y))

        # Create a frame to hold the notification message
        message_frame = tk.Frame(root)
        message_frame.pack(side=tk.TOP, pady=20)

        # Create a label to display the message
        message_label = tk.Label(message_frame, text=message, font=("Helvetica", 16))
        message_label.pack(side=tk.TOP, padx=20, pady=20)

        # Create a button to close the notification
        button = tk.Button(root, text="Close", command=root.destroy, width=10)
        button.pack(side=tk.BOTTOM, pady=20)

        # Set the background color and remove the window border
        root.configure(background='#f0f0f0')
        root.overrideredirect(True)

        # Set the window to stay on top of other windows
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)

        # Start the main loop
        root.mainloop()