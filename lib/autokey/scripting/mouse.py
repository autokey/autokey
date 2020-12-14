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

    def move_cursor(self, x,y):
        """
        Move mouse cursor to xy location on screen without warping back to the start location

        Usage: C{mouse.move_cursor(x,y,tracking=False)}

        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        """
        self.interface.move_cursor(x,y)

    def press_button(self, button):
        """
        Send mouse button down signal at current  location

        Usage: C{mouse.press_button(button)}

        @param button: the mouse button to press down
        """
        x,y = self.interface.mouse_location()
        self.interface.mouse_press(x,y,button)

    def release_button(self, button):
        """
        Send mouse button up signal at current location

        Usage: C{mouse.release_button(button)}

        @param button: the mouse button to press down
        """
        x,y = self.interface.mouse_location()
        self.interface.mouse_release(x,y,button)

    def select_area(self, startx, starty, endx, endy, button):
        """
        "Drag and Select" for an area with the top left corner at (startx, starty)
        and the bottom right corner at (endx, endy) and uses C{button} for the mouse button held down

        Usage: C{mouse.select_area(startx, starty, endx, endy, button)}

        @param startx: X coordinate of where to start the drag and select
        @param starty: Y coordinate of where to start the drag and select
        @param endx: X coordinate of where to end the drag and select
        @param endy: Y coordinate of where to end the drag and select
        @param button: What mouse button to press at the start coordinates and release at the end coordinates

        """
        self.interface.move_cursor(startx, starty)
        self.interface.mouse_press(startx, starty, button)
        self.interface.move_cursor(endx,endy)
        self.interface.mouse_release(endx, endy, button)


    def get_location(self):
        """
        Returns the current location of the mouse.
        Be warned that this is instantaneous (where as other methods get loaded into an execution queue)
        and this may produce unexpected results:
        C{mouse.move_cursor(0,0)
        x,y = mouse.get_location()}

        Will generally NOT return (0,0). the C{mouse.get_location()} line is executed before the actual move put into the queue
        by C{move_cursor()} is able to be executed, meaning the actual action put into the queue by C{move_cursor} will not be 
        executed for a few milliseconds. The gap is long enough that C{get_location} will read the previous location instead of 0,0 
        as one might expect on first glance.

        Usage: C{mouse.get_location()}

        @return: x,y location of the mouse
        @rtype: C{tuple(int,int)}
        """

        return self.interface.mouse_location()