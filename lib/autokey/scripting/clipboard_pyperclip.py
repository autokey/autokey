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
PyperclipClipboard Functions
"""

import threading
from pathlib import Path

import pyperclip

import autokey.common
from autokey.scripting.abstract_clipboard import AbstractClipboard

logger = __import__("autokey.logger").logger.get_logger(__name__)

# pyperclip normally binds copy()/paste() lazily on first use, so that
# importing it doesn't force a clipboard mechanism to be chosen before the
# caller has a chance to override it. That lazy stub's signature doesn't
# accept the primary= kwarg fill_selection()/get_selection() need below, so
# if one of those happens to be the very first pyperclip call this process
# ever makes, it crashes with a TypeError instead of ever reaching the real
# xclip/wl-copy backend (confirmed live: any AutoKey session where a
# SELECTION-mode phrase fires before a CB_CTRL_V-mode one does). Binding the
# real backend eagerly here avoids the lazy stub entirely.
pyperclip.copy, pyperclip.paste = pyperclip.determine_clipboard()


class PyperclipClipboard(AbstractClipboard):
    """
    Read/write access to the X selection and clipboard, via pyperclip.

    One implementation for all front ends (GTK, Qt, headless), replacing
    the previous per-toolkit classes plus their GNOME Shell extension and
    klipper D-Bus fallbacks. Those fallbacks existed because GTK's/Qt's own
    clipboard APIs make a Wayland wl_data_device.set_selection() request
    that needs a real input-event serial to offer, which AutoKey does not
    have as a background daemon with no focused surface of its own when a
    hotkey fires in another application -- GNOME's/KDE's compositors
    silently reject the request (confirmed live via WAYLAND_DEBUG=1
    tracing). pyperclip instead shells out to xclip/wl-copy/wl-paste as a
    detached background process, which claims the selection through a
    different mechanism not subject to that rejection (X11 has no such
    requirement at all; wl-copy uses the wlr-data-control protocol
    extension, designed specifically for background clients like this).
    """

    def __init__(self, app=None):
        """
        Initialize the pyperclip-backed Clipboard

        Usage: Called when PyperclipClipboard is imported

        :param app: refers to the application instance. Unused for text
            clipboard/selection access -- kept only so this class is a
            drop-in replacement for the toolkit-specific Clipboard classes
            it replaces, and to dispatch set_clipboard_image() onto Qt's
            main thread the same way the old QtClipboard did.
        """
        self.app = app

    def fill_clipboard(self, contents: str):
        """
        Copy text into the clipboard

        Usage: C{clipboard.fill_clipboard(contents)}

        :param contents: string to be placed in the clipboard
        """
        pyperclip.copy(contents)

    def get_clipboard(self) -> str:
        """
        Read text from the clipboard

        Usage: C{clipboard.get_clipboard()}

        :return: text contents of the clipboard
        :rtype: C{str}
        """
        text = pyperclip.paste()
        if not text:
            logger.warning("No text found on clipboard")
        return text or ""

    def fill_selection(self, contents: str):
        """
        Copy text into the X selection

        Usage: C{clipboard.fill_selection(contents)}

        :param contents: string to be placed in the selection
        """
        pyperclip.copy(contents, primary=True)

    def get_selection(self) -> str:
        """
        Read text from the X selection

        The X selection refers to the currently highlighted text.

        Usage: C{clipboard.get_selection()}

        :return: text contents of the mouse selection
        :rtype: C{str}
        """
        text = pyperclip.paste(primary=True)
        if not text:
            logger.warning("No text found in X selection")
        return text or ""

    def set_clipboard_image(self, path: str):
        """
        Set clipboard to image

        Usage: C{clipboard.set_clipboard_image(path)}

        :param path: Path to image file
        :raise OSError: If path does not exist

        pyperclip is text-only, so this delegates to the same GTK/Qt
        image-setting logic the toolkit-specific Clipboard classes this
        replaces used to use, chosen by the running front end.
        """
        image_path = Path(path).expanduser()
        if not image_path.exists():
            raise OSError("Image file not found")
        if autokey.common.USED_UI_TYPE == "QT":
            self.__set_clipboard_image_qt(image_path)
        elif autokey.common.USED_UI_TYPE == "GTK":
            self.__set_clipboard_image_gtk(image_path)
        else:
            logger.error("Headless app clipboard does not support setting clipboard to image.")

    def __set_clipboard_image_gtk(self, image_path: Path):
        from gi.repository import Gtk, Gdk
        Gdk.threads_enter()
        try:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            copied_image = Gtk.Image.new_from_file(str(image_path))
            clipboard.set_image(copied_image.get_pixbuf())
        finally:
            Gdk.threads_leave()

    def __set_clipboard_image_qt(self, image_path: Path):
        if self.app:
            sem = threading.Semaphore(0)

            def do_set():
                self.__do_set_clipboard_image_qt(image_path)
                sem.release()

            self.app.exec_in_main(do_set)
            sem.acquire()
        else:
            self.__do_set_clipboard_image_qt(image_path)

    @staticmethod
    def __do_set_clipboard_image_qt(image_path: Path):
        from PyQt5.QtGui import QImage
        from PyQt5.QtWidgets import QApplication
        copied_image = QImage()
        copied_image.load(str(image_path))
        QApplication.clipboard().setImage(copied_image)
