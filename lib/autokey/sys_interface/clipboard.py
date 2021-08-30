# Copyright (C) 2011 Chris Dekter, 2021 BlueDrink9
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

from autokey import common


# Platform abstraction; Allows code like `import scripting.Dialog`
if common.USED_UI_TYPE == "QT":
    from autokey.scripting.clipboard_qt import QtClipboard as APIClipboard
elif common.USED_UI_TYPE == "GTK":
    from autokey.scripting.clipboard_gtk import GtkClipboard as APIClipboard
elif common.USED_UI_TYPE == "headless":
    from autokey.scripting.clipboard_tkinter import TkClipboard as APIClipboard

logger = __import__("autokey.logger").logger.get_logger(__name__)

if common.USED_UI_TYPE == "QT":
    from PyQt5.QtGui import QClipboard
    from PyQt5.QtWidgets import QApplication
elif common.USED_UI_TYPE == "GTK":
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk

    try:
        gi.require_version('Atspi', '2.0')
        import pyatspi
        HAS_ATSPI = True
    except ImportError:
        HAS_ATSPI = False
    except ValueError:
        HAS_ATSPI = False
    except SyntaxError:  # pyatspi 2.26 fails when used with Python 3.7
        HAS_ATSPI = False
elif common.USED_UI_TYPE == "headless":
    pass

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


if common.USED_UI_TYPE == "QT":
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

elif common.USED_UI_TYPE == "GTK":
    class Clipboard(AbstractClipboard):
        def __init__(self):
            self.cb = APIClipboard()

        @property
        def text(self):
            return self.cb.get_clipboard()
        @text.setter
        def text(self, new_content: str):
            self.cb.set_clipboard(new_content)

        @property
        def selection(self):
            return self.cb.get_selection()
        @selection.setter
        def selection(self, new_content: str):
            self.cb.fill_selection(new_content)

elif common.USED_UI_TYPE == "headless":
    # TODO headless app clipboard?
    class Clipboard(AbstractClipboard):
        def __init__(self):
            pass

        @property
        def text(self):
            # return self._clipboard.text(QClipboard.Clipboard)
            return ""

        @text.setter
        def text(self, new_content: str):
            # self._clipboard.setText(new_content, QClipboard.Clipboard)
            pass


        @property
        def selection(self):
            return ""
            # return self._clipboard.text(QClipboard.Selection)

        @selection.setter
        def selection(self, new_content: str):
            # self._clipboard.setText(new_content, QClipboard.Selection)
            pass
