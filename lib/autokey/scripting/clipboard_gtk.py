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

import autokey.common
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

        :param app: refers to the application instance
        """

        self._clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        """
        Refers to the data contained in the Gtk Clipboard (conventional clipboard)
        """
        self._selection = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        """
        Refers to the selection of the clipboard or the highlighted text
        """
        self.app = app
        """
        Refers to the application instance
        """
        self._gnome_clipboard_interface = None
        """
        Lazily-created connection to the AutoKey GNOME Shell extension's
        SetClipboardText D-Bus method. Only used on GNOME Wayland -- see
        _use_gnome_extension_for_clipboard_set().
        """

    def _use_gnome_extension_for_clipboard_set(self) -> bool:
        """
        On GNOME Wayland, GTK's own clipboard-set call is a normal Wayland
        client request that Mutter rejects outright: AutoKey is a background
        daemon with no focused surface of its own when a hotkey fires in
        another application, so it has no input-event serial to offer, and
        Gtk.Clipboard.set_text() silently has no effect (confirmed live via
        WAYLAND_DEBUG=1 tracing -- wl_data_device.set_selection() called with
        serial 0, cancelled by the compositor immediately). The AutoKey GNOME
        Shell extension can set the clipboard on our behalf instead, because
        the Shell is the compositor, not an ordinary client, and does not
        need to make that same claim. This particular GTK-on-GNOME check
        only applies here; KDE's Qt-based clipboard has the same underlying
        problem on Wayland, but is worked around separately in
        clipboard_qt.py (see QtClipboard._use_klipper_for_clipboard_set()).
        """
        return autokey.common.SESSION_TYPE == "wayland" and autokey.common.DESKTOP != "KDE"

    def _get_gnome_clipboard_interface(self):
        if self._gnome_clipboard_interface is None:
            from autokey.gnome_interface import GnomeClipboardInterface
            self._gnome_clipboard_interface = GnomeClipboardInterface()
        return self._gnome_clipboard_interface

    def fill_selection(self, contents):
        """
        Copy C{contents} into the X selection

        Usage: C{clipboard.fill_selection(contents)}

        :param contents: string to be placed in the selection
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
        Read text from the selection

        Refers to the currently-highlighted text

        Usage: C{clipboard.get_selection()}

        :return: text contents of the mouse selection
        :rtype: C{str}
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

        :param contents: string to be placed in the selection

        On GNOME Wayland specifically, this is routed through the AutoKey
        GNOME Shell extension's SetClipboardText D-Bus method instead of
        GTK's own Gtk.Clipboard.set_text(). GTK's Wayland clipboard backend
        calls wl_data_device.set_selection() with a serial of 0 (no real
        input-event serial available, since AutoKey is a background daemon
        with no focused surface of its own when a hotkey fires in some
        other application), and Mutter immediately cancels the resulting
        wl_data_source -- confirmed live via WAYLAND_DEBUG=1 tracing. The
        Shell itself is not an ordinary Wayland client and does not need to
        make that same claim, so setting the clipboard from inside the
        extension avoids the rejection entirely. See
        _use_gnome_extension_for_clipboard_set() and
        GnomeClipboardInterface in gnome_interface.py. This path is
        GNOME-only; X11 and headless are unaffected either way. KDE's
        Qt-based clipboard (clipboard_qt.py) has the same underlying
        rejection on Wayland, worked around there via klipper's D-Bus
        service instead -- see QtClipboard's
        _use_klipper_for_clipboard_set(). An earlier version of this
        comment claimed KDE's Qt clipboard did not have this problem;
        that was never actually verified against the clipboard (as
        opposed to selection) path and was wrong.
        """
        if self._use_gnome_extension_for_clipboard_set():
            self._get_gnome_clipboard_interface().set_clipboard_text(contents)
            return
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

        :return: text contents of the clipboard
        :rtype: C{str}
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

        :param path: path to image file
        :raise OSError: if path does not exist

        """
        image_path = Path(path).expanduser()
        if image_path.exists():
            Gdk.threads_enter()
            copied_image = Gtk.Image.new_from_file(str(image_path))
            self.clipBoard.set_image(copied_image.get_pixbuf())
            Gdk.threads_leave()
        else:
            raise OSError("Image file not found")


