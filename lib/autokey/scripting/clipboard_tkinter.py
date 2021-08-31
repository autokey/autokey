# Copyright (C) 2021 BlueDrink9
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
"""
try:
    from Tkinter import Tk
except ImportError:
    from tkinter import Tk
from pathlib import Path

from autokey.scripting.abstract_clipboard import AbstractClipboard

logger = __import__("autokey.logger").logger.get_logger(__name__)

class TkClipboard(AbstractClipboard):
    """
    Read/write access to the X selection and clipboard
    """

    def __init__(self, app=None):
        """
        Initialize the tkinter version of the Clipboard

        Usage: Called when TkClipboard is imported
        """
        self.tkroot = Tk()
        self.tkroot.withdraw()

    def fill_selection(self, contents):
        """
        Copy text into the X selection

        Usage: C{clipboard.fill_selection(contents)}

        @param contents: string to be placed in the selection
        """
        logger.error("Headless app clipboard does not support setting selection clipboard")
        pass


    def get_selection(self):
        """
        Read text from the X selection

        The X selection refers to the currently highlighted text.

        Usage: C{clipboard.get_selection()}

        @return: text contents of the mouse selection
        @rtype: C{str}
        """
        text = self.tkroot.selection_get(selection="PRIMARY")
        if text is not None:
            return text
        else:
            logger.warning("No text found in X selection")
            return ""

    def fill_clipboard(self, contents):
        """
        Copy text into the clipboard

        Usage: C{clipboard.fill_clipboard(contents)}

        @param contents: string to be placed in the selection
        """
        self.tkroot.clipboard_clear()
        self.tkroot.clipboard_append(contents)
        self.tkroot.update()

        # If code is run from within e.g. an ipython qt console, invoking Tk root's mainloop() may hang the console.
        # r.mainloop() # the Tk root's mainloop() must be invoked.
        # r.destroy()

    def get_clipboard(self):
        """
        Read text from the clipboard

        Usage: C{clipboard.get_clipboard()}

        @return: text contents of the clipboard
        @rtype: C{str}
        """
        text = self.tkroot.selection_get(selection="CLIPBOARD")
        if text is not None:
            return text
        else:
            logger.warning("No text found on clipboard")
            return ""

    def set_clipboard_image(self, path):
        """
        Set clipboard to image

        Usage: C{clipboard.set_clipboard_image(path)}

        @param path: Path to image file
        """
        logger.error("Headless app clipboard does not support setting clipboard to image.")
        pass
