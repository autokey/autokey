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

from abc import abstractmethod

from . import common

if common.USING_QT:
    from PyQt5.QtGui import QClipboard
    from PyQt5.QtWidgets import QApplication
else:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk

logger = __import__("autokey.logger").logger.get_logger(__name__)

class AbstractClipboard:
    """
    Abstract interface for clipboard interactions.
    This is an abstraction layer for platform dependent clipboard handling.
    It unifies clipboard handling for Qt and GTK.
    """
    @property
    @abstractmethod
    def text(self):
        """Get and set the keyboard clipboard content."""
        return

    @property
    @abstractmethod
    def selection(self):
        """Get and set the mouse selection clipboard content."""
        return


if common.USING_QT:
    class Clipboard(AbstractClipboard):
        def __init__(self):
            self._clipboard = QApplication.clipboard()

        @property
        def text(self):
            return self._clipboard.text(QClipboard.Clipboard)

        @text.setter
        def text(self, new_content: str):
            self._clipboard.setText(new_content, QClipboard.Clipboard)

        @property
        def selection(self):
            return self._clipboard.text(QClipboard.Selection)

        @selection.setter
        def selection(self, new_content: str):
            self._clipboard.setText(new_content, QClipboard.Selection)

else:
    class Clipboard(AbstractClipboard):
        def __init__(self):
            self._clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            self._selection = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)

        @property
        def text(self):
            Gdk.threads_enter()
            text = self._clipboard.wait_for_text()
            Gdk.threads_leave()
            return text

        @text.setter
        def text(self, new_content: str):
            Gdk.threads_enter()
            try:
                # This call might fail and raise an Exception.
                # If it does, make sure to release the mutex and not deadlock AutoKey.
                self._clipboard.set_text(new_content, -1)
            finally:
                Gdk.threads_leave()

        @property
        def selection(self):
            Gdk.threads_enter()
            text = self._selection.wait_for_text()
            Gdk.threads_leave()
            return text

        @selection.setter
        def selection(self, new_content: str):
            Gdk.threads_enter()
            try:
                # This call might fail and raise an Exception.
                # If it does, make sure to release the mutex and not deadlock AutoKey.
                self._selection.set_text(new_content, -1)
            finally:
                Gdk.threads_leave()
