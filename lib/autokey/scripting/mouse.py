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
"""Mouse functions, see also L{highlevel} for mouse move and click functions using C{xte} from C{xautomation}"""

import typing
import time

if typing.TYPE_CHECKING:
    import autokey.iomediator.iomediator


from autokey.model.button import Button

import autokey.iomediator.waiter


class Mouse:
    """
    Provides access to send mouse clicks
    """

    Button = Button

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
        w = autokey.iomediator.waiter.Waiter(None, None, button, None, None, timeOut)
        w.wait()

    def move_cursor(self, x,y):
        """
        Move mouse cursor to xy location on screen without warping back to the start location

        Usage: C{mouse.move_cursor(x,y)}

        @param x: x-coordinate in pixels, relative to upper left corner of screen
        @param y: y-coordinate in pixels, relative to upper left corner of screen
        """
        self.interface.move_cursor(x,y)

    def move_relative(self, x, y):
        """
        Move cursor relative to xy location based on the top left hand corner of the window that has input focus

        Usage: C{mouse.move_relative(x,y)}

        @param x: x-coordinate in pixels, relative to upper left corner of window
        @param y: y-coordinate in pixels, relative to upper left corner of window
        """
        self.interface.move_cursor(x,y,relative=True)


    def move_relative_self(self, x, y):
        """
        Move cursor relative to the location of the mouse cursor

        Usage: C{mouse.move_relative_self(x,y)}

        @param x: x-coordinate in pixels, relative to current position of mouse cursor
        @param y: y-coordinate in pixels, relative to current position of mouse cursor
        """
        self.interface.move_cursor(x, y, relative_self=True)

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

    def select_area(self, startx, starty, endx, endy, button, scrollNumber=0, down=True, warp=True):
        """
        "Drag and Select" for an area with the top left corner at (startx, starty)
        and the bottom right corner at (endx, endy) and uses C{button} for the mouse button held down

        Usage: C{mouse.select_area(startx, starty, endx, endy, button)}

        @param startx: X coordinate of where to start the drag and select
        @param starty: Y coordinate of where to start the drag and select
        @param endx: X coordinate of where to end the drag and select
        @param endy: Y coordinate of where to end the drag and select
        @param button: What mouse button to press at the start coordinates and release at the end coordinates
        @param scrollNumber: Number of times to scroll, defaults to 0
        @param down: Boolean to choose which direction to scroll, True for down, False for up., defaults to scrolling down.
        @param warp: If True method will return cursor to the position it was at at the start of execution
        """
        #store mouse location
        x,y = self.interface.mouse_location()
        self.interface.move_cursor(startx, starty)
        self.interface.mouse_press(startx, starty, button)
        if down:
            self.interface.scroll_down(scrollNumber)
        else:
            self.interface.scroll_up(scrollNumber)
        self.interface.move_cursor(endx,endy)
        self.interface.mouse_release(endx, endy, button)
        #restore mouse location
        if warp:
            self.interface.move_cursor(x,y)


    def get_location(self):
        """
        Returns the current location of the mouse.
        Incorporates a tiny delay in order to make sure AutoKey executes any queued commands before checking the location.
        C{mouse.move_cursor(0,0)
        x,y = mouse.get_location()}

        Usage: C{mouse.get_location()}

        @return: x,y location of the mouse
        @rtype: C{tuple(int,int)}
        """
        #minimal delay added to make sure location is correct
        time.sleep(0.05)
        return self.interface.mouse_location()

    def get_relative_location(self):
        """
        Returns the relative location of the mouse in the window that has input focus
        Incorporates a tiny delay in order to make sure AutoKey executes any queued commands

        Usage: C{mouse.get_relative_location()}
        
        @return: x,y location of the mouse relative to the top left hand corner of the window that has input focus
        @rtype: C{tuple(int, int)}
        """
        time.sleep(0.05)
        return self.interface.relative_mouse_location()

    def scroll_down(self, number):
        """
        Fires the mouse button 5 signal the specified number of times.

        Note that the behavior of these methods are effected (and untested) by programs like imwheel.
        
        Usage: C{mouse.scroll_down()}
    
        @param number: The number of times the scroll up signal will be fired.
        """
        self.interface.scroll_down(number)

    def scroll_up(self, number):
        """
        Fires the mouse button 4 signal the specified number of times.

        Note that the behavior of these methods are effected (and untested) by programs like imwheel.

        Usage: C{mouse.scroll_up()}

        @param number: The number of times the scroll up signal will be fired.
        """
        self.interface.scroll_up(number)