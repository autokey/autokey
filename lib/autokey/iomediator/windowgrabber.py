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

import time
import threading

from .iomediator import IoMediator

SEND_LOCK = threading.Lock()  # TODO: This is never accessed anywhere. Does creating this lock do anything?

# Import Wayland-specific modules
try:
    from pywayland.client import Display
    from pywayland.protocol.wayland import WlSeat
    from libinput import LibInput
    WAYLAND_AVAILABLE = True
except ImportError:
    WAYLAND_AVAILABLE = False


class WindowGrabber:

    def __init__(self, dialog):
        self.dialog = dialog
        self.wayland_display = None
        self.libinput_context = None

        if WAYLAND_AVAILABLE:
            self.wayland_display = Display()
            self.libinput_context = LibInput()

    def start(self):
        time.sleep(0.1)
        IoMediator.listeners.append(self)

    def handle_keypress(self, raw_key, modifiers, key, *args):
        pass

    def handle_mouseclick(self, root_x, root_y, rel_x, rel_y, button, window_info):
        IoMediator.listeners.remove(self)
        self.dialog.receive_window_info(window_info)

    def handle_wayland_events(self):
        if not WAYLAND_AVAILABLE:
            return

        while True:
            self.libinput_context.dispatch()
            for event in self.libinput_context.events:
                if event.type == 'pointer_button':
                    self.handle_mouseclick(event.root_x, event.root_y, event.rel_x, event.rel_y, event.button, None)
                elif event.type == 'keyboard_key':
                    self.handle_keypress(event.raw_key, event.modifiers, event.key)
