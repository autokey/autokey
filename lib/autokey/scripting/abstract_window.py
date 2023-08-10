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

from abc import ABC, ABCMeta, abstractmethod




class AbstractWindow(ABC):
    __metaclass__ = ABCMeta
    """
    Basic window management
    """

    @abstractmethod
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
        return

    @abstractmethod
    def wait_for_exist(self, title, timeOut=5, by_hex=False):
        """
        Wait for window with the given title to be created

        Usage: C{window.wait_for_exist(title, timeOut=5)}

        If the window is in existence, returns True. Otherwise, returns False if
        the window has not been created by the time the timeout has elapsed.

        @param title: title to match against (as a regular expression)
        @param timeOut: period (seconds) to wait before giving up
        @param by_hex: If true, C{wmctrl} will interpret the C{title} as a hexid
        @rtype: boolean
        """
        return

    @abstractmethod
    def activate(self, title, switchDesktop=False, matchClass=False, by_hex=False):
        """
        Activate the specified window, giving it input focus

        Usage: C{window.activate(title, switchDesktop=False, matchClass=False)}

        If switchDesktop is False (default), the window will be moved to the current desktop
        and activated. Otherwise, switch to the window's current desktop and activate it there.

        @param title: window title to match against (as case-insensitive substring match)
        @param switchDesktop: whether or not to switch to the window's current desktop
        @param matchClass: if True, match on the window class instead of the title
        @param by_hex: If true, C{wmctrl} will interpret the C{title} as a hexid
        """
        return

    @abstractmethod
    def close(self, title, matchClass=False, by_hex=False):
        """
        Close the specified window gracefully

        Usage: C{window.close(title, matchClass=False)}

        @param title: window title to match against (as case-insensitive substring match)
        @param matchClass: if True, match on the window class instead of the title
        @param by_hex: If true, C{wmctrl} will interpret the C{title} as a hexid
        """
        return

    @abstractmethod
    def resize(self, title, width=-1, height=-1, matchClass=False, by_hex=False):
        """
        Resize the specified window

        Usage: C{window.resize(title, xOrigin=-1, yOrigin=-1, width=-1, height=-1, matchClass=False)}

        Leaving and of the position/dimension values as the default (-1) will cause that
        value to be left unmodified.

        @param title: window title to match against (as case-insensitive substring match)
        @param xOrigin: new x origin of the window (upper left corner)
        @param yOrigin: new y origin of the window (upper left corner)
        @param width: new width of the window
        @param height: new height of the window
        @param matchClass: if C{True}, match on the window class instead of the title
        @param by_hex: If true, C{wmctrl} will interpret the C{title} as a hexid
        """
        return
    
    @abstractmethod
    def move(self, title, x, y, by_id=False):
        """
        Move the specified window

        Usage: C{window.move(title, x, y, by_id=False)}

        @param title: window title to match against.
        @param x: new x origin of the window (upper left corner)
        @param y: new y origin of the window (upper left corner)
        @param by_id: If true, C{wmctrl} will interpret the C{title} as a hexid

        """
        return

    @abstractmethod
    def move_to_desktop(self, title, deskNum, matchClass=False, by_hex=False):
        """
        Move the specified window to the given desktop

        Usage: C{window.move_to_desktop(title, deskNum, matchClass=False)}

        @param title: window title to match against (as case-insensitive substring match)
        @param deskNum: desktop to move the window to (note: zero based)
        @param matchClass: if True, match on the window class instead of the title
        @param by_hex: If true, C{wmctrl} will interpret the C{title} as a hexid
        """
        return

    @abstractmethod
    def switch_desktop(self, deskNum):
        """
        Switch to the specified desktop

        Usage: C{window.switch_desktop(deskNum)}

        @param deskNum: desktop to switch to (note: zero based)
        """
        return

    @abstractmethod
    def set_property(self, title, action, prop, matchClass=False, by_hex=False):
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
        @param by_hex: If true, C{wmctrl} will interpret the C{title} as a hexid
        """
        return

    @abstractmethod
    def get_active_geometry(self):
        """
        Get the geometry of the currently active window. Uses the C{:ACTIVE:} function of C{wmctrl}.

        Usage: C{window.get_active_geometry()}

        @return: a 4-tuple containing the x-origin, y-origin, width and height of the window (in pixels)
        @rtype: C{tuple(int, int, int, int)}
        """
        return

    @abstractmethod
    def get_active_title(self):
        """
        Get the visible title of the currently active window

        Usage: C{window.get_active_title()}

        @return: the visible title of the currently active window
        @rtype: C{str}
        """
        return

    @abstractmethod
    def get_active_class(self):
        """
        Get the class of the currently active window

        Usage: C{window.get_active_class()}

        @return: the class of the currentle active window
        @rtype: C{str}
        """
        return
    
    @abstractmethod
    def get_active_info(self):
        """
        Get all info about the currently active window

        Usage: C{window.get_active_info()}

        @return: a dictionary containing all info about the currently active window
        @rtype: C{dict}
        """
        return
    

    @abstractmethod
    def center_window(self, title=":ACTIVE:", win_width=None, win_height=None, monitor=0, matchClass=False, by_hex=False):
        """
        Centers the active (or window selected by title) window. Requires xrandr for getting monitor sizes and offsets.

        @param title: Title of the window to center (defaults to using the active window)
        @param win_width: Width of the centered window, defaults to screenx/3. Use -1 to center without size change.
        @param win_height: Height of the centered window, defaults to screeny/3. Use -1 to center without size change.
        @param monitor: Monitor number (0 is primary, listed via C{xrandr --listactivemonitors} etc.)
        @param matchClass: if True, match on the window class instead of the title
        @raises ValueError: If title or desktop is not found by wmctrl
        @param by_hex: If true, C{wmctrl} will interpret the C{title} as a hexid
        """
        return

    @abstractmethod
    def get_window_list(self, filter_desktop=-1):
        """
        Returns a list of windows matching an optional desktop filter, requires C{wmctrl}!

        Each list item consists of: C{[hexid, desktop, hostname, title]}

        Where the C{hexid} is the ID used for some other functions (like L{import -window} from ImageMagick).

        C{desktop} is the number of which desktop (sometimes called workspaces) the window appears upon.

        C{hostname} is the hostname of your computer.

        C{title} is the title that you would usually see in your window manager of choice.

        @param filter_desktop: String, (usually 0-n) to filter the windows by. Any window not on the given desktop will not be returned.
        @return: C{[[hexid1, desktop1, hostname1, title1], [hexid2,desktop2,hostname2,title2], ...etc]}
        Returns C{[]} if no windows are found.
        """
        return

    @abstractmethod
    def get_window_hex(self, title):
        """
        Returns the hexid of the first window to match title.

        @param title: Window title to match for returning hexid
        @return: Returns hexid of the window to be used for other functions See L{get_window_geom}, L{visgrep_by_window_id}

        Returns C{None} if no matches are found
        """
        return



    @abstractmethod
    def get_window_geometry(self, title, by_hex=False):
        """
        Uses C{wmctrl} to return the window geometry of the given window title. Returns where the location of the
        top left hand corner of the window is and the width/height of the window.


        @param title
        @return: C{[offsetx, offsety, sizex, sizey]} Returns none if no matches are found
        """
        return
