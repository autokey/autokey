# Copyright (C) 2021 BlueDrink9

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import pytest
from hamcrest import *
import unittest
from unittest.mock import Mock, MagicMock, patch

from tests.engine_helpers import *
import tests.helpers_for_tests as testhelpers

from autokey.model.key import Key
import autokey.interface

class EventCapturer():
    def __init__(self):
        self.received = []
        self.mods = []

    def get_result(self):
        # return "|".join(self.received)
        return self.received

    def get_mods(self):
        return self.mods


    def capture_event(self, keycode, modifiers, theWindow=None, press=True):
        self.received.append(keycode)
        self.mods.append(modifiers)

# I just printed these to the console running regular autokey on my machine.
# I don't know how likely they are to change. -- BlueDrink9, 6/9/21
mock_usable_offsets = (0, 1, 4, 5)
mock_modMask = {Key.SHIFT: 1, Key.CONTROL: 4, Key.ALT: 8, Key.ALT_GR: 128, Key.SUPER: 64, Key.HYPER: 64, Key.META: 8, Key.NUMLOCK: 16}

@patch("autokey.interface.XInterfaceBase._XInterfaceBase__checkWorkaroundNeeded", return_value=False)
class TestXrecord(unittest.TestCase):

    def setUp(self):
        self.ec = EventCapturer()
        self.ifc = autokey.interface.XRecordInterface(MagicMock(), MagicMock())
        self.ifc._XInterfaceBase__usableOffsets = mock_usable_offsets
        self.ifc.modMasks = mock_modMask
        self.event_capture_patch = \
            patch(
            "autokey.interface.XInterfaceBase._XInterfaceBase__send_key_press_release_event",
                self.ec.capture_event)
        self.check_workaround_patch = \
            patch(
                "autokey.interface.XInterfaceBase._XInterfaceBase__checkWorkaroundNeeded",
                return_value=False)

    def test_send_string(self, *args):
        test_string = "hello"
        # These are just the values recorded on my machine. I don't know enough
        # to be sure they will be correct on every machine.
        # So long as they work on the CI though, I'm happy this test protects
        # against any _major_ screw-ups.
        expected = [43, 43, 26, 26, 46, 46, 46, 46, 32, 32]
        expected_mods = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        with self.event_capture_patch, self.check_workaround_patch:
            self.ifc.send_string(test_string)
            try:
                autokey.interface.XInterfaceBase.cancel(self.ifc)
            except RuntimeError:
                # Complaints about joining self thread before it starts.
                pass
        assert_that(self.ec.get_result(), is_(equal_to(expected)))
        assert_that(self.ec.get_mods(), is_(equal_to(expected_mods)))
