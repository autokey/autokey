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
import Xlib

import pytest
from hamcrest import *
import unittest
from unittest.mock import Mock, MagicMock, patch

from autokey.model.key import Key
import autokey.interface

class EventCapturer():
    def __init__(self):
        self.received = []

    def get_result(self):
        # return "|".join(self.received)
        return self.received

    def capture_event(self, keycode, modifiers, theWindow=None, press=True):
        if press:
            pressed = "p"
        else:
            pressed = "r"
        self.received.append((keycode, modifiers, pressed))

# I just printed these to the console running regular autokey on my machine.
# I don't know how likely they are to change. -- BlueDrink9, 6/9/21
mock_usable_offsets = (0, 1, 4, 5)
mock_modMask = {Key.SHIFT: 1, Key.CONTROL: 4, Key.ALT: 8, Key.ALT_GR: 128, Key.SUPER: 64, Key.HYPER: 64, Key.META: 8, Key.NUMLOCK: 16}

class TestXrecord():

    def setup_method(self):
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

    def teardown_method(self):
        self.cancel()

    def cancel(self):
        try:
            autokey.interface.XInterfaceBase.cancel(self.ifc)
        except RuntimeError:
            # Complaints about joining self thread before it starts.
            pass
        except Xlib.error.ConnectionClosedError:
            # Complaints about closing after closing already.
            pass

    # These are just the values recorded on my machine. I don't know enough
    # to be sure they will be correct on every machine.
    # So long as they work on the CI though, I'm happy this test protects
    # against any _major_ screw-ups.
    @pytest.mark.parametrize(
    "inpt, expected, failmsg", [
        ["hi.",
         [(43, 0, 'p'), (43, 0, 'r'), (31, 0, 'p'), (31, 0, 'r'), (60, 0, 'p'), (60, 0, 'r')],
         "Xinterface doesn't send a normal string properly",
         ],
        ["",
         [],
         "Xinterface doesn't send an empty string properly",
         ],
        [" ",
         [(65, 0, 'p'), (65, 0, 'r')],
         "Xinterface doesn't send a space-only string properly",
         ],
    ])
    def test_send_string(self, inpt, expected, failmsg):
        with self.event_capture_patch, self.check_workaround_patch:
            self.ifc.send_string(inpt)
            # Need to cancel early. But cancel in tearDown as well in case this test fails.
            self.cancel()
        assert_that(self.ec.get_result(), is_(equal_to(expected)), failmsg)


    @pytest.mark.parametrize(
    "inpt, expected, failmsg", [
        ["a",
         [(38, 0, 'p'), (38, 0, 'r')],
         "Xinterface doesn't send a normal key properly",],
    ])
    def test_send_key(self, inpt, expected, failmsg):
        with self.event_capture_patch, self.check_workaround_patch:
            self.ifc.send_key(inpt)
            # Need to cancel early. But cancel in tearDown as well in case this test fails.
            self.cancel()
        assert_that(self.ec.get_result(), is_(equal_to(expected)), failmsg)

    @pytest.mark.parametrize(
    "inpt, mods, expected, failmsg", [
        ["a", ["<ctrl>"],
         [(105, 0, 'p'), (38, 4, 'p'), (38, 4, 'r'), (105, 0, 'r')],
         "Xinterface doesn't send a modified key properly",
         ],
        ["a", ["<ctrl>", "<shift>"],
         [(105, 0, 'p'), (62, 0, 'p'), (38, 5, 'p'), (38, 5, 'r'), (105, 0, 'r'), (62, 0, 'r')],
         "Xinterface doesn't send a multiply-modified key properly",
         ],
    ])
    def test_send_modified_key(self, inpt, mods, expected, failmsg):
        with self.event_capture_patch, self.check_workaround_patch:
            self.ifc.send_modified_key(inpt, mods)
            # Need to cancel early. But cancel in tearDown as well in case this test fails.
            self.cancel()
        assert_that(self.ec.get_result(), is_(equal_to(expected)), failmsg)
