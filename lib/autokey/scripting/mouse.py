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
    import autokey.iomediator


class Mouse:
    """
    Provides access to send mouse clicks
    """
    def __init__(self, mediator):
        self.mediator = mediator  # type: autokey.iomediator.IoMediator
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
        w = autokey.iomediator.Waiter(None, None, button, timeOut)
        w.wait()
