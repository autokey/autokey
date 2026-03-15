#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests for the game controller module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

# Mock evdev before importing controller
evdev_mock = MagicMock()
evdev_mock.EV_KEY = 1
evdev_mock.EV_ABS = 3

with patch.dict('sys.modules', {'evdev': evdev_mock}):
    from autokey.controller import (
        ControllerButton,
        ControllerAxis,
        ControllerEvent,
        ControllerDevice,
        ControllerManager,
        EVDEV_AVAILABLE,
        BUTTON_CODE_MAP,
        AXIS_CODE_MAP,
    )


class TestControllerButton(unittest.TestCase):
    """Test ControllerButton enum."""
    
    def test_button_values(self):
        """Test that all expected buttons exist."""
        self.assertIsNotNone(ControllerButton.A)
        self.assertIsNotNone(ControllerButton.B)
        self.assertIsNotNone(ControllerButton.X)
        self.assertIsNotNone(ControllerButton.Y)
        self.assertIsNotNone(ControllerButton.START)
        self.assertIsNotNone(ControllerButton.SELECT)
        self.assertIsNotNone(ControllerButton.HOME)
        self.assertIsNotNone(ControllerButton.LB)
        self.assertIsNotNone(ControllerButton.RB)
        self.assertIsNotNone(ControllerButton.LS)
        self.assertIsNotNone(ControllerButton.RS)
        self.assertIsNotNone(ControllerButton.DPAD_UP)
        self.assertIsNotNone(ControllerButton.DPAD_DOWN)
        self.assertIsNotNone(ControllerButton.DPAD_LEFT)
        self.assertIsNotNone(ControllerButton.DPAD_RIGHT)


class TestControllerAxis(unittest.TestCase):
    """Test ControllerAxis enum."""
    
    def test_axis_values(self):
        """Test that all expected axes exist."""
        self.assertIsNotNone(ControllerAxis.LS_X)
        self.assertIsNotNone(ControllerAxis.LS_Y)
        self.assertIsNotNone(ControllerAxis.RS_X)
        self.assertIsNotNone(ControllerAxis.RS_Y)
        self.assertIsNotNone(ControllerAxis.LT)
        self.assertIsNotNone(ControllerAxis.RT)


class TestControllerEvent(unittest.TestCase):
    """Test ControllerEvent class."""
    
    def test_button_event_creation(self):
        """Test creating a button event."""
        event = ControllerEvent(
            event_type='button_press',
            code=304,
            value=1,
            button=ControllerButton.A
        )
        self.assertEqual(event.event_type, 'button_press')
        self.assertEqual(event.code, 304)
        self.assertEqual(event.value, 1)
        self.assertEqual(event.button, ControllerButton.A)
        self.assertIsNone(event.axis)
    
    def test_axis_event_creation(self):
        """Test creating an axis event."""
        event = ControllerEvent(
            event_type='axis',
            code=0,
            value=16000,
            axis=ControllerAxis.LS_X
        )
        self.assertEqual(event.event_type, 'axis')
        self.assertEqual(event.code, 0)
        self.assertEqual(event.value, 16000)
        self.assertEqual(event.axis, ControllerAxis.LS_X)
        self.assertIsNone(event.button)


class TestControllerDevice(unittest.TestCase):
    """Test ControllerDevice class."""
    
    def test_initialization(self):
        """Test device initialization."""
        device = ControllerDevice('/dev/input/event0', 'Test Controller')
        self.assertEqual(device.device_path, '/dev/input/event0')
        self.assertEqual(device.device_name, 'Test Controller')
        self.assertFalse(device.is_connected)
    
    @patch('autokey.controller.EVDEV_AVAILABLE', False)
    def test_connect_without_evdev(self):
        """Test connect fails gracefully without evdev."""
        device = ControllerDevice('/dev/input/event0')
        result = device.connect()
        self.assertFalse(result)
        self.assertFalse(device.is_connected)


class TestControllerManager(unittest.TestCase):
    """Test ControllerManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ControllerManager()
    
    @patch('autokey.controller.EVDEV_AVAILABLE', False)
    def test_is_available_without_evdev(self):
        """Test is_available returns False without evdev."""
        self.assertFalse(self.manager.is_available())
    
    def test_add_remove_listener(self):
        """Test adding and removing listeners."""
        callback = Mock()
        
        # Add listener
        self.manager.add_listener(callback)
        self.assertIn(callback, self.manager.listeners)
        
        # Remove listener
        self.manager.remove_listener(callback)
        self.assertNotIn(callback, self.manager.listeners)
    
    @patch('autokey.controller.EVDEV_AVAILABLE', False)
    def test_start_monitoring_without_evdev(self):
        """Test start_monitoring is no-op without evdev."""
        # Should not raise any exceptions
        self.manager.start_monitoring()
        self.assertFalse(self.manager._monitoring)
    
    def test_stop_monitoring(self):
        """Test stop_monitoring clears controllers."""
        # Add a mock controller
        mock_controller = Mock()
        self.manager.controllers['/dev/input/event0'] = mock_controller
        
        self.manager.stop_monitoring()
        
        mock_controller.disconnect.assert_called_once()
        self.assertEqual(len(self.manager.controllers), 0)


class TestButtonCodeMap(unittest.TestCase):
    """Test button code mappings."""
    
    def test_common_button_mappings(self):
        """Test that common button codes are mapped."""
        # BTN_A / BTN_GAMEPAD = 304
        self.assertEqual(BUTTON_CODE_MAP[304], ControllerButton.A)
        # BTN_B = 305
        self.assertEqual(BUTTON_CODE_MAP[305], ControllerButton.B)
        # BTN_X = 307
        self.assertEqual(BUTTON_CODE_MAP[307], ControllerButton.X)
        # BTN_Y = 308
        self.assertEqual(BUTTON_CODE_MAP[308], ControllerButton.Y)
        # BTN_START = 315
        self.assertEqual(BUTTON_CODE_MAP[315], ControllerButton.START)


class TestAxisCodeMap(unittest.TestCase):
    """Test axis code mappings."""
    
    def test_common_axis_mappings(self):
        """Test that common axis codes are mapped."""
        # ABS_X = 0
        self.assertEqual(AXIS_CODE_MAP[0], ControllerAxis.LS_X)
        # ABS_Y = 1
        self.assertEqual(AXIS_CODE_MAP[1], ControllerAxis.LS_Y)
        # ABS_RX = 3
        self.assertEqual(AXIS_CODE_MAP[3], ControllerAxis.RS_X)
        # ABS_RY = 4
        self.assertEqual(AXIS_CODE_MAP[4], ControllerAxis.RS_Y)


class TestAbstractControllerTrigger(unittest.TestCase):
    """Test AbstractControllerTrigger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid issues with evdev mocking
        with patch.dict('sys.modules', {'evdev': MagicMock()}):
            from autokey.model.abstract_controller import AbstractControllerTrigger
            self.AbstractControllerTrigger = AbstractControllerTrigger
            self.trigger = self.AbstractControllerTrigger()
    
    def test_initialization(self):
        """Test initial state."""
        self.assertIsNone(self.trigger.controller_button)
        self.assertIsNone(self.trigger.controller_axis)
        self.assertEqual(self.trigger.axis_threshold, 16384)
        self.assertEqual(self.trigger.controller_name_filter, "")
    
    def test_set_controller_trigger_button(self):
        """Test setting a button trigger."""
        from autokey.controller import ControllerButton
        from autokey.model.helpers import TriggerMode
        
        self.trigger.set_controller_trigger(button=ControllerButton.A)
        
        self.assertEqual(self.trigger.controller_button, ControllerButton.A)
        self.assertIn(TriggerMode.CONTROLLER, self.trigger.modes)
    
    def test_unset_controller_trigger(self):
        """Test unsetting a controller trigger."""
        from autokey.controller import ControllerButton
        from autokey.model.helpers import TriggerMode
        
        self.trigger.set_controller_trigger(button=ControllerButton.A)
        self.trigger.unset_controller_trigger()
        
        self.assertIsNone(self.trigger.controller_button)
        self.assertNotIn(TriggerMode.CONTROLLER, self.trigger.modes)
    
    def test_get_serializable_empty(self):
        """Test serialization with empty trigger."""
        data = self.trigger.get_serializable()
        
        self.assertIsNone(data['controller_button'])
        self.assertIsNone(data['controller_axis'])
        self.assertEqual(data['axis_threshold'], 16384)
        self.assertEqual(data['controller_name_filter'], "")


if __name__ == '__main__':
    unittest.main()
