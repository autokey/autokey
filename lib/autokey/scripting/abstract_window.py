# Copyright (C) 2024 sebastiansam55
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
Abstract interface for window interactions.
This is an abstraction layer for platform dependent window handling.
It unifies window handling for X11, Wayland (gnome based) desktop environments.
"""

from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path

logger = __import__("autokey.logger").logger.get_logger(__name__)

class AbstractWindow(ABC):
    __metaclass__ = ABCMeta
    """
    Abstract interface for window interactions.
    This is an abstraction layer for platform dependent window handling.
    It unifies window handling for X11, Wayland (gnome based) desktop environments.
    """
    @abstractmethod
    def wait_for_focus(self, title, timeOut=5):
        return
    @abstractmethod
    def wait_for_exist(self, title, timeOut=5, by_hex=False):
        return
    @abstractmethod
    def activate(self, title, switchDesktop=False, matchClass=False, by_hex=False):
        return
    @abstractmethod
    def close(self, title, matchClass=False, by_hex=False):
        return
    @abstractmethod
    def get_active_geometry(self):
        return
    @abstractmethod
    def get_active_title(self):
        return
    @abstractmethod
    def get_active_class(self):
        return
    @abstractmethod
    def get_window_list(self, filter_desktop=-1):
        return
    @abstractmethod
    def get_window_geometry(self, title, by_hex=False):
        return