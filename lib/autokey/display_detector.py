"""
Display server detector for Wayland/X11 compatibility
"""
import os
import logging

logger = __import__("autokey.logger").logger.get_logger(__name__)

class DisplayDetector:
    """Detect whether running on X11 or Wayland"""
    
    @staticmethod
    def get_display_server():
        """
        Detect the current display server type
        Returns: 'wayland', 'x11', or 'unknown'
        """
        # Check WAYLAND_DISPLAY environment variable
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        if wayland_display:
            logger.info(f"Wayland detected: {wayland_display}")
            return 'wayland'
        
        # Check XDG_SESSION_TYPE
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type == 'wayland':
            logger.info("Wayland detected via XDG_SESSION_TYPE")
            return 'wayland'
        elif session_type == 'x11':
            logger.info("X11 detected via XDG_SESSION_TYPE")
            return 'x11'
        
        # Check DISPLAY environment variable for X11
        display = os.environ.get('DISPLAY')
        if display:
            logger.info(f"X11 detected: {display}")
            return 'x11'
        
        logger.warning("Could not detect display server type")
        return 'unknown'
    
    @staticmethod
    def is_wayland():
        """Check if running on Wayland"""
        return DisplayDetector.get_display_server() == 'wayland'
    
    @staticmethod
    def is_x11():
        """Check if running on X11"""
        return DisplayDetector.get_display_server() == 'x11'
