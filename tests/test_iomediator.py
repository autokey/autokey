# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

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

import typing

import pytest
import unittest
from hamcrest import *

import autokey.iomediator.constants as iomediator_constants
from autokey.iomediator.iomediator import IoMediator
import autokey.model.key
import autokey.common
from autokey.model.phrase import SendMode
from unittest.mock import MagicMock

from autokey.model.key import Key


def generate_tests_for_key_split_re():
    """Yields test_input_str, expected_split_list"""
    # Values taken from original test code
    yield "<ctrl>+y", ["", "<ctrl>+", "y"]
    yield "asdf <ctrl>+y asdf ", ["asdf ", "<ctrl>+", "y asdf "]
    yield "<table><ctrl>+y</table>", ["", "<table>", "", "<ctrl>+", "y", "</table>", ""]
    yield "<!<alt_gr>+8CDATA<alt_gr>+8", ["<!", "<alt_gr>+", "8CDATA", "<alt_gr>+", "8"]
    yield "<ctrl>y", ["", "<ctrl>", "y"]
    yield "Test<tab>More text", ["Test", "<tab>", "More text"]


@pytest.mark.parametrize("input_string, expected_split", generate_tests_for_key_split_re())
def test_key_split_re(input_string: str, expected_split: typing.List[str]):
    assert_that(
        autokey.model.key.KEY_SPLIT_RE.split(input_string),
        has_items(*expected_split)
    )


class MockInterface():
    def __init__(self):
        self.received = []
        self.modifiers = []

    def get_result(self):
        return "|".join(self.received)
    def get_modifiers(self):
        return self.modifiers

    def send_modified_key(self, string, mods):
        self.received.append("+".join(mods))
        self.modifiers.append(mods)
        self.received.append(string)

    def send_key(self, key):
        self.received.append(key)

    def send_string(self, s):
        self.received.append(s)





@pytest.mark.parametrize("inpt, failmsg", [
    ["hello this string is a test", "iomediator doesn't send a normal string properly"],
    ["", "iomediator doesn't send a blank string properly"],
    ["---", "iomediator doesn't send all dashes properly"],
    ["- -", "iomediator doesn't send this properly"],
])
def test_send_string(inpt: str, failmsg):
    interface = unittest.mock.Mock(wraps=MockInterface())
    IoMediator._send_string(inpt, interface)
    assert_that(
        interface.get_result(),
        is_(equal_to(inpt)),
        failmsg
    )


@pytest.mark.parametrize("inpt, result, mods, failmsg", [
    ["i want <ctrl>+a", "i want |<ctrl>|a", [["<ctrl>"]], "iomediator doesn't send a modified string properly"],
    ["i want <ctrl>+a and <alt>+<super>+t", "i want |<ctrl>|a| and |<alt>+<super>|t", [["<ctrl>"], ["<alt>", "<super>"]], "iomediator doesn't send a modified string properly"],
])
def test_send_string_modified(inpt: str, result: typing.List[str], mods: typing.List[str], failmsg):
    interface = unittest.mock.Mock(wraps=MockInterface())
    IoMediator._send_string(inpt, interface)
    assert_that(
        interface.get_result(),
        is_(equal_to(result)),
        failmsg
    )
    assert_that(
        interface.get_modifiers(),
        is_(equal_to(mods)),
        failmsg
    )


@pytest.mark.parametrize("ui_type", ["QT", "GTK"])
def test_send_string_clipboard_marshals_onto_toolkit_main_thread(ui_type):
    """
    Regression test for a bug where GTK's clipboard-paste path was called
    directly on a background thread instead of being marshaled onto the
    GTK main thread via exec_in_main() -- unlike Qt, which already did
    this correctly. On a real GNOME Wayland session this caused an
    indefinite hang, because GTK's Wayland clipboard backend requires its
    synchronous calls (e.g. Gtk.Clipboard.wait_for_text()) to happen on
    the thread running the GLib main loop. Both toolkits must route
    through exec_in_main(); only "headless" (no toolkit main loop to
    marshal onto) may call directly.
    """
    original_ui_type = autokey.common.USED_UI_TYPE
    autokey.common.USED_UI_TYPE = ui_type
    try:
        mediator = IoMediator.__new__(IoMediator)
        mediator.app = unittest.mock.Mock()
        mediator.send_string_clipboard("some text", SendMode.CB_CTRL_V)
        mediator.app.exec_in_main.assert_called_once()
    finally:
        autokey.common.USED_UI_TYPE = original_ui_type


def test_send_string_clipboard_headless_calls_directly():
    """headless has no toolkit main loop, so it must not use exec_in_main()."""
    original_ui_type = autokey.common.USED_UI_TYPE
    autokey.common.USED_UI_TYPE = "headless"
    try:
        mediator = IoMediator.__new__(IoMediator)
        mediator.app = unittest.mock.Mock()
        mediator.clipboard = unittest.mock.Mock(text="")
        mediator.interface = unittest.mock.Mock()
        with unittest.mock.patch.object(IoMediator, "send_string"), \
             unittest.mock.patch.object(IoMediator, "_wait_responsively"):
            mediator.send_string_clipboard("some text", SendMode.CB_CTRL_V)
        mediator.app.exec_in_main.assert_not_called()
    finally:
        autokey.common.USED_UI_TYPE = original_ui_type


def test_clear_modifiers_releases_via_xtest_not_xsendevent():
    """
    Held modifiers must be released through IoMediator.release_key(), which routes
    to interface.fake_keyup() and XTEST.

    interface.release_key() sends an XSendEvent instead. That is delivered to a
    client but never enters the server's input pipeline, so the server's key state
    and XKB modifier state are untouched: the modifier the user is physically
    holding is not cleared, and every character of the expansion arrives with it
    still applied. That was the behaviour in 0.96.0; 2ad54f5 fixed it here without
    a test, so nothing currently stops it regressing.
    """
    mediator = MagicMock()
    mediator.releasedModifiers = []
    mediator.modifiers = {Key.CONTROL: True, Key.HYPER: True, Key.SHIFT: False}

    IoMediator._clear_modifiers(mediator)

    assert_that(mediator.releasedModifiers, contains_inanyorder(Key.CONTROL, Key.HYPER))
    assert_that(mediator.release_key.call_count, is_(2))
    mediator.interface.release_key.assert_not_called()


def test_reapply_modifiers_presses_via_xtest_not_xsendevent():
    mediator = MagicMock()
    mediator.releasedModifiers = [Key.CONTROL, Key.HYPER]

    IoMediator._reapply_modifiers(mediator)

    assert_that(mediator.press_key.call_count, is_(2))
    mediator.interface.press_key.assert_not_called()


def test_capslock_and_numlock_are_not_cleared():
    mediator = MagicMock()
    mediator.releasedModifiers = []
    mediator.modifiers = {Key.CAPSLOCK: True, Key.NUMLOCK: True, Key.CONTROL: True}

    IoMediator._clear_modifiers(mediator)

    assert_that(mediator.releasedModifiers, is_([Key.CONTROL]))


def test_modifier_keysyms_resolve_to_the_left_hand_variant():
    """
    XK_TO_AK_MAP maps both variants of each modifier onto a single Key, so simply
    inverting it keeps whichever came last -- the right-hand one. Releasing Hyper_R
    does not clear a Hyper_L the user is holding, so the explicit overrides below
    the inversion are load-bearing, not cosmetic.
    """
    from Xlib import XK
    from autokey.interface import AK_TO_XK_MAP

    assert_that(AK_TO_XK_MAP[Key.SHIFT], is_(XK.XK_Shift_L))
    assert_that(AK_TO_XK_MAP[Key.CONTROL], is_(XK.XK_Control_L))
    assert_that(AK_TO_XK_MAP[Key.ALT], is_(XK.XK_Alt_L))
    assert_that(AK_TO_XK_MAP[Key.SUPER], is_(XK.XK_Super_L))
    assert_that(AK_TO_XK_MAP[Key.HYPER], is_(XK.XK_Hyper_L))
    assert_that(AK_TO_XK_MAP[Key.META], is_(XK.XK_Meta_L))
