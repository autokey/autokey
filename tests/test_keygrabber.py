"""
Unit tests for KeyGrabber's mouse-click grace period.

Regression coverage for a race where the very mouse click used to press
"Record a key combination" is observed by AutoKey's own raw-input thread
independently of the GUI toolkit's click-to-slot delivery that registers
the KeyGrabber. Without a grace period, that click could arrive just after
registration and immediately cancel the recording via handle_mouseclick(),
before the user had a chance to press anything.
"""

import queue
import threading
import time
import unittest
from unittest.mock import MagicMock

from autokey.iomediator.keygrabber import InlineKeyGrabber, KeyGrabber, Recorder
from autokey.iomediator.iomediator import IoMediator
from autokey.iomediator import iomediator as iomediator_module
from autokey.model.key import Key


class TestKeyGrabberMouseClickGracePeriod(unittest.TestCase):

    def setUp(self):
        self._orig_listeners = IoMediator.listeners
        IoMediator.listeners = []
        self._orig_interface = iomediator_module.CURRENT_INTERFACE
        iomediator_module.CURRENT_INTERFACE = MagicMock()

    def tearDown(self):
        IoMediator.listeners = self._orig_listeners
        iomediator_module.CURRENT_INTERFACE = self._orig_interface

    def test_click_within_grace_period_is_ignored(self):
        parent = MagicMock()
        grabber = KeyGrabber(parent)
        grabber.start()

        grabber.handle_mouseclick(0, 0, 0, 0, None, None)

        parent.cancel_grab.assert_not_called()
        self.assertIn(grabber, IoMediator.listeners)
        iomediator_module.CURRENT_INTERFACE.ungrab_keyboard.assert_not_called()

    def test_click_after_grace_period_cancels(self):
        parent = MagicMock()
        grabber = KeyGrabber(parent)
        grabber.start()
        grabber.start_time = time.time() - KeyGrabber.CLICK_GRACE_PERIOD - 0.1

        grabber.handle_mouseclick(0, 0, 0, 0, None, None)

        parent.cancel_grab.assert_called_once()
        self.assertNotIn(grabber, IoMediator.listeners)
        iomediator_module.CURRENT_INTERFACE.ungrab_keyboard.assert_called_once()

    def test_real_keypress_still_sets_key(self):
        parent = MagicMock()
        grabber = KeyGrabber(parent)
        grabber.start()

        grabber.handle_keypress('f9', [], 'f9')

        parent.set_key.assert_called_once_with('f9', [])
        self.assertNotIn(grabber, IoMediator.listeners)


class TestInlineKeyGrabberMouseClickGracePeriod(unittest.TestCase):
    """InlineKeyGrabber overrides handle_mouseclick(), so it needs the same grace period."""

    def setUp(self):
        self._orig_listeners = IoMediator.listeners
        IoMediator.listeners = []
        self._orig_interface = iomediator_module.CURRENT_INTERFACE
        iomediator_module.CURRENT_INTERFACE = MagicMock()

    def tearDown(self):
        IoMediator.listeners = self._orig_listeners
        iomediator_module.CURRENT_INTERFACE = self._orig_interface

    def test_click_within_grace_period_is_ignored(self):
        parent = MagicMock()
        grabber = InlineKeyGrabber(parent)
        grabber.start()

        grabber.handle_mouseclick(0, 0, 0, 0, None, None)

        parent.inline_hotkey_cancelled.assert_not_called()
        self.assertIn(grabber, IoMediator.listeners)

    def test_click_after_grace_period_cancels(self):
        parent = MagicMock()
        grabber = InlineKeyGrabber(parent)
        grabber.start()
        grabber.start_time = time.time() - InlineKeyGrabber.CLICK_GRACE_PERIOD - 0.1

        grabber.handle_mouseclick(0, 0, 0, 0, None, None)

        parent.inline_hotkey_cancelled.assert_called_once()
        self.assertNotIn(grabber, IoMediator.listeners)


class TestHotkeyCaptureOwnsTheKeyboard(unittest.TestCase):
    """
    #1188: pressing a combination that is already bound, while a hotkey
    capture dialog is waiting for a key, used to run the existing binding
    because Service listens alongside the grabber. While a grabber is
    registered it must be the only listener that receives keypresses.
    """

    def setUp(self):
        self._orig_listeners = IoMediator.listeners
        IoMediator.listeners = []
        self._orig_interface = iomediator_module.CURRENT_INTERFACE
        iomediator_module.CURRENT_INTERFACE = MagicMock()
        self.service = MagicMock(spec=['handle_keypress', 'handle_mouseclick'])
        IoMediator.listeners.append(self.service)
        self.mediator = IoMediator.__new__(IoMediator)

    def tearDown(self):
        IoMediator.listeners = self._orig_listeners
        iomediator_module.CURRENT_INTERFACE = self._orig_interface

    def test_all_listeners_receive_keys_when_nothing_is_capturing(self):
        other = MagicMock(spec=['handle_keypress', 'handle_mouseclick'])
        IoMediator.listeners.append(other)

        self.assertEqual(self.mediator._keypress_targets(), [self.service, other])

    def test_only_the_grabber_receives_keys_while_capturing(self):
        grabber = KeyGrabber(MagicMock())
        grabber.start()

        self.assertEqual(self.mediator._keypress_targets(), [grabber])

    def test_only_the_inline_grabber_receives_keys_while_capturing(self):
        grabber = InlineKeyGrabber(MagicMock())
        grabber.start()

        self.assertEqual(self.mediator._keypress_targets(), [grabber])

    def test_macro_recorder_does_not_suppress_other_listeners(self):
        recorder = Recorder(MagicMock())
        IoMediator.listeners.append(recorder)

        self.assertEqual(self.mediator._keypress_targets(), [self.service, recorder])

    def _run_mediator_on(self, keys):
        """Drive the real IoMediator.run() loop with the given raw keys."""
        self.mediator.queue = queue.Queue()
        self.mediator.modifiers = {Key.NUMLOCK: False, Key.CAPSLOCK: False,
                                   Key.SHIFT: False, Key.ALT_GR: False}
        self.mediator._get_modifiers_on = lambda: []
        self.mediator.interface = MagicMock()
        self.mediator.interface.lookup_string.side_effect = lambda code, *args: code
        for key in keys:
            self.mediator.queue.put((key, ("title", "class")))
        self.mediator.queue.put((None, None))
        thread = threading.Thread(target=self.mediator.run)
        thread.start()
        thread.join(5)
        self.assertFalse(thread.is_alive())

    def test_capturing_a_bound_combination_does_not_fire_it_and_resumes_after(self):
        parent = MagicMock()
        grabber = KeyGrabber(parent)
        grabber.start()

        self._run_mediator_on(['<f7>', 'a'])

        # The captured key reached the grabber, not the service ...
        parent.set_key.assert_called_once_with('<f7>', [])
        # ... and the next key, after capture ended, reaches the service again.
        self.assertEqual([call.args[0] for call in self.service.handle_keypress.call_args_list], ['a'])
        iomediator_module.CURRENT_INTERFACE.ungrab_keyboard.assert_called_once()

    def test_inline_grabber_keeps_suppressing_until_it_is_stopped(self):
        parent = MagicMock()
        grabber = InlineKeyGrabber(parent)
        grabber.start()

        self._run_mediator_on(['<f7>', '<f8>'])
        self.service.handle_keypress.assert_not_called()

        grabber.stop()
        self._run_mediator_on(['<f9>'])
        self.assertEqual([call.args[0] for call in self.service.handle_keypress.call_args_list], ['<f9>'])


if __name__ == '__main__':
    unittest.main()
