# -*- coding: utf-8 -*-

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

from .iomediator_constants import X_RECORD_INTERFACE
ATSPI_INTERFACE = "AT-SPI"

INTERFACES = [X_RECORD_INTERFACE, ATSPI_INTERFACE]
# CURRENT_INTERFACE = None

import time
import threading

# MODIFIERS = [Key.CONTROL, Key.ALT, Key.ALT_GR, Key.SHIFT, Key.SUPER, Key.HYPER, Key.META, Key.CAPSLOCK, Key.NUMLOCK]
# HELD_MODIFIERS = [Key.CONTROL, Key.ALT, Key.SUPER, Key.SHIFT, Key.HYPER, Key.META]

SEND_LOCK = threading.Lock()

from .iomediator00 import IoMediator


class WindowGrabber:

    def __init__(self, dialog):
        self.dialog = dialog

    def start(self):
        time.sleep(0.1)
        IoMediator.listeners.append(self)

    def handle_keypress(self, rawKey, modifiers, key, *args):
        pass

    def handle_mouseclick(self, rootX, rootY, relX, relY, button, windowInfo):
        IoMediator.listeners.remove(self)
        self.dialog.receive_window_info(windowInfo)
