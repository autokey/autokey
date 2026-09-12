"""
Unit tests for KeyGrabber's mouse-click grace period.

Regression coverage for a race where the very mouse click used to press
"Record a key combination" is observed by AutoKey's own raw-input thread
independently of the GUI toolkit's click-to-slot delivery that registers
the KeyGrabber. Without a grace period, that click could arrive just after
registration and immediately cancel the recording via handle_mouseclick(),
before the user had a chance to press anything.
"""

import time
import unittest
from unittest.mock import MagicMock

from autokey.iomediator.keygrabber import KeyGrabber
from autokey.iomediator.iomediator import IoMediator
from autokey.iomediator import iomediator as iomediator_module


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


if __name__ == '__main__':
    unittest.main()
