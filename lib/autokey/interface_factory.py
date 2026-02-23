"""
Interface factory for creating appropriate system interface based on display server
"""
import logging
from autokey.display_detector import DisplayDetector

logger = __import__("autokey.logger").logger.get_logger(__name__)

class InterfaceFactory:
    """Factory for creating display-server-appropriate interfaces"""
    
    @staticmethod
    def create_interface(iomediator):
        """
        Create the appropriate interface based on display server type
        
        Args:
            iomediator: The IoMediator instance
            
        Returns:
            Interface instance (X11 or Wayland-compatible)
        """
        display_server = DisplayDetector.get_display_server()
        
        if display_server == 'wayland':
            logger.info("Creating Wayland-compatible interface (uinput)")
            try:
                from autokey.uinput_interface import UInputInterface
                return UInputInterface(iomediator)
            except Exception as e:
                logger.error(f"Failed to create uinput interface: {e}")
                logger.warning("Falling back to X11 interface")
                from autokey.interface import XRecordInterface
                return XRecordInterface(iomediator)
        else:
            logger.info("Creating X11 interface")
            from autokey.interface import XRecordInterface
            return XRecordInterface(iomediator)
    
    @staticmethod
    def create_window_interface():
        """Create window interface based on display server"""
        display_server = DisplayDetector.get_display_server()
        
        if display_server == 'wayland':
            logger.info("Creating Wayland window interface (GNOME extension)")
            try:
                from autokey.gnome_interface import GnomeExtensionWindowInterface
                return GnomeExtensionWindowInterface()
            except Exception as e:
                logger.error(f"Failed to create GNOME window interface: {e}")
                logger.warning("Window info will be limited on Wayland without GNOME extension")
                return None
        else:
            logger.info("Creating X11 window interface")
            from autokey.interface import X11WindowInterface
            return X11WindowInterface()
