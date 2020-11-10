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

import typing

if typing.TYPE_CHECKING:
    import autokey.iomediator.iomediator


class Mouse:
    """
    Provides access to send mouse clicks
    """
    def __init__(self, mediator):
        self.mediator = mediator  # type: autokey.iomediator.iomediator.IoMediator
        self.interface = self.mediator.interface

    def click_relative(self, x, y, button):
        """
        Send a mouse click relative to the active window

        Usage: C{mouse.click_relative(x, y, button)}

        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        @param button: mouse button to simulate (left=1, middle=2, right=3)
        """
        self.interface.send_mouse_click(x, y, button, True)

    def click_relative_self(self, x, y, button):
        """
        Send a mouse click relative to the current mouse position

        Usage: C{mouse.click_relative_self(x, y, button)}

        @param x: x-offset in pixels, relative to current mouse position
        @param y: y-offset in pixels, relative to current mouse position
        @param button: mouse button to simulate (left=1, middle=2, right=3)
        """
        self.interface.send_mouse_click_relative(x, y, button)

    def click_absolute(self, x, y, button):
        """
        Send a mouse click relative to the screen (absolute)

        Usage: C{mouse.click_absolute(x, y, button)}

        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        @param button: mouse button to simulate (left=1, middle=2, right=3)
        """
        self.interface.send_mouse_click(x, y, button, False)

    def wait_for_click(self, button, timeOut=10.0):
        """
        Wait for a mouse click

        Usage: C{mouse.wait_for_click(self, button, timeOut=10.0)}

        @param button: they mouse button click to wait for as a button number, 1-9
        @param timeOut: maximum time, in seconds, to wait for the keypress to occur
        """
        button = int(button)
        w = autokey.iomediator.waiter.Waiter(None, None, button, timeOut)
        w.wait()

    def move_cursor(self, x,y, tracking=False):
        """
        Move mouse cursor to xy location on screen

        Usage: C{mouse.move_cursor(x,y,tracking=False)}

        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        @param tracking: Boolean to determine if the cursor warps or gradually moves across the screen
        """
        self.interface.move_cursor(x,y,tracking)

    def mouse_down(self, x, y, button):
        """
        Send mouse button down signal at given location

        Usage: C{mouse.mouse_button_down(x,y,button)}

        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        @param button: the mouse button to press down
        """
        self.interface.mouse_down(x,y,button)

    def mouse_up(self, x, y, button):
        """
        Send mouse button up signal at given location (does the location matter? I don't know)

        Usage: C{mouse.mouse_button_down(x,y,button)}

        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        @param button: the mouse button to press down
        """
        self.interface.mouse_up(x,y,button)

    def get_location(self):
        """
        Returns the current location of the mouse

        Usage: C{mouse.get_location()}

        @return: x,y location of the mouse
        @rtype: C{tuple(int,int)}
        """

        return self.interface.mouse_location()

    def drag_and_select(self, startx, starty, endx, endy, button):
        """
        Moves mouse to (startx, starty) presses down button
        Drag the mouse across from startx,starty to endx,endy
        Once mouse reaches final location sends button up signal

        Usage: C{mouse.drag_and_select(self, startx, starty, endx, endy, button)}

        @param startx: x-coordinate in pixels, relative to upper left corner of window
        @param starty: y-coordinate in pixels, relative to upper left corner of window
        @param endx: x-coordinate in pixels, relative to upper left corner of window
        @param endy: y-coordinate in pixels, relative to upper left corner of window
        @param button: the mouse button to press down
        """
        self.interface.drag_select(startx, starty, endx, endy, button)
