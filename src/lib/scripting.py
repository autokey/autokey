# -*- coding: utf-8 -*-

# Copyright (C) 2009 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import subprocess

class Keyboard:
    """
    Provides access to the keyboard for event generation.
    """
    
    def __init__(self, mediator):
        self.mediator = mediator
        
    def send_keys(self, keyString):
        """
        Send a sequence of keys via keyboard event
        
        Usage: C{keyboard.send_keys(keyString)}
        
        @param keyString: string of keys (including special keys) to send
        """
        self.mediator.send_string(keyString)
        
    def send_key(self, key, repeat=1):
        """
        Send a keyboard event
        
        Usage: C{keyboard.send_key(key, repeat=1)}
        
        @param key: they key to be sent (e.g. "s" or "<enter>")
        @param repeat: number of times to repeat the key event
        """        
        for x in range(repeat):
            self.mediator.send_key(key)
            
            
class Store(dict):
    """
    Allows persistent storage of values between invocations of the script.
    """
    
    def set_value(self, key, value):
        """
        Store a value
        
        Usage: C{store.set_value(key, value)}
        """
        self[key] = value
        
    def get_value(self, key):
        """
        Get a value
        
        Usage: C{store.get_value(key)}
        """
        return self[key]        
        
    def remove_value(self, key):
        """
        Remove a value
        
        Usage: C{store.remove_value(key)}
        """
        del self[key]
        
class Dialog:
    """
    Provides a simple interface for the display of some basic dialogs to collect information from the user.
    """
    
    def __runKdialog(self, title, args):
        p = subprocess.Popen(["kdialog", "--title", title] + args, stdout=subprocess.PIPE)
        retCode = p.wait()
        output = p.stdout.read()[:-1] # Drop trailing newline
        
        return (retCode, output)
        
    def input_dialog(self, title="Enter a value", message="Enter a value", default=""):
        """
        Show an input dialog
        
        Usage: C{dialog.input_dialog(title="Enter a value", message="Enter a value", default="")}
        
        @param title: window title for the dialog
        @param message: message displayed above the input box
        @param default: default value for the input box
        """
        return self.__runKdialog(title, ["--inputbox", message, default])
        
    def password_dialog(self, title="Enter password", message="Enter password"):
        """
        Show a password input dialog
        
        Usage: C{dialog.password_dialog(title="Enter password", message="Enter password")}
        
        @param title: window title for the dialog
        @param message: message displayed above the password input box
        """
        return self.__runKdialog(title, ["--password", message])        
        
    def combo_menu(self, options, title="Choose an option", message="Choose an option"):
        """
        Show a combobox menu
        
        Usage: C{dialog.combo_menu(options, title="Choose an option", message="Choose an option")}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the combobox      
        """
        return self.__runKdialog(title, ["--combobox", message] + options)
        
    def list_menu(self, options, title="Choose a value", message="Choose a value", default=None):
        """
        Show a single-selection list menu
        
        Usage: C{dialog.list_menu(options, title="Choose a value", message="Choose a value", default=None)}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the list
        @param default: default value to be selected
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
            
        retCode, result = self.__runKdialog(title, ["--radiolist", message] + choices)
        choice = options[int(result)]
        
        return retCode, choice        
        
    def list_menu_multi(self, options, title="Choose one or more values", message="Choose one or more values", defaults=[]):
        """
        Show a multiple-selection list menu
        
        Usage: C{dialog.list_menu_multi(options, title="Choose one or more values", message="Choose one or more values", defaults=[])}
        
        @param options: list of options (strings) for the dialog
        @param title: window title for the dialog
        @param message: message displayed above the list
        @param defaults: list of default values to be selected
        """
        
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
            
        retCode, output = self.__runKdialog(title, ["--separate-output", "--checklist", message] + choices)
        results = output.split()
    
        choices = []
        for index in results:
            choices.append(options[int(index)])
        
        return retCode, choices
        
    def open_file(self, title="Open File", initialDir="~", fileTypes="*|All Files", rememberAs=None):
        """
        Show an Open File dialog
        
        Usage: C{dialog.open_file(title="Open File", initialDir="~", fileTypes="*|All Files", rememberAs=None)}
        
        @param title: window title for the dialog
        @param initialDir: starting directory for the file dialog
        @param fileTypes: file type filter expression
        @param rememberAs: gives an ID to this file dialog, allowing it to open at the last used path next time
        """
        if rememberAs is not None:
            return self.__runKdialog(title, ["--getopenfilename", initialDir, fileTypes, ":" + rememberAs])
        else:
            return self.__runKdialog(title, ["--getopenfilename", initialDir, fileTypes])
        
    def save_file(self, title="Save As", initialDir="~", fileTypes="*|All Files", rememberAs=None):
        """
        Show an Save As dialog
        
        Usage: C{dialog.save_file(title="Save As", initialDir="~", fileTypes="*|All Files", rememberAs=None)}
        
        @param title: window title for the dialog
        @param initialDir: starting directory for the file dialog
        @param fileTypes: file type filter expression
        @param rememberAs: gives an ID to this file dialog, allowing it to open at the last used path next time
        """
        if rememberAs is not None:
            return self.__runKdialog(title, ["--getsavefilename", initialDir, fileTypes, ":" + rememberAs])
        else:
            return self.__runKdialog(title, ["--getsavefilename", initialDir, fileTypes])

    def choose_directory(self, title="Select Directory", initialDir="~", rememberAs=None):
        """
        Show a Directory Chooser dialog
        
        Usage: C{dialog.choose_directory(title="Select Directory", initialDir="~", rememberAs=None)}
        
        @param title: window title for the dialog
        @param initialDir: starting directory for the directory chooser dialog
        @param rememberAs: gives an ID to this file dialog, allowing it to open at the last used path next time
        """
        if rememberAs is not None:
            return self.__runKdialog(title, ["--getexistingdirectory", initialDir, ":" + rememberAs])
        else:
            return self.__runKdialog(title, ["--getexistingdirectory", initialDir])
        
    def choose_colour(self, title="Select Colour"):
        """
        Show a Colour Chooser dialog
        
        Usage: C{dialog.choose_colour(title="Select Colour")}
        
        @param title: window title for the dialog
        """
        return self.__runKdialog(title, ["--getcolor"])
        