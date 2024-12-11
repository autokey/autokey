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

import threading

# from .iomediator import IoMediator
from typing import Callable, Any


class Waiter:
    """
    Waits for a specified event to occur
    """

    def __init__(self, raw_key, modifiers, button, check: Callable[[Any,str,list,str], bool], name: str, time_out):
        # IoMediator.listeners.append(self)
        self.raw_key = raw_key
        self.modifiers = modifiers
        self.button = button
        self.event = threading.Event()
        self.check = check
        self.name = name
        self.time_out = time_out
        self.result = ''

        if modifiers is not None:
            self.modifiers.sort()

    def wait(self):
        return self.event.wait(self.time_out)

    def handle_keypress(self, raw_key, modifiers, key, *args):
        if (raw_key == self.raw_key and modifiers == self.modifiers) or (self.check is not None and self.check(self, raw_key, modifiers, key, *args)):
            # IoMediator.listeners.remove(self)
            self.event.set()

    def handle_mouseclick(self, root_x, root_y, rel_x, rel_y, button, window_info):
        if button == self.button:
            self.event.set()
