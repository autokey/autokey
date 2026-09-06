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
import queue
import time

import Xlib
from Xlib import X, display
from Xlib.ext import xtest

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


class TestModifierKeyReleaseForwarding:
    """
    Regression harness for https://github.com/autokey/autokey/issues/1007.

    When a hotkey combo like <ctrl>+1 is grabbed and released out of order
    (the modifier released before the non-modifier key), X's implicit
    keyboard grab swallows the modifier's KeyRelease: it reaches AutoKey's
    connection but never the application the user was typing into, leaving
    the modifier "stuck" from that application's point of view.

    This exercises AutoKey's real grab_key/__flush_events machinery against
    a live (Xvfb) X server, with a second connection standing in for "the
    focused application", rather than mocking the interface layer.
    """

    def setup_method(self):
        # __grab_ungrab_hotkey reads common.ARGS.grabkey_logging directly; outside
        # a real app bootstrap (argument_parser.parse_args()) it's None, which
        # makes every real grab silently no-op (the AttributeError is swallowed
        # by __eventLoop's catch-all). Populate it the same way the app does.
        import autokey.argument_parser
        import autokey.common
        self.args_patch = patch.object(
            autokey.common, "ARGS",
            autokey.argument_parser._generate_argument_parser().parse_args([]))
        self.args_patch.start()

        # XInterfaceBase.queue is a *class* attribute, shared by every
        # instance in the process. If an earlier test's interface left its
        # (None, None) shutdown sentinel sitting in it, our instance's fresh
        # eventThread would consume that sentinel first and exit immediately,
        # leaving every real call we enqueue (including __initMappings' own)
        # stuck forever -- queue.join() would then hang for good. Give this
        # test its own queue so it can't inherit another test's leftovers --
        # via patch.object (not a plain assignment) so it's restored on
        # teardown instead of leaking a fresh queue forward into whichever
        # test runs next in the session.
        self.queue_patch = patch.object(
            autokey.interface.XInterfaceBase, "queue", queue.Queue())
        self.queue_patch.start()

        self.app = MagicMock()
        self.app.configManager.hotKeys = []
        self.app.configManager.hotKeyFolders = []
        self.app.configManager.globalHotkeys = []
        self.mediator = MagicMock()
        self.ifc = autokey.interface.XRecordInterface(self.mediator, self.app)
        # Let the (empty) initial hotkey grab enqueued by __initMappings settle
        # before the test enqueues its own grab.
        self.ifc.queue.join()

        # A second connection + window standing in for the focused application.
        self.target_display = display.Display()
        screen = self.target_display.screen()
        self.target_window = screen.root.create_window(
            0, 0, 100, 100, 0, screen.root_depth, X.InputOutput, X.CopyFromParent,
            background_pixel=screen.white_pixel,
            event_mask=X.KeyPressMask | X.KeyReleaseMask,
        )
        self.target_window.map()
        self.target_display.sync()
        self.target_window.set_input_focus(X.RevertToParent, X.CurrentTime)
        self.target_display.sync()
        self._drain(self.target_display)

    def teardown_method(self):
        try:
            self.target_display.close()
        except Exception:
            pass
        try:
            autokey.interface.XInterfaceBase.cancel(self.ifc)
        except RuntimeError:
            # Complaints about joining self thread before it starts.
            pass
        except Xlib.error.ConnectionClosedError:
            # Complaints about closing after closing already.
            pass
        self.queue_patch.stop()
        self.args_patch.stop()

    @staticmethod
    def _drain(disp):
        while disp.pending_events():
            disp.next_event()

    @staticmethod
    def _wait_for_event(disp, event_type, detail, timeout=3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            while disp.pending_events():
                evt = disp.next_event()
                if evt.type == event_type and evt.detail == detail:
                    return evt
            time.sleep(0.05)
        return None

    @pytest.mark.xfail(
        reason="Known bug, autokey/autokey#1007: the modifier's KeyRelease "
               "is swallowed by AutoKey's X11 grab instead of being "
               "forwarded to the focused window. strict=True so this turns "
               "into a hard failure (XPASS) the moment a real fix lands, as "
               "a prompt to remove this marker.",
        strict=True,
    )
    def test_modifier_release_reaches_focused_window_after_hotkey_use(self):
        """
        Press <ctrl>, press '1' (triggering the grabbed hotkey), release
        <ctrl> *before* releasing '1'. The focused window should still see
        the <ctrl> KeyRelease.
        """
        hotkey = Mock()
        hotkey.hotKey = '1'
        hotkey.modifiers = [Key.CONTROL]
        hotkey.get_applicable_regex.return_value = None

        self.ifc.grab_hotkey(hotkey)
        self.ifc.queue.join()

        ctrl_keycode = self.ifc._XInterfaceBase__lookupKeyCode(Key.CONTROL)
        one_keycode = self.ifc._XInterfaceBase__lookupKeyCode('1')

        disp = self.ifc.localDisplay
        xtest.fake_input(disp, X.KeyPress, ctrl_keycode)
        disp.sync()
        xtest.fake_input(disp, X.KeyPress, one_keycode)
        disp.sync()
        xtest.fake_input(disp, X.KeyRelease, ctrl_keycode)
        disp.sync()
        xtest.fake_input(disp, X.KeyRelease, one_keycode)
        disp.sync()

        evt = self._wait_for_event(self.target_display, X.KeyRelease, ctrl_keycode)
        assert evt is not None, (
            "Focused window never received the <ctrl> KeyRelease event; "
            "the modifier is left stuck from that application's point of "
            "view (autokey/autokey#1007)."
        )
