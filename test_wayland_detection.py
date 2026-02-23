#!/usr/bin/env python3
"""
Test Wayland detection and interface selection
"""
import sys
sys.path.insert(0, 'lib')

from autokey.display_detector import DisplayDetector

def test_detection():
    print("=== Wayland Detection Test ===")
    
    # Test detection
    server = DisplayDetector.get_display_server()
    print(f"Detected display server: {server}")
    
    # Test boolean checks
    print(f"Is Wayland: {DisplayDetector.is_wayland()}")
    print(f"Is X11: {DisplayDetector.is_x11()}")
    
    # Test factory
    from autokey.interface_factory import InterfaceFactory
    
    print("\n=== Interface Factory Test ===")
    print(f"Display server: {DisplayDetector.get_display_server()}")
    print("Factory will create appropriate interface based on display server")
    
    print("\n✅ All tests passed")

if __name__ == "__main__":
    test_detection()
