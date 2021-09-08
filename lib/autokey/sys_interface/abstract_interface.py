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

from abc import ABC, ABCMeta, abstractmethod
import typing

from autokey import common
from autokey.scripting import Clipboard as APIClipboard

logger = __import__("autokey.logger").logger.get_logger(__name__)

# This tuple is used to return requested window properties.
WindowInfo = typing.NamedTuple("WindowInfo", [("wm_title", str), ("wm_class", str)])

class AbstractSysInterface(ABC, metaclass=ABCMeta):
    """
    This class aims to define all the methods needed to interact with the underlying
    key system. (eg X11, via some underlying library like XRecord)
    """

    # @abstractmethod
    # def look_up_key_string(self, key_code, shifted, num_lock, modifiers):
    #     return
    @abstractmethod
    def flush(self):
        return
    @abstractmethod
    def cancel(self):
        return
    @abstractmethod
    def on_keys_changed(self):
        """
        Update interface when keyboard layout changes.
        """
        return

    @abstractmethod
    def handle_keypress(self, keyCode):
        return
    @abstractmethod
    def handle_keyrelease(self, keyCode):
        return
    @abstractmethod
    def grab_keyboard(self):
        return
    @abstractmethod
    def ungrab_keyboard(self):
        return
    @abstractmethod
    def grab_hotkey(self, item):
        return
    @abstractmethod
    def ungrab_hotkey(self, item):
        return

    @abstractmethod
    def send_string(self, string):
        return
    @abstractmethod
    def send_key(self, key_name):
        return
    @abstractmethod
    def send_modified_key(self, key_name, modifiers):
        return
    @abstractmethod
    def press_key(self, key_name):
        return
    def release_key(self, key_name):
        return
    @abstractmethod
    def fake_keydown(self, key_name):
        return
    @abstractmethod
    def fake_keyup(self, key_name):
        return
    @abstractmethod
    def fake_keypress(self, key_name):
        return

class AbstractMouseInterface(ABC, metaclass=ABCMeta):
    """
    This class aims to define all the methods needed to interact with the underlying
    mouse system. (eg X11)
    """

    @abstractmethod
    def send_mouse_click(self, xCoord, yCoord, button, relative):
        return
    @abstractmethod
    def mouse_press(self, xCoord, yCoord, button):
        return
    @abstractmethod
    def mouse_release(self, xCoord, yCoord, button):
        return
    @abstractmethod
    def mouse_location(self):
        return
    @abstractmethod
    def relative_mouse_location(self, window=None):
        return
    @abstractmethod
    def scroll_down(self, number):
        return
    @abstractmethod
    def scroll_up(self, number):
        return
    @abstractmethod
    def move_cursor(self, xCoord, yCoord, relative=False, relative_self=False):
        return
    @abstractmethod
    def send_mouse_click_relative(self, xoff, yoff, button):
        return
    @abstractmethod
    def handle_mouseclick(self, button, x, y):
        return

class AbstractWindowInterface(ABC, metaclass=ABCMeta):
    """
    This class aims to define all the methods needed to interact with the underlying
    window system. (eg X11)
    """

    @abstractmethod
    def get_window_info(self, window=None, traverse: bool=True) -> WindowInfo:
        return
    @abstractmethod
    def get_window_title(self, window=None, traverse=True) -> str:
        return
    @abstractmethod
    def get_window_class(self, window=None, traverse=True) -> str:
        return
