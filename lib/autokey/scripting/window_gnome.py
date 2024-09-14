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

"""Extremely basic window management. Requires autokey gnome extension"""

import re
import subprocess
import time
from .abstract_window import AbstractWindow

#TODO review how desktop/workspace switching works with gnome extension. I think this may be in "workspace"

class Window(AbstractWindow):
    """
    Extremely basic Window management with gnome autokey extension
    """

    def __init__(self, mediator):
        self.mediator = mediator

    def wait_for_focus(self, title, timeOut=5):
        """
        """
        raise NotImplementedError

    def wait_for_exist(self, title, timeOut=5, by_hex=False):
        """
        """
        raise NotImplementedError

    def activate(self, title, switchDesktop=False, matchClass=False, by_hex=False):
        """
        Activate the specified window, giving it input focus

        Usage: C{window.activate(title, switchDesktop=False, matchClass=False)}

        If switchDesktop is False (default), the window will be moved to the current desktop and activated. Otherwise, switch to the window's current desktop and activate it there.

        :param title: window title to match against (as case-insensitive substring match)
        :param switchDesktop: not supported for gnome extension
        :param matchClass: if True, match on the window class instead of the title
        :param by_hex: not supported for gnome extension
        """
        if switchDesktop or by_hex:
            raise NotImplementedError

        windows = self.get_window_list()
        for window in windows:
            if not matchClass and title in window.get('wm_title'):
                self.mediator.windowInterface.activate_window(window.get('id'))
            elif matchClass and title in window.get('wm_class'):
                self.mediator.windowInterface.activate_window(window.get('id'))
        return

    def close(self, title, matchClass=False, by_hex=False):
        """
        Close the specified window gracefully

        Usage: C{window.close(title, matchClass=False)}

        :param title: window title to match against (as case-insensitive substring match)
        :param matchClass: if True, match on the window class instead of the title
        :param by_hex: not supported for gnome extension
        """

        windows = self.get_window_list()
        for window in windows:
            #TODO regex support
            if not matchClass and title in window.get('wm_title'):
                self.mediator.windowInterface.close_window(window.get('id'))
            elif matchClass and title in window.get('wm_class'):
                self.mediator.windowInterface.close_window(window.get('id'))
        return

    def resize_move(self, title, xOrigin=-1, yOrigin=-1, width=-1, height=-1, matchClass=False, by_hex=False):
        """
        """
        raise NotImplementedError

    def move_to_desktop(self, title, deskNum, matchClass=False, by_hex=False):
        """
        """
        raise NotImplementedError

    def switch_desktop(self, deskNum):
        """
        """
        raise NotImplementedError

    def set_property(self, title, action, prop, matchClass=False, by_hex=False):
        """
        """
        raise NotImplementedError

    def get_active_geometry(self):
        """
        """
        raise NotImplementedError

    def get_active_title(self):
        """
        Get the visible title of the currently active window

        Usage: C{window.get_active_title()}

        :return: the visible title of the currentle active window
        :rtype: C{str}
        """
        return self.mediator.windowInterface.get_window_title()

    def get_active_class(self):
        """
        Get the class of the currently active window

        Usage: C{window.get_active_class()}

        :return: the class of the currently active window
        :rtype: C{str}
        """
        return self.mediator.windowInterface.get_window_class()

    def center_window(self, title=":ACTIVE:", win_width=None, win_height=None, monitor=0, matchClass=False, by_hex=False):
        """
        """
        raise NotImplementedError

    def get_window_list(self, filter_desktop=-1):
        """
        Returns a list of windows matching an optional desktop filter, requires C{wmctrl}!

        Each list item consists of: C{[hexid, desktop, hostname, title]}

        Where the C{hexid} is the ID used for some other functions (like L{import -window} from ImageMagick).

        C{desktop} is the number of which desktop (sometimes called workspaces) the window appears upon.

        C{hostname} is the hostname of your computer.

        C{title} is the title that you would usually see in your window manager of choice.

        :param filter_desktop: Not currently supported
        :return: C{[[hexid1, desktop1, hostname1, title1], [hexid2,desktop2,hostname2,title2], ...etc]} Returns C{[]} if no windows are found.
        """
        if filter_desktop!=-1:
            raise NotImplementedError
        return self.mediator.windowInterface.get_window_list()

    def get_window_hex(self, title):
        """
        """
        raise NotImplementedError




    def get_window_geometry(self, title, by_hex=False):
        """
        """

        raise NotImplementedError
