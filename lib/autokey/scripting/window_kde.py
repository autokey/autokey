#  Copyright (C) 2023 Sam Sebastian
#  Copyright (C) 2026 David King
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#####################################################################

"""
Desktop window management based on KDE KWin scripts
"""

import re
import subprocess
import time
from .abstract_window import AbstractWindow
import socket
import os
import json

logger = __import__("autokey.logger").logger.get_logger(__name__)

class Window(AbstractWindow):
    """
    Window management with AutoKey KDE KWin window interface
    """

    def __init__(self, mediator):
        self.mediator = mediator

    def wait_for_focus(self, title, timeOut=5):
        """
        Wait for window with the given title to have focus

        Usage: C{window.wait_for_focus(title, timeOut=5)}

        If the window becomes active, returns True. Otherwise, returns False if
        the window has not become active by the time the timeout has elapsed.

        :param title: title to match against (as a regular expression)
        :param timeOut: period (seconds) to wait before giving up
        :rtype: boolean
        """
        start = time.time()
        while time.time() - start <= timeOut:
            for item in self.mediator.windowInterface.get_window_list():
                if item['focus'] and re.search(rf'{title}', item['wm_title'], re.IGNORECASE):
                    return True
            time.sleep(0.3)
        return False

    def wait_for_exist(self, title, timeOut=5, by_hex=False):
        """
        Wait for window with the given title to be created

        Usage: C{window.wait_for_exist(title, timeOut=5)}

        If the window is in existence, returns True. Otherwise, returns False if the window has not been created by the time the timeout has elapsed.

        :param title: title to match against (as a regular expression)
        :param timeOut: period (seconds) to wait before giving up
        :param by_hex: If true, will interpret the C{title} as a hexid
        :rtype: boolean
        """
        start = time.time()
        while time.time() - start <= timeOut:
            for item in self.mediator.windowInterface.get_window_list():
                if (by_hex and by_hex == item['id']) or re.search(rf'{title}', item['wm_title'], re.IGNORECASE):
                    return True
            time.sleep(0.3)
        return False

    def activate(self, title, switchDesktop=False, matchClass=False, by_hex=False):
        """
        Activate the specified window, giving it input focus

        Usage: C{window.activate(title, switchDesktop=False, matchClass=False)}

        If switchDesktop is False (default), the window will be moved to the current desktop and activated. Otherwise, switch to the window's current desktop and activate it there.

        :param title: window title to match against (as case-insensitive substring match)
        :param switchDesktop: If True, switch to desktop where window resides and activate
        :param matchClass: if True, match on the window class instead of the title
        :param by_hex: If true, interpret the C{title} as a hexid
        """
        target_window = self.__get_target_window(title, matchClass, by_hex)
        if target_window:
            #logger.debug(f'window API: target window details:\n{json.dumps(target_window, indent=4)}')
            if switchDesktop:
                self.mediator.windowInterface.switch_workspace(target_window['workspace'])
            else:
                wksid = self.mediator.windowInterface.get_active_desktop_index()
                self.mediator.windowInterface.move_to_workspace(target_window['id'], wksid)
            self.mediator.windowInterface.activate_window(target_window['id'])
        return

    def close(self, title, matchClass=False, by_hex=False):
        """
        Close the specified window gracefully

        Usage: C{window.close(title, matchClass=False), by_hex=False}

        :param title: window title to match against (as case-insensitive substring match)
        :param matchClass: if True, match on the window class instead of the title
        :param by_hex: If true, interpret the C{title} as a hexid
        """
        target_window = self.__get_target_window(title, matchClass, by_hex)
        if target_window:
            #logger.debug(f'window API: target window details:\n{json.dumps(target_window, indent=4)}')
            self.mediator.windowInterface.close_window(target_window['id'])

    def resize_move(self, title, xOrigin=-1, yOrigin=-1, width=-1, height=-1, matchClass=False, by_hex=False):
        """
        Resize and/or move the specified window

        Usage: C{window.resize_move(title, xOrigin=-1, yOrigin=-1, width=-1, height=-1, matchClass=False)}

        Leaving any of the position/dimension values as the default (-1) will cause that
        value to be left unmodified.

        :param title: window title to match against (as case-insensitive substring match)
        :param xOrigin: new x origin of the window (upper left corner)
        :param yOrigin: new y origin of the window (upper left corner)
        :param width: new width of the window
        :param height: new height of the window
        :param matchClass: if C{True}, match on the window class instead of the title
        :param by_hex: If true, interpret the C{title} as a hexid
        """
        target_window = self.__get_target_window(title, matchClass, by_hex)
        if target_window:
            #logger.debug(f'window API: target window details:\n{json.dumps(target_window, indent=4)}')
            hexid = target_window['id']
            if xOrigin == -1:
                xOrigin = target_window['x']
            if yOrigin == -1:
                yOrigin = target_window['y']
            if width == -1:
                width = target_window['width']
            if height == -1:
                height = target_window['height']
            self.mediator.windowInterface.move_resize_window(hexid, xOrigin, yOrigin, width, height)
        return

    def move_to_desktop(self, title, deskNum, matchClass=False, by_hex=False):
        """
        Move window to specified desktop (GNOME workspace)

        Usage: C{window.move_to_desktop(title, desknum, matchClass=False, by_hex=False)}

        :param title: window title to match against (as case-insensitive substring match)
        :param desknum: the number of the desktop (workspace) to which to move this window (note: zero based)
        :param matchClass: if C{True}, match on the window class instead of the title
        :param by_hex: If true, interpret the C{title} as a hexid
        """
        target_window = self.__get_target_window(title, matchClass, by_hex)
        if target_window:
            #logger.debug(f'window API: target window details:\n{json.dumps(target_window, indent=4)}')
            self.mediator.windowInterface.move_to_workspace(target_window['id'], deskNum)

    def switch_desktop(self, deskNum):
        """
        Switch to the specified desktop (GNOME workspace)

        Usage: C{window.switch_desktop(deskNum)}

        :param deskNum: desktop to switch to (note: zero based)
        """
        self.mediator.windowInterface.switch_workspace(deskNum)

    def set_property(self, title, action, prop, matchClass=False, by_hex=False):
        """
        Set a property on the given window using the specified action

        Usage: C{window.set_property(title, action, prop, matchClass=False, by_hex=False)}

        Allowable actions:

        - add
        - remove
        - toggle

        Properties available in KDE environment:

        - above
        - fullscreen
        - maximized_vert
        - maximized_horz
        - shaded
        - skip_pager
        - skip_taskbar

        :param title: window title to match against (as case-insensitive substring match)
        :param action: one of the actions listed above
        :param prop: one of the properties listed above
        :param matchClass: if True, match on the window class instead of the title
        :param by_hex: If true, will interpret the C{title} as a hexid
        """
        target_window = self.__get_target_window(title, matchClass, by_hex)
        if target_window:
            #logger.debug(f'window API: target window details:\n{json.dumps(target_window, indent=4)}')
            properties = self.mediator.windowInterface.get_properties(target_window['id'])
            if prop == 'above':
                if action == 'toggle':
                    if properties['is_above']:
                        self.mediator.windowInterface.unmake_above_window(target_window['id'])
                    else:
                        self.mediator.windowInterface.make_above_window(target_window['id'])
                elif action == 'add':
                    self.mediator.windowInterface.make_above_window(target_window['id'])
                elif action == 'remove':
                    self.mediator.windowInterface.unmake_above_window(target_window['id'])
                else:
                    logger.error(f'Unknown action "{action}" in window.set_property()')
            elif prop == 'fullscreen':
                if action == 'toggle':
                    if properties['is_fullscreen']:
                        self.mediator.windowInterface.unmake_fullscreen_window(target_window['id'])
                    else:
                        self.mediator.windowInterface.make_fullscreen_window(target_window['id'])
                elif action == 'add':
                    self.mediator.windowInterface.make_fullscreen_window(target_window['id'])
                elif action == 'remove':
                    self.mediator.windowInterface.unmake_fullscreen_window(target_window['id'])
                else:
                    logger.error(f'Unknown action "{action}" in window.set_property()')
            elif prop == 'maximized_vert':
                if action == 'toggle':
                    if properties['is_maximized_vert']:
                        self.mediator.windowInterface.unmaximize_window(target_window['id'], 2)
                    else:
                        self.mediator.windowInterface.maximize_window(target_window['id'], 2)
                elif action == 'add':
                    self.mediator.windowInterface.maximize_window(target_window['id'], 2)
                elif action == 'remove':
                    self.mediator.windowInterface.unmaximize_window(target_window['id'], 2)
                else:
                    logger.error(f'Unknown action "{action}" in window.set_property()')
            elif prop == 'maximized_horz':
                if action == 'toggle':
                    if properties['is_maximized_vert']:
                        self.mediator.windowInterface.unmaximize_window(target_window['id'], 1)
                    else:
                        self.mediator.windowInterface.maximize_window(target_window['id'], 1)
                elif action == 'add':
                    self.mediator.windowInterface.maximize_window(target_window['id'], 1)
                elif action == 'remove':
                    self.mediator.windowInterface.unmaximize_window(target_window['id'], 1)
                else:
                    logger.error(f'Unknown action "{action}" in window.set_property()')
            elif prop == 'shaded':
                if action == 'toggle':
                    self.mediator.windowInterface.set_property(target_window['id'], 'shade', not properties['is_shaded'])
                elif action == 'add':
                    self.mediator.windowInterface.set_property(target_window['id'], 'shade', True)
                elif action == 'remove':
                    self.mediator.windowInterface.set_property(target_window['id'], 'shade', False)
                else:
                    logger.error(f'Unknown action "{action}" in window.set_property()')
            elif prop == 'skip_pager':
                if action == 'toggle':
                    self.mediator.windowInterface.set_property(target_window['id'], 'skipPager', not properties['is_skip_pager'])
                elif action == 'add':
                    self.mediator.windowInterface.set_property(target_window['id'], 'skipPager', True)
                elif action == 'remove':
                    self.mediator.windowInterface.set_property(target_window['id'], 'skipPager', False)
                else:
                    logger.error(f'Unknown action "{action}" in window.set_property()')
            elif prop == 'skip_taskbar':
                if action == 'toggle':
                    self.mediator.windowInterface.set_property(target_window['id'], 'skipTaskbar', not properties['is_skip_taskbar'])
                elif action == 'add':
                    self.mediator.windowInterface.set_property(target_window['id'], 'skipTaskbar', True)
                elif action == 'remove':
                    self.mediator.windowInterface.set_property(target_window['id'], 'skipTaskbar', False)
                else:
                    logger.error(f'Unknown action "{action}" in window.set_property()')
            else:
                logger.error(f'Unknown or unimplemented property "{prop}" in window.set_property()')
        return

    def get_active_geometry(self):
        """
        Get the geometry of the currently active window.

        Usage: C{window.get_active_geometry()}

        :return: a 4-tuple containing the x-origin, y-origin, width and height of the window (in pixels)
        :rtype: C{tuple(int, int, int, int)}
        """
        #wrapper for get_window_geometry()
        return self.get_window_geometry(":ACTIVE:")


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

    def center_window(self, title=":ACTIVE:", win_width=None, win_height=None, matchClass=False, by_hex=False):
        """
        Centers the active (or window selected by title) window.

        :param title: Title of the window to center (defaults to using the active window)
        :param win_width: Width of the centered window, defaults to screenx/3. Use -1 to center without size change.
        :param win_height: Height of the centered window, defaults to screeny/3. Use -1 to center without size change.
        :param matchClass: if True, match on the window class instead of the title
        :param by_hex: If true, interpret the C{title} as a hexid
        """
        try:
            (screen_width, screen_height) = self.mediator.windowInterface.get_screen_size()
        except Exception as e:
            logger.exception('KDE KWin never responded with the screen size.')
            return
        target_window = self.__get_target_window(title, matchClass, by_hex)
        if target_window:
            #logger.debug(f'window API: target window details:\n{json.dumps(target_window, indent=4)}')
            if win_width == -1:
                win_width = target_window['width']
            elif not win_width:
                win_width = screen_width // 3
            if win_height == -1:
                win_height = target_window['height']
            elif not win_height:
                win_height = screen_height // 3
            x = (screen_width - win_width) // 2
            y = (screen_height - win_height) // 2
            self.resize_move(title, x, y, win_width, win_height, matchClass=matchClass, by_hex=by_hex)
        return

    def get_window_list(self, filter_desktop=-1):
        """
        Returns a list of windows matching an optional desktop filter, requires AutoKey GNOME Shell extension!

        Each list item consists of: C{[hexid, desktop, hostname, title]}

        Where the C{hexid} is the window ID.

        C{desktop} is the number of which desktop (sometimes called workspaces) the window appears upon.

        C{hostname} is the hostname of your computer.

        C{title} is the title that you would usually see in your window manager of choice.

        :param filter_desktop (note: zero based)
        :return: C{[[hexid1, desktop1, hostname1, title1], [hexid2,desktop2,hostname2,title2], ...etc]} Returns C{[]} if no windows are found.
        """
        output_list = []
        for item in self.mediator.windowInterface.get_window_list():
            window = (
                item['id'],
                item['workspace'],
                socket.gethostname(),
                item['wm_title']
            )
            if filter_desktop != -1:
                if item['workspace'] == filter_desktop:
                    output_list.append(window)
            else:
                output_list.append(window)
        return output_list

    def get_window_hex(self, title):
        """
        Returns the hexid of the first window to match title.

        :param title: Window title to match for returning hexid.  Use ":ACTIVE:" to specify the window that currently has focus on the desktop.
        :return: Returns hexid of the window to be used for other functions See L{get_window_geom}, L{visgrep_by_window_id}

        Returns C{None} if no matches are found
        """
        target_window = self.__get_target_window(title, False, False)
        if target_window:
            #logger.debug(f'window API: target window details:\n{json.dumps(target_window, indent=4)}')
            return target_window['id']
        return None

    def get_window_geometry(self, title, matchClass=False, by_hex=False):
        """
        Returns the window geometry of the given window title. Returns where the location of the
        top left hand corner of the window is and the width/height of the window.

        :param title: Window title to match for returning geometry.  Use ":ACTIVE:" to specify the window that currently has focus on the desktop.
        :param matchClass: if True, match on the window class instead of the title
        :param by_hex: If true, interpret the C{title} as a hexid
        :return: C{[offsetx, offsety, sizex, sizey]} Returns none if no matches are found

        Returns C{None} if no matching window was found
        """
        target_window = self.__get_target_window(title, matchClass, by_hex)
        if target_window:
            #logger.debug(f'window API: target window details:\n{json.dumps(target_window, indent=4)}')
            return (target_window['x'], target_window['y'], target_window['width'], target_window['height'])
        return None

    def __get_target_window(self, title, matchClass, by_hex):
        """
        A utility function that searches for a window on the desktop that matches
        s specific set of criteria.  This function is used by several of the
        functions in this class.

        :param title: window title to match against (as case-insensitive substring match)
        :param matchClass: if C{True}, match on the window class instead of the title
        :param by_hex: If true, interpret the C{title} as a hexid
        :return: A dictionary containing the data the AutoKey GNOME Shell extension found for the matching window

        Returns C{None} if no matching window was found
        """
        if by_hex and matchClass:
            logger.warning('window API: both by_hex and matchClass are set True, ignoring matchClass and continuing')

        for win in self.mediator.windowInterface.get_window_list():
            if by_hex:
                if win['id'] == title:
                    return win
            else:
                if matchClass:
                     if re.search(rf'{title}', win['wm_class'], re.IGNORECASE):
                        return win
                else:
                    if title == ':ACTIVE:' and win['focus']:
                        return win
                    elif re.search(rf'{title}', win['wm_title'], re.IGNORECASE):
                        return win
        return None
