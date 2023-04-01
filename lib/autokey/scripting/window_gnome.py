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
Abstract interface for window interactions.
This is an abstraction layer for platform dependent window handling.
"""

from autokey.scripting.abstract_window import AbstractWindow

import time
import re


class WindowGnome(AbstractWindow):
    """
    Basic window management using a GNOME extension via dbus

    Initial implementation using:
    https://github.com/sebastiansam55/autokey-gnome-extension

    Have to look into publication of the extension as well.
    """

    def __init__(self, mediator):
        self.mediator = mediator
        self.windowInterface = self.mediator.windowInterface

        #TODO if the gnome shell crashes these need to be reinitialized, not sure how to handle that scenario

        

    def wait_for_focus(self, title, timeOut=5):
        """
        Wait for window with the given title to have focus

        Usage: C{window.wait_for_focus(title, timeOut=5)}

        If the window becomes active, returns True. Otherwise, returns False if
        the window has not become active by the time the timeout has elapsed.

        @param title: title to match against (as a regular expression)
        @param timeOut: period (seconds) to wait before giving up
        @rtype: boolean
        """
        regex = re.compile(title)
        waited = 0

        while waited < timeOut:
            if regex.match(self.get_active_title()):
                return True 
            if timeOut == 0:
                break

            time.sleep(0.3)
            waited += 0.3
        return

    def wait_for_exist(self, title, timeOut=5, by_id=False):
        """
        Wait for window with the given title to be created

        Usage: C{window.wait_for_exist(title, timeOut=5)}

        If the window is in existence, returns True. Otherwise, returns False if
        the window has not been created by the time the timeout has elapsed.

        @param title: title to match against (as a regular expression)
        @param timeOut: period (seconds) to wait before giving up
        @param by_id: If true, C{wmctrl} will interpret the C{title} as a id
        @rtype: boolean
        """
        waited = 0
        while waited < timeOut:
            windowList = self.get_window_list()
            for window in windowList:
                if by_id:
                    if title == window["id"]:
                        return True
                else:
                    if title in window["wm_title"]:
                        return True
                if timeOut == 0:
                    break
            time.sleep(0.3)
            waited += 0.3
        
        return False

    def activate(self, title, switchDesktop=False, matchClass=False, by_id=False):
        """
        Activate the specified window, giving it input focus

        Usage: C{window.activate(title, switchDesktop=False, matchClass=False)}

        If switchDesktop is False (default), the window will be moved to the current desktop
        and activated. Otherwise, switch to the window's current desktop and activate it there.

        @param title: window title to match against (as case-insensitive substring match)
        @param switchDesktop: whether or not to switch to the window's current desktop
        @param matchClass: if True, match on the window class instead of the title
        @param by_id: If true, C{wmctrl} will interpret the C{title} as a id
        """
        #TODO: implement switchDesktop, matchClass
        if by_id:
            self.windowInterface._dbus_activate_window(title)
        else:
            id = self.get_window_id(title)
            self.windowInterface._dbus_activate_window(id)


    def close(self, title, by_id=False):
        """
        Close the specified window gracefully

        Usage: C{window.close(title, matchClass=False)}

        @param title: window title to match against (as case-insensitive substring match)
        @param by_id: If true it will interpret the C{title} as an id
        """
        if by_id:
            self.windowInterface._dbus_close_window(title)
        else:
            id = self.get_window_id(title)
            self.windowInterface._dbus_close_window(id)

    def resize(self, title, width=-1, height=-1, by_id=False):
        """
        Resize the specified window, note that this appears to not include the window border/title bar.

        Usage: C{window.resize(title, width=-1, height=-1)}


        @param title: window title to match against (as case-insensitive substring match)
        @param width: new width of the window
        @param height: new height of the window
        @param by_id: If true, it will interpret the C{title} as an id
        """
        if by_id:
            self.windowInterface._dbus_resize_window(title, width, height)
        else:
            id = self.get_window_id(title)
            self.windowInterface._dbus_resize_window(id, width, height)


    def move(self, title, x=-1, y=-1, by_id=False):
        """
        Move the specified window

        Usage: C{window.move(title, x=-1, y=-1)}

        @param title: window title to match against (as case-insensitive substring match)
        @param x: new x position of the window
        @param y: new y position of the window
        @param by_id: If true, it will interpret the C{title} as an id
        """
        if by_id:
            self.windowInterface._dbus_move_window(title, x, y)
        else:
            id = self.get_window_id(title)
            self.windowInterface._dbus_move_window(id, x, y)

    def move_to_desktop(self, title, deskNum, matchClass=False, by_id=False):
        """
        Move the specified window to the given desktop

        Usage: C{window.move_to_desktop(title, deskNum, matchClass=False)}

        @param title: window title to match against (as case-insensitive substring match)
        @param deskNum: desktop to move the window to (note: zero based)
        @param matchClass: if True, match on the window class instead of the title
        @param by_id: If true, C{wmctrl} will interpret the C{title} as a id
        """
        #TODO: is this possible to implement with the gnome extension?
        raise NotImplementedError

    def switch_desktop(self, deskNum):
        """
        Switch to the specified desktop

        Usage: C{window.switch_desktop(deskNum)}

        @param deskNum: desktop to switch to (note: zero based)
        """
        #TODO: is this possible to implement with the gnome extension?
        raise NotImplementedError

    def set_property(self, title, action, prop, matchClass=False, by_id=False):
        """
        Set a property on the given window using the specified action

        Usage: C{window.set_property(title, action, prop, matchClass=False)}

        Allowable actions: C{add, remove, toggle}
        Allowable properties: C{modal, sticky, maximized_vert, maximized_horz, shaded, skip_taskbar,
        skip_pager, hidden, fullscreen, above}

        @param title: window title to match against (as case-insensitive substring match)
        @param action: one of the actions listed above
        @param prop: one of the properties listed above
        @param matchClass: if True, match on the window class instead of the title
        @param by_id: If true, C{wmctrl} will interpret the C{title} as a id
        """
        #TODO: is this possible to implement with the gnome extension?
        raise NotImplementedError
    
    def get_active_info(self):
        """
        Get all info about the currently active window

        Usage: C{window.get_active_info()}

        @return: a dictionary containing all info about the currently active window
        @rtype: C{dict}
        """
        window_list = self.windowInterface._dbus_window_list()
        for window in window_list:
            if window['focus']:
                return window

    def get_active_geometry(self):
        """
        Get the geometry of the currently active window. Uses the C{:ACTIVE:} function of C{wmctrl}.

        Usage: C{window.get_active_geometry()}

        @return: a 4-tuple containing the x-origin, y-origin, width and height of the window (in pixels)
        @rtype: C{tuple(int, int, int, int)}
        """
        active_info = self.get_active_info()
        x = active_info['x']
        y = active_info['y']
        width = active_info['width']
        height = active_info['height']
        return [x, y, width, height]

    def get_active_title(self):
        """
        Get the visible title of the currently active window

        Usage: C{window.get_active_title()}

        @return: the visible title of the currently active window
        @rtype: C{str}
        """
        return self.get_active_info()['wm_title']

    def get_active_class(self):
        """
        Get the class of the currently active window

        Usage: C{window.get_active_class()}

        @return: the class of the currently active window
        @rtype: C{str}
        """
        return self.get_active_info()['wm_class']

    def center_window(self, title=":ACTIVE:", win_width=None, win_height=None, monitor=0, matchClass=False, by_id=False):
        """
        Centers the active (or window selected by title) window. Requires xrandr for getting monitor sizes and offsets.

        @param title: Title of the window to center (defaults to using the active window)
        @param win_width: Width of the centered window, defaults to screenx/3. Use -1 to center without size change.
        @param win_height: Height of the centered window, defaults to screeny/3. Use -1 to center without size change.
        @param monitor: Monitor number (0 is primary, listed via C{xrandr --listactivemonitors} etc.)
        @param matchClass: if True, match on the window class instead of the title
        @raises ValueError: If title or desktop is not found by wmctrl
        @param by_id: If true, C{wmctrl} will interpret the C{title} as a id
        """
        raise NotImplementedError

    def get_window_list(self, filter_desktop=-1):
        """
        Returns a list of windows matching an optional desktop filter, requires C{wmctrl}!

        Each list item consists of: C{[id, title, class]}

        Where the C{id} is the ID used for some other functions.

        C{title} is the title that you would usually see in your window manager of choice.

        C{class} is the class of the window, usually the name of the application, like C{firefox}.

        @param filter_desktop: String, (usually 0-n) to filter the windows by. Any window not on the given desktop will not be returned.
        @return: C{[[id1, title1, class1], [id2, title2, class2], ...etc]}
        Returns C{[]} if no windows are found.
        """
        window_list = []
        dbus_window_list = self.windowInterface._dbus_window_list()
        for window in dbus_window_list:
            window_list.append([window['id'],  window['wm_title'], window['wm_class']])
        
        return window_list

    def get_window_hex(self, title):
        """
        Returns the id of the first window to match title.

        @param title: Window title to match for returning id
        @return: Returns id of the window to be used for other functions See L{get_window_geom}, L{visgrep_by_window_id}

        Returns C{None} if no matches are found
        """
        raise NotImplementedError


    def get_window_id(self, title):
        """
        Returns the id of the first window to match title.

        @param title: Window title to match for returning id
        @return: Returns id of the window to be used for other functions.

        Returns C{None} if no matches are found
        """
        window_list = self.windowInterface._dbus_window_list()
        for window in window_list:
            if window['wm_title'] == title:
                return window['id']
        return None


    def get_window_geometry(self, title):
        """
        Returns where the location of the top left hand corner of the window is and the width/height of the window.

        @param title
        @return: C{[x, y, width, height]} Returns C{None} if no matches are found
        """
        window_list = self.windowInterface_dbus_window_list()
        for window in window_list:
            if window['wm_title'] == title:
                x = window['x']
                y = window['y']
                width = window['width']
                height = window['height']
                return [x, y, width, height]
        return None

