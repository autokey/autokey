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

import datetime
import time

from .iomediator import IoMediator
from autokey.model.key import Key, MODIFIERS
from . import iomediator


class KeyGrabber:
    """
    Keygrabber used by the hotkey settings dialog to grab the key pressed
    """

    def __init__(self, parent):
        self.target_parent = parent

    def start(self):
        # In QT version, sometimes the mouse click event arrives before we finish initialising
        # sleep slightly to prevent this
        time.sleep(0.1)
        IoMediator.listeners.append(self)
        iomediator.CURRENT_INTERFACE.grab_keyboard()

    def handle_keypress(self, raw_key, modifiers, key, *args):
        if raw_key not in MODIFIERS:
            IoMediator.listeners.remove(self)
            self.target_parent.set_key(raw_key, modifiers)
            iomediator.CURRENT_INTERFACE.ungrab_keyboard()

    def handle_mouseclick(self, root_x, root_y, rel_x, rel_y, button, window_info):
        IoMediator.listeners.remove(self)
        iomediator.CURRENT_INTERFACE.ungrab_keyboard()
        self.target_parent.cancel_grab()


class Recorder(KeyGrabber):
    """
    Recorder used by the record macro functionality
    """

    def __init__(self, parent):
        KeyGrabber.__init__(self, parent)
        self.insideKeys = False
        self.start_time = .0
        self.delay = .0
        self.delay_finished = False
        self.record_keyboard = self.record_mouse = False

    def start(self, delay: float):
        time.sleep(0.1)
        IoMediator.listeners.append(self)
        self.target_parent.start_record()
        self.start_time = time.time()
        self.delay = delay
        self.delay_finished = False

    def start_withgrab(self):
        time.sleep(0.1)
        IoMediator.listeners.append(self)
        self.target_parent.start_record()
        self.start_time = time.time()
        self.delay = 0
        self.delay_finished = True
        iomediator.CURRENT_INTERFACE.grab_keyboard()

    def stop(self):
        if self in IoMediator.listeners:
            IoMediator.listeners.remove(self)
            if self.insideKeys:
                self.target_parent.end_key_sequence()
            self.insideKeys = False

    def stop_withgrab(self):
        iomediator.CURRENT_INTERFACE.ungrab_keyboard()
        if self in IoMediator.listeners:
            IoMediator.listeners.remove(self)
            if self.insideKeys:
                self.target_parent.end_key_sequence()
            self.insideKeys = False

    def set_record_keyboard(self, record: bool):
        self.record_keyboard = record

    def set_record_mouse(self, record: bool):
        self.record_mouse = record

    def _delay_passed(self) -> bool:
        if not self.delay_finished:
            now = time.time()
            delta = datetime.datetime.utcfromtimestamp(now - self.start_time)
            self.delay_finished = (delta.second > self.delay)

        return self.delay_finished

    def handle_keypress(self, raw_key, modifiers, key, *args):
        if self.record_keyboard and self._delay_passed():
            if not self.insideKeys:
                self.insideKeys = True
                self.target_parent.start_key_sequence()

            modifier_count = len(modifiers)

            # TODO: This check assumes that Key.SHIFT is the only case shifting modifier. What about ISO_Level3_Shift
            # or ISO_Level5_Lock?
            if modifier_count > 1 or (modifier_count == 1 and Key.SHIFT not in modifiers) or \
                    (Key.SHIFT in modifiers and len(raw_key) > 1):
                self.target_parent.append_hotkey(raw_key, modifiers)

            elif key not in MODIFIERS:
                self.target_parent.append_key(key)

    def handle_mouseclick(self, root_x, root_y, rel_x, rel_y, button, window_info):
        if self.record_mouse and self._delay_passed():
            if self.insideKeys:
                self.insideKeys = False
                self.target_parent.end_key_sequence()

            self.target_parent.append_mouseclick(rel_x, rel_y, button, window_info[0])
