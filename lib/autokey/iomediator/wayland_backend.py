# Copyright (C) 2026 AutoKey Contributors
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Wayland Backend for AutoKey

This module provides a Wayland-compatible implementation of keyboard input
and monitoring using xdg-desktop-portal, libinput, and D-Bus APIs.

Note: Due to Wayland's security model, some features may be limited compared
to X11. Key limitations include:
- No global key monitoring without compositor support
- Keyboard injection requires accessibility permissions
- Clipboard access may require user confirmation
"""

import os
import subprocess
import threading
import time
from typing import Optional, Callable, List, Tuple

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import GLib
    HAS_GLIB = True
except ImportError:
    HAS_GLIB = False

logger = __import__("autokey.logger").logger.get_logger(__name__)


class DisplayServerDetector:
    """Detects whether we're running on Wayland or X11"""
    
    @staticmethod
    def get_display_server() -> str:
        """Returns 'wayland' or 'x11' or 'unknown'"""
        display = os.environ.get('DISPLAY', '')
        wayland = os.environ.get('WAYLAND_DISPLAY', '')
        
        if wayland:
            return 'wayland'
        elif 'x11' in display.lower() or 'unix' in display:
            return 'x11'
        
        # Fallback: check GNOME session
        try:
            output = subprocess.check_output(['echo', '$XDG_SESSION_TYPE'], shell=True).decode()
            if 'wayland' in output.lower():
                return 'wayland'
        except:
            pass
        
        return 'x11'  # Default fallback
    
    @staticmethod
    def is_wayland() -> bool:
        return DisplayServerDetector.get_display_server() == 'wayland'


class WaylandInputBackend:
    """
    Wayland-compatible keyboard input backend
    
    Uses xdg-desktop-portal for accessibility-based keyboard injection.
    This requires the application to have accessibility permissions enabled
    in the desktop environment.
    """
    
    def __init__(self):
        self.is_available = False
        self.portal_available = False
        self.libinput_available = False
        
        self._check_dependencies()
        
        if self.is_available:
            logger.info("Wayland input backend initialized successfully")
        else:
            logger.warning("Wayland input backend not available - will fall back to XWayland")
    
    def _check_dependencies(self):
        """Check if required Wayland tools are available"""
        
        # Check for xdg-desktop-portal
        try:
            result = subprocess.run(
                ['which', 'xdg-desktop-portal'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.portal_available = result.returncode == 0
        except Exception as e:
            logger.debug(f"Failed to check xdg-desktop-portal: {e}")
        
        # Check for libinput
        try:
            result = subprocess.run(
                ['which', 'libinput'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.libinput_available = result.returncode == 0
        except Exception as e:
            logger.debug(f"Failed to check libinput: {e}")
        
        # Check for at-spi (accessibility API)
        try:
            import pyatspi
            self.has_atspi = True
        except ImportError:
            self.has_atspi = False
        
        # Wayland is available if we have at least one method
        self.is_available = (
            self.portal_available or 
            self.libinput_available or 
            self.has_atspi
        )
    
    def send_keys(self, key_string: str) -> bool:
        """
        Send a string of keys using Wayland-compatible methods
        
        Priority order:
        1. AT-SPI (if available and accessible)
        2. xdg-desktop-portal
        3. libinput fallback
        """
        if not self.is_available:
            logger.error("Wayland input backend not available")
            return False
        
        # Try AT-SPI first (most reliable for accessibility)
        if self.has_atspi:
            try:
                return self._send_via_atspi(key_string)
            except Exception as e:
                logger.warning(f"AT-SPI failed: {e}, trying alternative")
        
        # Try xdg-desktop-portal
        if self.portal_available:
            try:
                return self._send_via_portal(key_string)
            except Exception as e:
                logger.warning(f"xdg-desktop-portal failed: {e}")
        
        # Last resort: try libinput
        if self.libinput_available:
            try:
                return self._send_via_libinput(key_string)
            except Exception as e:
                logger.error(f"All Wayland methods failed: {e}")
                return False
        
        return False
    
    def _send_via_atspi(self, key_string: str) -> bool:
        """Send keys via AT-SPI accessibility API"""
        import pyatspi
        
        # Use ATK to simulate keyboard events
        root = pyatspi.Registry.get_default_root()
        if not root:
            raise RuntimeError("Could not get AT-SPI root object")
        
        # For now, we'll use a simple approach: type character by character
        # A more sophisticated implementation would parse special keys
        for char in key_string:
            if char == '<enter>' or char == '\\n':
                # Simulate Enter key
                self._press_and_release(pyatspi.KEY_Return)
            elif char == '<tab>':
                self._press_and_release(pyatspi.KEY_Tab)
            elif char.startswith('<') and char.endswith('>'):
                # Special key
                key_name = char[1:-1].lower()
                keycode = self._keyname_to_keycode(key_name)
                if keycode:
                    self._press_and_release(keycode)
            else:
                # Regular character
                self._type_character(char)
        
        return True
    
    def _press_and_release(self, keycode: int):
        """Press and release a key code"""
        # This is a simplified implementation
        # In reality, you'd need to use GKeyboardDevice or similar
        logger.debug(f"Simulating key press/release for keycode {keycode}")
        # TODO: Implement proper key event using appropriate Wayland mechanism
    
    def _type_character(self, char: str):
        """Type a single character"""
        logger.debug(f"Typing character: {repr(char)}")
        # TODO: Use appropriate API to type character
    
    def _keyname_to_keycode(self, key_name: str) -> Optional[int]:
        """Convert key name to keycode"""
        # Simplified mapping - real implementation would need full keysym table
        key_mappings = {
            'enter': 36,
            'tab': 23,
            'escape': 1,
            'backspace': 22,
            'delete': 119,
            'up': 110,
            'down': 111,
            'left': 113,
            'right': 114,
        }
        return key_mappings.get(key_name)
    
    def _send_via_portal(self, key_string: str) -> bool:
        """Send keys via xdg-desktop-portal (future implementation)"""
        # This would require implementing D-Bus calls to the portal
        # For now, just log that it's not implemented
        raise NotImplementedError("xdg-desktop-portal keyboard injection not yet implemented")
    
    def _send_via_libinput(self, key_string: str) -> bool:
        """Send keys via libinput (requires elevated privileges)"""
        # This would require opening /dev/input/event* devices
        # and sending EV_KEY events - typically needs root/admin
        raise NotImplementedError("libinput keyboard injection requires privileged access")


class WaylandEventMonitor:
    """
    Monitor keyboard and mouse events on Wayland
    
    Limitations:
    - Cannot monitor all keys globally without special permissions
    - Can only monitor events from specific applications
    - Relies on accessibility APIs which have restricted scope
    """
    
    def __init__(self, callback: Callable[[str, List[str], dict], None]):
        """
        Args:
            callback: Function(key_name, modifiers, window_info) called on keypress
        """
        self.callback = callback
        self.running = False
        self.thread = None
        
        self.atspi_available = False
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check AT-SPI availability"""
        try:
            import pyatspi
            self.atspi_available = True
            logger.info("AT-SPI event monitoring available")
        except ImportError:
            self.atspi_available = False
            logger.warning("AT-SPI not available - event monitoring disabled")
    
    def start(self):
        """Start monitoring events"""
        if not self.atspi_available:
            logger.warning("Cannot start event monitor - dependencies not available")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._event_loop, daemon=True)
        self.thread.start()
        logger.info("Wayland event monitor started")
        return True
    
    def stop(self):
        """Stop monitoring events"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Wayland event monitor stopped")
    
    def _event_loop(self):
        """Main event loop for monitoring"""
        # This is a placeholder - actual implementation would need to hook into
        # AT-SPI or compositor-specific event systems
        while self.running:
            time.sleep(0.1)
            # In a real implementation, we'd poll for events here
            pass


class XWaylandFallback:
    """
    Fallback strategy: run AutoKey in XWayland mode
    
    When native Wayland support is insufficient, fall back to running
    AutoKey inside an XWayland compatibility layer.
    """
    
    @staticmethod
    def is_xwayland_available() -> bool:
        """Check if XWayland is running"""
        try:
            result = subprocess.run(
                ['ps', '-ef'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return 'Xwayland' in result.stdout
        except:
            return False
    
    @staticmethod
    def suggest_compatibility_mode() -> bool:
        """Suggest switching to X11/Xorg session"""
        logger.info("For best AutoKey compatibility, consider using X11/Xorg session")
        logger.info("You can select 'Ubuntu on Xorg' or similar from the login screen")
        return True


class WaylandCompatibilityManager:
    """
    Main interface for Wayland compatibility
    
    Decides which backend to use based on system capabilities.
    """
    
    def __init__(self):
        self.display_server = DisplayServerDetector.get_display_server()
        self.input_backend = None
        self.event_monitor = None
        
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize appropriate backend based on display server"""
        if self.display_server == 'wayland':
            logger.info("Detected Wayland session")
            
            # Initialize Wayland-native backend
            self.input_backend = WaylandInputBackend()
            
            # Set up event monitor (will be non-functional without AT-SPI)
            self.event_monitor = WaylandEventMonitor(self._handle_keypress)
            
            # Check if we should suggest fallback
            if not self.input_backend.is_available:
                logger.warning("Native Wayland support unavailable")
                
                if XWaylandFallback.is_xwayland_available():
                    logger.info("XWayland detected - running in compatibility mode")
                else:
                    XWaylandFallback.suggest_compatibility_mode()
        else:
            logger.info("Detected X11 session - using native backend")
    
    def _handle_keypress(self, key_name: str, modifiers: List[str], window_info: dict):
        """Handle incoming keypress event"""
        if self.callback:
            self.callback(key_name, modifiers, window_info)
    
    def send_keys(self, key_string: str):
        """Public method to send keys"""
        if self.input_backend:
            return self.input_backend.send_keys(key_string)
        return False
    
    def start_event_monitor(self):
        """Start monitoring for keyboard events"""
        if self.event_monitor:
            return self.event_monitor.start()
        return False
    
    def stop_event_monitor(self):
        """Stop monitoring events"""
        if self.event_monitor:
            self.event_monitor.stop()


# Global instance for use by other modules
compatibility_manager = None


def initialize_wayland_support():
    """Initialize Wayland compatibility manager (call once at startup)"""
    global compatibility_manager
    compatibility_manager = WaylandCompatibilityManager()
    return compatibility_manager


def get_compat_manager():
    """Get the global compatibility manager instance"""
    return compatibility_manager
