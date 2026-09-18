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
import functools

import Xlib

import pytest
from hamcrest import *
import unittest
from unittest.mock import Mock, MagicMock, patch

from autokey.model.key import Key
import autokey.interface
import autokey.model.abstract_window_filter

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
        pytest.param(
            "hi.",
            [(43, 0, 'p'), (43, 0, 'r'), (31, 0, 'p'), (31, 0, 'r'), (60, 0, 'p'), (60, 0, 'r')],
            "Xinterface doesn't send a normal string properly",
            id="normal_string"
        ),
        pytest.param(
            "",
            [],
            "Xinterface doesn't send an empty string properly",
            id="empty_string"
        ),
        pytest.param(
            " ",
            [(65, 0, 'p'), (65, 0, 'r')],
            "Xinterface doesn't send a space-only string properly",
            marks=pytest.mark.xfail(reason="Test requires X11/xhost and is incompatible with Wayland."),
            id="space_only_string"
        ),
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

    @pytest.mark.xfail(reason="Test requires X11/xhost and is incompatible with Wayland.")
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

    @pytest.mark.xfail(reason="Test requires X11/xhost and is incompatible with Wayland.")
    def test_send_modified_key(self, inpt, mods, expected, failmsg):
        with self.event_capture_patch, self.check_workaround_patch:
            self.ifc.send_modified_key(inpt, mods)
            # Need to cancel early. But cancel in tearDown as well in case this test fails.
            self.cancel()
        assert_that(self.ec.get_result(), is_(equal_to(expected)), failmsg)


# Tests for the lock-state query helper (query_lock_state) added for #1177.
# These use fake display objects. They do not need an X server.
from Xlib.error import XError
from autokey.interface import query_lock_state

XK_Num_Lock = 0xff7f
XK_Caps_Lock = 0xffe5


class FakePointerState:
    def __init__(self, mask):
        self.mask = mask


class FakeRootWindow:
    def __init__(self, mask, error=False):
        self._mask = mask
        self._error = error

    def query_pointer(self):
        if self._error:
            raise XError(None, b"\x00\x01\x00\x00" + b"\x00" * 28)
        return FakePointerState(self._mask)


class FakeDisplay:
    """
    A minimal fake of the python-xlib Display interface.
    """

    def __init__(self, keycodes, modifier_mapping):
        # keycodes: dict keysym -> keycode
        # modifier_mapping: list of eight lists of keycodes
        self._keycodes = keycodes
        self._modifier_mapping = modifier_mapping

    def keysym_to_keycode(self, keysym):
        return self._keycodes.get(keysym, 0)

    def get_modifier_mapping(self):
        return self._modifier_mapping


def make_display(numlock_code=66, capslock_code=77, numlock_modifier=4,
                 capslock_modifier=1):
    # Standard layout: NumLock on Mod2 (index 4), CapsLock on Lock (index 1).
    keycodes = {}
    if numlock_code:
        keycodes[XK_Num_Lock] = numlock_code
    if capslock_code:
        keycodes[XK_Caps_Lock] = capslock_code
    mapping = [[] for _ in range(8)]
    if numlock_code:
        mapping[numlock_modifier].append(numlock_code)
    if capslock_code:
        mapping[capslock_modifier].append(capslock_code)
    return FakeDisplay(keycodes, mapping)


def test_numlock_on():
    display = make_display()
    root = FakeRootWindow(mask=1 << 4)
    capslock_on, numlock_on = query_lock_state(display, root)
    assert_that(capslock_on, is_(False))
    assert_that(numlock_on, is_(True))


def test_numlock_off():
    display = make_display()
    root = FakeRootWindow(mask=0)
    capslock_on, numlock_on = query_lock_state(display, root)
    assert_that(capslock_on, is_(False))
    assert_that(numlock_on, is_(False))


def test_capslock_on():
    display = make_display()
    root = FakeRootWindow(mask=1 << 1)
    capslock_on, numlock_on = query_lock_state(display, root)
    assert_that(capslock_on, is_(True))
    assert_that(numlock_on, is_(False))


def test_both_locks_on():
    display = make_display()
    root = FakeRootWindow(mask=(1 << 1) | (1 << 4))
    capslock_on, numlock_on = query_lock_state(display, root)
    assert_that(capslock_on, is_(True))
    assert_that(numlock_on, is_(True))


def test_non_standard_modifier_index():
    # NumLock bound to Mod3 (index 5) instead of the usual Mod2.
    display = make_display(numlock_modifier=5)
    root = FakeRootWindow(mask=1 << 5)
    capslock_on, numlock_on = query_lock_state(display, root)
    assert_that(numlock_on, is_(True))
    assert_that(capslock_on, is_(False))


def test_keycode_absent_from_mapping():
    # NumLock keycode known but bound to no modifier: state stays off.
    display = make_display()
    display._modifier_mapping[4] = []
    root = FakeRootWindow(mask=1 << 4)
    capslock_on, numlock_on = query_lock_state(display, root)
    assert_that(capslock_on, is_(False))
    assert_that(numlock_on, is_(False))


def test_no_numlock_key():
    display = make_display(numlock_code=0)
    root = FakeRootWindow(mask=1 << 4)
    capslock_on, numlock_on = query_lock_state(display, root)
    assert_that(capslock_on, is_(False))
    assert_that(numlock_on, is_(False))


def test_pointer_query_error_masks_state():
    display = make_display()
    root = FakeRootWindow(mask=1 << 4, error=True)
    capslock_on, numlock_on = query_lock_state(display, root)
    assert_that(capslock_on, is_(False))
    assert_that(numlock_on, is_(False))


class TestGrabWalkWindowFilter():
    """
    Regression tests for which windows an X11 key grab is placed on.

    __grab_ungrab_recurse() obtains WindowInfo with traverse=False, so window-manager
    frames and other intermediate windows report an empty title and class (see
    _get_window_info()). An include filter simply fails to match those and the walk
    descends. An inverted filter would "not match" them and therefore claim the whole
    subtree -- including the application the user asked to exclude -- grabbing the key
    there and then declining to fire, which swallows the keystroke.

    The walk is exercised as an unbound function against a stub self, so that the test
    does not construct XInterfaceBase (whose __init__ starts long-lived threads).
    """

    TERMINAL = autokey.interface.WindowInfo("bjohas@host: ~", "gnome-terminal-server.Gnome-terminal")
    FIREFOX = autokey.interface.WindowInfo("Mozilla Firefox", "Navigator.Firefox")
    UNKNOWN = autokey.interface.WindowInfo("", "")

    def setup_method(self):
        self.info = {}

        def window(info, children):
            w = MagicMock()
            w.query_tree.return_value.children = children
            self.info[w] = info
            return w

        # root -> frame -> client -> widget, per application. Only the client window
        # carries a real title and class, exactly as traverse=False reports them.
        self.term_widget = window(self.UNKNOWN, [])
        self.term_client = window(self.TERMINAL, [self.term_widget])
        self.term_frame = window(self.UNKNOWN, [self.term_client])

        self.ff_widget = window(self.UNKNOWN, [])
        self.ff_client = window(self.FIREFOX, [self.ff_widget])
        self.ff_frame = window(self.UNKNOWN, [self.ff_client])

        self.root = window(self.UNKNOWN, [self.term_frame, self.ff_frame])

    def _item(self, regex, inverted):
        item = autokey.model.abstract_window_filter.AbstractWindowFilter()
        item.parent = None
        item.set_window_titles(regex)
        item.isInverted = inverted
        item.hotKey = "a"
        item.modifiers = ["<hyper>"]
        return item

    def _walk(self, item, grab=True):
        # Resolved here, not as a class attribute: a plain function assigned to a
        # class attribute becomes a method of that class, which would silently shift
        # every argument by one.
        walk = autokey.interface.XInterfaceBase._XInterfaceBase__grab_ungrab_recurse

        stub = MagicMock()
        stub.mediator.windowInterface.get_window_info = \
            lambda window, traverse=True: self.info[window]
        # The walk recurses through self; bind it so recursion reaches the real code.
        stub._XInterfaceBase__grab_ungrab_recurse = functools.partial(walk, stub)

        walk(stub, item, self.root, grab=grab)

        recorder = stub._XInterfaceBase__grabHotkey if grab \
            else stub._XInterfaceBase__ungrabHotkey
        return [call.args[2] for call in recorder.call_args_list]

    def test_inverted_filter_does_not_grab_in_the_excluded_application(self):
        grabbed = self._walk(self._item("gnome-terminal.*", inverted=True))

        assert_that(grabbed, has_item(self.ff_client))
        for window in (self.term_frame, self.term_client, self.term_widget):
            assert_that(grabbed, is_not(has_item(window)))

    def test_include_filter_grabs_only_the_matching_application(self):
        grabbed = self._walk(self._item("Navigator.Firefox", inverted=False))

        assert_that(grabbed, has_item(self.ff_client))
        for window in (self.term_frame, self.term_client, self.term_widget):
            assert_that(grabbed, is_not(has_item(window)))

    def test_ungrab_covers_exactly_the_same_windows_as_grab(self):
        item = self._item("gnome-terminal.*", inverted=True)

        assert_that(set(self._walk(item, grab=False)), is_(set(self._walk(item, grab=True))))
