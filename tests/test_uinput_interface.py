"""
Unit tests for the mouse-button handling in uinput_interface.py.

Regression coverage for a bug where evdev.categorize() gives multi-alias
keycodes (e.g. mouse buttons) as a tuple, but the code checked
`type(x) == list`, so BTN_LEFT/RIGHT/MIDDLE always fell through to the
"couldn't identify this key" fallback (evdev code 0, KEY_RESERVED) --
corrupting the keyboard-hotkey pipeline with a fake "reserved" keypress
on every mouse click, and also revealing that mouse clicks were never
actually routed to the mouse-click dispatch path at all.
"""

import unittest
from unittest.mock import MagicMock

import autokey.uinput_interface as uinput_interface
from autokey.model.button import Button


class TestTranslateToEvdevButtons(unittest.TestCase):
    """translate_to_evdev/lookup_string only need class-level attributes
    (inv_btn_map, btn_map, inv_map, etc.), so a bare instance (bypassing
    __init__'s hardware setup) is enough to exercise them directly."""

    def setUp(self):
        self.iface = uinput_interface.UInputInterface.__new__(uinput_interface.UInputInterface)

    def test_translate_tuple_form_button(self):
        result = self.iface.translate_to_evdev(('BTN_LEFT', 'BTN_MOUSE'))
        self.assertEqual(result, (Button.LEFT, False))

    def test_translate_tuple_form_right_button(self):
        result = self.iface.translate_to_evdev(('BTN_RIGHT',))
        self.assertEqual(result, (Button.RIGHT, False))

    def test_translate_unrecognized_tuple_falls_back_to_reserved(self):
        # A tuple that isn't a known BTN_* name should still fall through
        # to the documented (0, False) fallback, not raise.
        result = self.iface.translate_to_evdev(('SOMETHING_UNKNOWN',))
        self.assertEqual(result, (0, False))

    def test_lookup_string_does_not_crash_on_button_tuple(self):
        # Before the fix, this raised AttributeError: 'tuple' object has
        # no attribute 'replace', once translate_to_evdev correctly
        # returned a Button enum for a mouse button.
        result = self.iface.lookup_string(
            (('BTN_LEFT', 'BTN_MOUSE'), False),
            shifted=False, num_lock=False, altGrid=False,
        )
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, 'reserved')


class TestHandleMouseclick(unittest.TestCase):

    def _make_interface(self):
        iface = uinput_interface.UInputInterface.__new__(uinput_interface.UInputInterface)
        iface.mediator = MagicMock()
        iface.mediator.windowInterface.get_window_info.return_value = 'window-info'
        iface.mouse_location = MagicMock(return_value=[12, 34])
        return iface

    def _click_event(self, code):
        return MagicMock(type=uinput_interface.e.EV_KEY, code=code, value=0)

    def test_recognized_button_dispatches_to_mediator(self):
        iface = self._make_interface()
        del iface.mediator.windowInterface.get_active_window
        iface.handle_mouseclick(self._click_event(uinput_interface.e.BTN_LEFT))

        iface.mediator.handle_mouse_click.assert_called_once()
        args = iface.mediator.handle_mouse_click.call_args[0]
        root_x, root_y, rel_x, rel_y, button, window_info = args
        self.assertEqual((root_x, root_y), (12, 34))
        self.assertEqual(button, Button.LEFT)
        self.assertEqual(window_info, 'window-info')
        # No get_active_window() available -> falls back to root coords.
        self.assertEqual((rel_x, rel_y), (12, 34))

    def test_unrecognized_button_is_ignored(self):
        iface = self._make_interface()
        # BTN_SIDE isn't in inv_btn_map -- should be a no-op, not a crash
        # or a fake dispatch.
        iface.handle_mouseclick(self._click_event(uinput_interface.e.BTN_SIDE))
        iface.mediator.handle_mouse_click.assert_not_called()

    def test_uses_window_relative_position_when_available(self):
        iface = self._make_interface()
        iface.mediator.windowInterface.get_active_window.return_value = {'x': 2, 'y': 4}
        iface.handle_mouseclick(self._click_event(uinput_interface.e.BTN_LEFT))

        args = iface.mediator.handle_mouse_click.call_args[0]
        root_x, root_y, rel_x, rel_y, button, window_info = args
        self.assertEqual((root_x, root_y), (12, 34))
        self.assertEqual((rel_x, rel_y), (10, 30))

    def test_mouse_location_failure_does_not_crash(self):
        iface = self._make_interface()
        iface.mouse_location.side_effect = Exception('boom')
        del iface.mediator.windowInterface.get_active_window
        iface.handle_mouseclick(self._click_event(uinput_interface.e.BTN_LEFT))

        args = iface.mediator.handle_mouse_click.call_args[0]
        root_x, root_y, rel_x, rel_y, button, window_info = args
        self.assertIsNone(root_x)
        self.assertIsNone(root_y)
        self.assertEqual(button, Button.LEFT)


if __name__ == '__main__':
    unittest.main()
