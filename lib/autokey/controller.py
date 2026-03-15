# Copyright (C) 2025 ClawOSS Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Game controller input handling for AutoKey.

This module provides support for using game controllers (gamepads, joysticks)
as input triggers for AutoKey actions. It uses the Linux evdev interface
for direct hardware access.
"""

import logging
import threading
import typing
from enum import Enum, auto

try:
    from evdev import InputDevice, list_devices, ecodes, categorize
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

logger = logging.getLogger(__name__)


class ControllerButton(Enum):
    """Common game controller button mappings."""
    A = auto()
    B = auto()
    X = auto()
    Y = auto()
    START = auto()
    SELECT = auto()
    HOME = auto()
    LB = auto()  # Left bumper
    RB = auto()  # Right bumper
    LS = auto()  # Left stick press
    RS = auto()  # Right stick press
    DPAD_UP = auto()
    DPAD_DOWN = auto()
    DPAD_LEFT = auto()
    DPAD_RIGHT = auto()


class ControllerAxis(Enum):
    """Common game controller axis mappings."""
    LS_X = auto()  # Left stick X
    LS_Y = auto()  # Left stick Y
    RS_X = auto()  # Right stick X
    RS_Y = auto()  # Right stick Y
    LT = auto()    # Left trigger
    RT = auto()    # Right trigger


# Mapping of common evdev codes to controller buttons
BUTTON_CODE_MAP = {
    304: ControllerButton.A,      # BTN_A / BTN_GAMEPAD
    305: ControllerButton.B,      # BTN_B
    307: ControllerButton.X,      # BTN_X
    308: ControllerButton.Y,      # BTN_Y
    315: ControllerButton.START,  # BTN_START
    314: ControllerButton.SELECT, # BTN_SELECT
    316: ControllerButton.HOME,   # BTN_MODE
    310: ControllerButton.LB,     # BTN_TL
    311: ControllerButton.RB,     # BTN_TR
    317: ControllerButton.LS,     # BTN_THUMBL
    318: ControllerButton.RS,     # BTN_THUMBR
}

# Mapping of common evdev codes to axes
AXIS_CODE_MAP = {
    0: ControllerAxis.LS_X,   # ABS_X
    1: ControllerAxis.LS_Y,   # ABS_Y
    2: ControllerAxis.LT,     # ABS_Z (often LT on Xbox-style)
    3: ControllerAxis.RS_X,   # ABS_RX
    4: ControllerAxis.RS_Y,   # ABS_RY
    5: ControllerAxis.RT,     # ABS_RZ (often RT on Xbox-style)
}

# DPAD is often mapped as axes on many controllers
DPAD_AXIS_MAP = {
    16: ('x', ControllerButton.DPAD_LEFT, ControllerButton.DPAD_RIGHT),  # ABS_HAT0X
    17: ('y', ControllerButton.DPAD_UP, ControllerButton.DPAD_DOWN),     # ABS_HAT0Y
}


class ControllerEvent:
    """Represents a controller input event."""
    
    def __init__(self, event_type: str, code: typing.Any, value: int, 
                 button: typing.Optional[ControllerButton] = None,
                 axis: typing.Optional[ControllerAxis] = None):
        self.event_type = event_type  # 'button_press', 'button_release', 'axis'
        self.code = code
        self.value = value
        self.button = button
        self.axis = axis
    
    def __repr__(self):
        return f"ControllerEvent({self.event_type}, button={self.button}, axis={self.axis}, value={self.value})"


class ControllerDevice:
    """Represents a connected game controller device."""
    
    def __init__(self, device_path: str, device_name: str = ""):
        self.device_path = device_path
        self.device_name = device_name
        self.device: typing.Optional[InputDevice] = None
        self._connected = False
        
    def connect(self) -> bool:
        """Connect to the controller device."""
        if not EVDEV_AVAILABLE:
            logger.warning("evdev library not available. Cannot connect to controller.")
            return False
            
        try:
            self.device = InputDevice(self.device_path)
            self.device_name = self.device.name
            self._connected = True
            logger.info(f"Connected to controller: {self.device_name} at {self.device_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to controller at {self.device_path}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the controller."""
        if self.device:
            try:
                self.device.close()
            except Exception:
                pass
        self._connected = False
        logger.info(f"Disconnected from controller: {self.device_name}")
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def read_events(self) -> typing.Generator[ControllerEvent, None, None]:
        """
        Read and yield controller events.
        
        Yields ControllerEvent objects for button presses, releases, and axis movements.
        """
        if not self._connected or not self.device:
            return
            
        try:
            for event in self.device.read_loop():
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    button = BUTTON_CODE_MAP.get(event.code)
                    
                    if key_event.keystate == key_event.key_down:
                        yield ControllerEvent('button_press', event.code, event.value, button=button)
                    elif key_event.keystate == key_event.key_up:
                        yield ControllerEvent('button_release', event.code, event.value, button=button)
                        
                elif event.type == ecodes.EV_ABS:
                    axis = AXIS_CODE_MAP.get(event.code)
                    
                    # Handle DPAD axes
                    if event.code in DPAD_AXIS_MAP:
                        direction, neg_button, pos_button = DPAD_AXIS_MAP[event.code]
                        if event.value < 0:
                            yield ControllerEvent('button_press', event.code, event.value, button=neg_button)
                        elif event.value > 0:
                            yield ControllerEvent('button_press', event.code, event.value, button=pos_button)
                    else:
                        yield ControllerEvent('axis', event.code, event.value, axis=axis)
                        
        except Exception as e:
            logger.error(f"Error reading controller events: {e}")
            self._connected = False


class ControllerManager:
    """
    Manages game controller detection and input handling.
    
    This class handles discovery of controllers, monitoring input events,
    and dispatching to registered listeners.
    """
    
    def __init__(self):
        self.controllers: typing.Dict[str, ControllerDevice] = {}
        self.listeners: typing.List[typing.Callable[[ControllerEvent, str], None]] = []
        self._monitoring = False
        self._monitor_thread: typing.Optional[threading.Thread] = None
        
    def is_available(self) -> bool:
        """Check if controller support is available (evdev installed)."""
        return EVDEV_AVAILABLE
    
    def discover_controllers(self) -> typing.List[ControllerDevice]:
        """
        Discover all connected game controller devices.
        
        Returns a list of ControllerDevice objects for detected controllers.
        """
        if not EVDEV_AVAILABLE:
            logger.warning("evdev library not available. Cannot discover controllers.")
            return []
            
        controllers = []
        
        try:
            for device_path in list_devices():
                try:
                    device = InputDevice(device_path)
                    
                    # Check if device has gamepad/joystick capabilities
                    capabilities = device.capabilities()
                    
                    has_buttons = ecodes.EV_KEY in capabilities
                    has_axes = ecodes.EV_ABS in capabilities
                    
                    # Look for gamepad-specific buttons
                    is_gamepad = False
                    if has_buttons:
                        key_codes = capabilities.get(ecodes.EV_KEY, [])
                        # Check for common gamepad buttons
                        if any(code in key_codes for code in [304, 305, 306, 307, 308]):
                            is_gamepad = True
                    
                    if is_gamepad or (has_buttons and has_axes):
                        controller = ControllerDevice(device_path, device.name)
                        controllers.append(controller)
                        logger.debug(f"Found controller: {device.name} at {device_path}")
                        
                except Exception as e:
                    logger.debug(f"Could not inspect device {device_path}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error discovering controllers: {e}")
            
        return controllers
    
    def add_listener(self, callback: typing.Callable[[ControllerEvent, str], None]):
        """
        Add a listener for controller events.
        
        The callback receives (ControllerEvent, device_name) for each event.
        """
        self.listeners.append(callback)
        
    def remove_listener(self, callback: typing.Callable[[ControllerEvent, str], None]):
        """Remove a listener."""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def start_monitoring(self, device_path: typing.Optional[str] = None):
        """
        Start monitoring controller input events.
        
        If device_path is None, discovers and monitors all available controllers.
        """
        if not EVDEV_AVAILABLE:
            logger.warning("Cannot start monitoring: evdev not available")
            return
            
        if self._monitoring:
            return
            
        self._monitoring = True
        
        if device_path:
            controller = ControllerDevice(device_path)
            if controller.connect():
                self.controllers[device_path] = controller
        else:
            # Auto-discover and connect to all controllers
            for controller in self.discover_controllers():
                if controller.connect():
                    self.controllers[controller.device_path] = controller
        
        # Start monitoring threads for each controller
        for controller in self.controllers.values():
            thread = threading.Thread(
                target=self._monitor_controller,
                args=(controller,),
                name=f"ControllerMonitor-{controller.device_name}",
                daemon=True
            )
            thread.start()
            
        logger.info(f"Started monitoring {len(self.controllers)} controller(s)")
    
    def stop_monitoring(self):
        """Stop monitoring controller events."""
        self._monitoring = False
        
        for controller in self.controllers.values():
            controller.disconnect()
            
        self.controllers.clear()
        logger.info("Stopped controller monitoring")
    
    def _monitor_controller(self, controller: ControllerDevice):
        """Monitor a single controller and dispatch events to listeners."""
        logger.debug(f"Starting monitor thread for {controller.device_name}")
        
        try:
            for event in controller.read_events():
                if not self._monitoring:
                    break
                    
                # Dispatch to all listeners
                for listener in self.listeners:
                    try:
                        listener(event, controller.device_name)
                    except Exception as e:
                        logger.error(f"Error in controller listener: {e}")
                        
        except Exception as e:
            logger.error(f"Controller monitor error for {controller.device_name}: {e}")


# Singleton instance for global use
_controller_manager: typing.Optional[ControllerManager] = None


def get_controller_manager() -> ControllerManager:
    """Get the global controller manager instance."""
    global _controller_manager
    if _controller_manager is None:
        _controller_manager = ControllerManager()
    return _controller_manager
