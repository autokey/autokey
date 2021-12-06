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
Abstract interface for clipboard interactions.
This is an abstraction layer for platform dependent clipboard handling.
It unifies clipboard handling for Qt, GTK and headless autokey UIs.
"""

from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path

logger = __import__("autokey.logger").logger.get_logger(__name__)

class AbstractClipboard(ABC):
    __metaclass__ = ABCMeta
    """
    Abstract interface for clipboard interactions.
    This is an abstraction layer for platform dependent clipboard handling.
    It unifies clipboard handling for Qt, GTK and headless autokey UIs.
    """
    @abstractmethod
    def fill_clipboard(self, contents: str):
        """
        Copy text into the clipboard

        Usage: C{clipboard.fill_clipboard(contents)}

        @param contents: string to be placed in the selection
        """
        return
    @abstractmethod
    def get_clipboard(self):
        """
        Read text from the clipboard

        Usage: C{clipboard.get_clipboard()}

        @return: text contents of the clipboard
        @rtype: C{str}
        """
        return

    @abstractmethod
    def fill_selection(self, contents: str):
        """
        Copy text into the X selection

        Usage: C{clipboard.fill_selection(contents)}

        @param contents: string to be placed in the selection
        """
        return
    @abstractmethod
    def get_selection(self):
        """
        Read text from the X selection
        The X selection refers to the currently highlighted text.

        Usage: C{clipboard.get_selection()}

        @return: text contents of the mouse selection
        @rtype: C{str}
        """
        return

    @abstractmethod
    def set_clipboard_image(self, path: str):
        """
        Set clipboard to image

        Usage: C{clipboard.set_clipboard_image(path)}

        @param path: Path to image file
        @raise OSError: If path does not exist
        """
        return
