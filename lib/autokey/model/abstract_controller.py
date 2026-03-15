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

import typing

from autokey.model.helpers import TriggerMode
from autokey.model.abstract_window_filter import AbstractWindowFilter
from autokey.controller import ControllerButton, ControllerAxis


class AbstractControllerTrigger(AbstractWindowFilter):
    """
    Abstract base class for controller input triggers.
    
    This class provides the foundation for triggering AutoKey actions
    using game controller inputs (buttons and axes).
    """
    
    def __init__(self):
        self.controller_button: typing.Optional[ControllerButton] = None
        self.controller_axis: typing.Optional[ControllerAxis] = None
        self.axis_threshold: int = 16384  # Default threshold for axis triggers (~50%)
        self.controller_name_filter: str = ""  # Optional filter by controller name
        
    def get_serializable(self) -> dict:
        """Get a serializable representation of the trigger."""
        d = {
            "controller_button": self.controller_button.name if self.controller_button else None,
            "controller_axis": self.controller_axis.name if self.controller_axis else None,
            "axis_threshold": self.axis_threshold,
            "controller_name_filter": self.controller_name_filter,
        }
        return d
    
    def load_from_serialized(self, data: dict):
        """Load trigger settings from serialized data."""
        if data.get("controller_button"):
            self.controller_button = ControllerButton[data["controller_button"]]
        if data.get("controller_axis"):
            self.controller_axis = ControllerAxis[data["controller_axis"]]
        self.axis_threshold = data.get("axis_threshold", 16384)
        self.controller_name_filter = data.get("controller_name_filter", "")
        
        # Add controller trigger mode if set
        if (self.controller_button or self.controller_axis) and TriggerMode.CONTROLLER not in self.modes:
            self.modes.append(TriggerMode.CONTROLLER)
    
    def set_controller_trigger(self, button: typing.Optional[ControllerButton] = None,
                               axis: typing.Optional[ControllerAxis] = None,
                               threshold: int = 16384,
                               controller_name: str = ""):
        """
        Set up a controller trigger.
        
        Args:
            button: The controller button to trigger on
            axis: The controller axis to trigger on (alternative to button)
            threshold: Threshold for axis triggers (0-32767)
            controller_name: Optional filter for specific controller name
        """
        self.controller_button = button
        self.controller_axis = axis
        self.axis_threshold = threshold
        self.controller_name_filter = controller_name
        
        if button or axis:
            if TriggerMode.CONTROLLER not in self.modes:
                self.modes.append(TriggerMode.CONTROLLER)
        
    def unset_controller_trigger(self):
        """Remove the controller trigger."""
        self.controller_button = None
        self.controller_axis = None
        if TriggerMode.CONTROLLER in self.modes:
            self.modes.remove(TriggerMode.CONTROLLER)
    
    def check_controller_trigger(self, button: typing.Optional[ControllerButton],
                                 axis: typing.Optional[ControllerAxis],
                                 axis_value: int,
                                 controller_name: str,
                                 window_title: typing.Tuple[str, str]) -> bool:
        """
        Check if this trigger matches the given controller input.
        
        Args:
            button: The button that was pressed (if any)
            axis: The axis that moved (if any)
            axis_value: The current axis value
            controller_name: Name of the controller that generated the input
            window_title: Window title tuple (title, class) for filtering
            
        Returns:
            True if the trigger matches and should fire
        """
        if not self._should_trigger_window_title(window_title):
            return False
            
        # Check controller name filter if set
        if self.controller_name_filter and self.controller_name_filter not in controller_name:
            return False
            
        # Check button match
        if self.controller_button and button == self.controller_button:
            return True
            
        # Check axis match (trigger when axis exceeds threshold)
        if self.controller_axis and axis == self.controller_axis:
            return abs(axis_value) >= self.axis_threshold
            
        return False
    
    def get_controller_trigger_string(self) -> str:
        """Get a human-readable string describing the trigger."""
        if TriggerMode.CONTROLLER not in self.modes:
            return ""
            
        parts = []
        
        if self.controller_button:
            parts.append(f"Button: {self.controller_button.name}")
            
        if self.controller_axis:
            parts.append(f"Axis: {self.controller_axis.name} (> {self.axis_threshold})")
            
        if self.controller_name_filter:
            parts.append(f"Controller: {self.controller_name_filter}")
            
        return ", ".join(parts) if parts else ""
