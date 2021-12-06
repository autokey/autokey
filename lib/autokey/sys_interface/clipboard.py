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

from abc import ABC, ABCMeta, abstractmethod

from autokey import common
from autokey.scripting import Clipboard as APIClipboard

logger = __import__("autokey.logger").logger.get_logger(__name__)

class AbstractClipboard(ABC):
    __metaclass__ = ABCMeta
    """
    Abstract interface for clipboard interactions.
    This is an abstraction layer for platform dependent clipboard handling.
    It unifies clipboard handling for Qt, GTK and headless autokey UIs.
    Usage:
    c = Clipboard()
    # set clipboard
    c.text = "string"
    # get clipboard
    print(c.text)
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


class Clipboard(AbstractClipboard):

    def __init__(self):
        self.cb = APIClipboard()

    @property
    def text(self):
        return self.cb.get_clipboard()
    @text.setter
    def text(self, new_content: str):
        self.cb.fill_clipboard(new_content)

    @property
    def selection(self):
        return self.cb.get_selection()
    @selection.setter
    def selection(self, new_content: str):
        self.cb.fill_selection(new_content)
