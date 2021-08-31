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
"""
GtkClipboard Functions
"""

from gi.repository import Gtk, Gdk

from pathlib import Path

from autokey.scripting.abstract_clipboard import AbstractClipboard

logger = __import__("autokey.logger").logger.get_logger(__name__)

class GtkClipboard(AbstractClipboard):
    """
    Read/write access to the X selection and clipboard - GTK version
    """

    def __init__(self, app=None):
        """
        Initialize the Gtk version of the Clipboard

        Usage: Called when GtkClipboard is imported

        @param app: refers to the application instance
        """

        self._clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        """
        Refers to the data contained in the Gtk Clipboard (conventional clipboard)
        """
        self._selection = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        """
        Refers to the "selection" of the clipboard or the highlighted text
        """
        self.app = app
        """
        Refers to the application instance
        """

    def fill_selection(self, contents):
        """
        Copy C{contents} into the X selection

        Usage: C{clipboard.fill_selection(contents)}

        @param contents: string to be placed in the selection
        """
        Gdk.threads_enter()
        try:
            # This call might fail and raise an Exception.
            # If it does, make sure to release the mutex and not deadlock AutoKey.
            self._selection.set_text(contents, -1)
        finally:
            Gdk.threads_leave()

    def get_selection(self):
        """
        Read text from the X selection

        The X selection refers to the currently highlighted text.

        Usage: C{clipboard.get_selection()}

        @return: text contents of the mouse selection
        @rtype: C{str}
        """
        Gdk.threads_enter()
        text = self._selection.wait_for_text()
        Gdk.threads_leave()
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
        Gdk.threads_enter()
        if Gtk.get_major_version() >= 3:
            self._clipboard.set_text(contents, -1)
        else:
            self._clipboard.set_text(contents)
        Gdk.threads_leave()

    def get_clipboard(self):
        """
        Read text from the clipboard

        Usage: C{clipboard.get_clipboard()}

        @return: text contents of the clipboard
        @rtype: C{str}
        """
        Gdk.threads_enter()
        text = self._clipboard.wait_for_text()
        Gdk.threads_leave()
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
        @raise OSError: If path does not exist

        """
        image_path = Path(path).expanduser()
        if image_path.exists():
            Gdk.threads_enter()
            copied_image = Gtk.Image.new_from_file(str(image_path))
            self.clipBoard.set_image(copied_image.get_pixbuf())
            Gdk.threads_leave()
        else:
            raise OSError("Image file not found")


