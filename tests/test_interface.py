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


@pytest.mark.parametrize("alt_list, expected, description", [
    # A stock layout: AltGr is keycode 108, carrying ISO_Level3_Shift itself.
    [[(108, 0)], (0, 1, 4, 5), "stock AltGr on 108"],
    # AltGr elsewhere. This is the case the old check missed: it required keycode
    # 108 specifically, so a keyboard with Control_R on 108 and AltGr on 92 lost
    # the AltGr levels entirely.
    [[(49, 0), (92, 0), (92, 2), (108, 2)], (0, 1, 4, 5), "AltGr on 92, Control_R on 108"],
    [[(92, 0)], (0, 1, 4, 5), "AltGr on 92 only"],
    # ISO_Level3_Shift appearing only as a secondary symbol is not an AltGr key.
    [[(108, 2)], (0, 1), "only as a shifted symbol"],
    [[(49, 1), (92, 3)], (0, 1), "only at non-zero offsets"],
    [[], (0, 1), "absent"],
])
def test_usable_offsets(alt_list, expected, description):
    """
    Offsets 4 and 5 are the AltGr levels. Whether AutoKey can reach them decides
    whether a character living there is considered typeable, or whether
    __sendString rewrites the keyboard mapping to borrow a spare keycode for it.
    """
    assert_that(autokey.interface.XInterfaceBase._usable_offsets(alt_list),
                is_(expected), description)
class TestKeymapChangeSkipping:
    """
    on_keys_changed() must not regrab every hotkey when the mapping is unchanged.

    A MappingNotify says the mapping *may* have changed, not that it did. Other
    clients re-apply the same mapping wholesale, and each of those events costs a
    full ungrab/regrab of every hotkey across every window.
    """

    @staticmethod
    def _interface(mapping, last):
        """An XInterfaceBase stand-in with just the state on_keys_changed touches."""
        iface = MagicMock()
        iface.localDisplay.get_keyboard_mapping.return_value = mapping
        iface._XInterfaceBase__lastKeyboardMapping = last
        iface._XInterfaceBase__ignoreRemap = False
        iface._XInterfaceBase__get_keyboard_mapping = (
            lambda: autokey.interface.XInterfaceBase._XInterfaceBase__get_keyboard_mapping(iface)
        )
        return iface

    @staticmethod
    def _run(iface):
        autokey.interface.XInterfaceBase.on_keys_changed(iface)

    def test_unchanged_mapping_does_not_regrab(self):
        mapping = [(1, 2), (3, 4)]
        iface = self._interface(mapping, list(mapping))
        self._run(iface)
        assert_that(iface._XInterfaceBase__ungrab_all_hotkeys.called, is_(False),
                    "an unchanged mapping must not provoke an ungrab")
        assert_that(iface._XInterfaceBase__delayedInitMappings.called, is_(False),
                    "an unchanged mapping must not provoke a regrab")

    def test_changed_mapping_does_regrab(self):
        iface = self._interface([(1, 2), (3, 4)], [(1, 2), (9, 9)])
        self._run(iface)
        assert_that(iface._XInterfaceBase__ungrab_all_hotkeys.called, is_(True))
        assert_that(iface._XInterfaceBase__delayedInitMappings.called, is_(True))

    def test_changed_mapping_is_remembered_for_next_time(self):
        mapping = [(1, 2), (3, 4)]
        iface = self._interface(mapping, [(1, 2), (9, 9)])
        self._run(iface)
        assert_that(iface._XInterfaceBase__lastKeyboardMapping, equal_to(mapping))

    def test_first_event_with_no_baseline_regrabs(self):
        """None means we have never read the mapping, so we cannot rule a change out."""
        iface = self._interface([(1, 2)], None)
        self._run(iface)
        assert_that(iface._XInterfaceBase__delayedInitMappings.called, is_(True))

    def test_unreadable_mapping_regrabs_rather_than_skipping(self):
        """If the mapping cannot be read, fail towards doing the work, not skipping it."""
        iface = self._interface([(1, 2)], [(1, 2)])
        iface.localDisplay.get_keyboard_mapping.side_effect = Xlib.error.ConnectionClosedError("gone")
        self._run(iface)
        assert_that(iface._XInterfaceBase__delayedInitMappings.called, is_(True))


class TestSelfRemapDoesNotRegrab:
    """
    AutoKey rewrites the keyboard mapping to borrow spare keycodes for characters
    the layout cannot reach. That rewrite genuinely changes the mapping, so the
    comparison in on_keys_changed() would see a real change and regrab everything.

    __ignoreRemap exists to prevent exactly that, but it is cleared when sending
    finishes rather than when the event arrives, so it loses the race.
    """

    @staticmethod
    def _interface():
        iface = MagicMock()
        iface._XInterfaceBase__lastKeyboardMapping = [(1, 2), (3, 4)]
        iface._XInterfaceBase__availableKeycodes = [8, 9]
        iface._XInterfaceBase__get_usable_char_keycode_and_offset.return_value = (None, None)
        iface._XInterfaceBase__get_keyboard_mapping = (
            lambda: autokey.interface.XInterfaceBase._XInterfaceBase__get_keyboard_mapping(iface)
        )
        # the mapping after our own rewrite differs from the baseline above
        iface.localDisplay.get_keyboard_mapping.return_value = [[0, 0], [0, 0], [0, 0]]
        return iface

    def test_own_remap_updates_the_remembered_mapping(self):
        iface = self._interface()
        autokey.interface.XInterfaceBase._XInterfaceBase__remap_characters(iface, True, "ä")
        assert_that(iface.localDisplay.change_keyboard_mapping.called, is_(True),
                    "the test needs the remap path to actually run")
        assert_that(iface._XInterfaceBase__lastKeyboardMapping,
                    equal_to(iface.localDisplay.get_keyboard_mapping.return_value),
                    "our own write must be recorded, or the event it provokes regrabs")

    def test_no_remap_leaves_the_remembered_mapping_alone(self):
        iface = self._interface()
        before = iface._XInterfaceBase__lastKeyboardMapping
        autokey.interface.XInterfaceBase._XInterfaceBase__remap_characters(iface, False, "a")
        assert_that(iface._XInterfaceBase__lastKeyboardMapping, equal_to(before))
