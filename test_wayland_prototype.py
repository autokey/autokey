#!/usr/bin/env python3
"""
AutoKey Wayland Support - Prototype Demo

This script demonstrates the basic structure of how AutoKey could support
Wayland, using accessibility APIs and D-Bus portals.

To test this prototype:
1. Ensure you're on a Wayland session (check with `echo $XDG_SESSION_TYPE`)
2. Install dependencies: pip install pyatspi gi
3. Enable Accessibility in your desktop environment settings
4. Run: python3 test_wayland_prototype.py
"""

import os
import sys
import time
import threading


def check_system():
    """Check if we're running on Wayland and what tools are available"""
    
    print("=" * 60)
    print("AutoKey Wayland Support - System Check")
    print("=" * 60)
    
    # Check display server
    display = os.environ.get('DISPLAY', '')
    wayland = os.environ.get('WAYLAND_DISPLAY', '')
    
    print(f"\n📌 Display Server Detection:")
    print(f"   DISPLAY env var: {display or '(not set)'}")
    print(f"   WAYLAND_DISPLAY env var: {wayland or '(not set)'}")
    
    if wayland:
        print(f"   ✅ Detected: Wayland")
        is_wayland = True
    elif 'x11' in display.lower() or 'unix' in display:
        print(f"   ✅ Detected: X11")
        is_wayland = False
    else:
        try:
            result = subprocess.run(
                ['echo', '$XDG_SESSION_TYPE'], shell=True,
                capture_output=True, text=True
            )
            session_type = result.stdout.strip().lower()
            print(f"   Fallback check: {session_type}")
            is_wayland = 'wayland' in session_type
        except Exception as e:
            print(f"   ⚠️  Could not determine: {e}")
            is_wayland = False
    
    # Check for AT-SPI
    print(f"\n🔧 Dependency Checks:")
    try:
        import gi
        gi.require_version('Atspi', '2.0')
        import pyatspi
        print(f"   ✅ AT-SPI (pyatspi): Available")
        has_atspi = True
    except ImportError as e:
        print(f"   ❌ AT-SPI (pyatspi): Not installed ({e})")
        has_atspi = False
    except ValueError as e:
        print(f"   ❌ AT-SPI (pyatspi): Version conflict ({e})")
        has_atspi = False
    
    # Check xdg-desktop-portal
    print(f"\n🚪 Portal Services:")
    try:
        result = subprocess.run(['which', 'xdg-desktop-portal'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ xdg-desktop-portal: Available at {result.stdout.strip()}")
            
            # Check which portal implementations are running
            result = subprocess.run(['pgrep', '-l', 'xdg-desktop-portal'],
                                  capture_output=True, text=True)
            if result.stdout:
                print(f"   Running instances:")
                for line in result.stdout.strip().split('\n'):
                    print(f"      • {line}")
        else:
            print(f"   ❌ xdg-desktop-portal: Not found")
    except Exception as e:
        print(f"   ⚠️  Could not check: {e}")
    
    # Check Accessibility settings
    print(f"\n♿ Accessibility:")
    print(f"   Note: Wayland keyboard injection typically requires")
    print(f"   Accessibility permissions to be enabled in system settings.")
    print(f"   In GNOME: Settings → Privacy → Accessibility")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    if is_wayland:
        print("✅ Running on Wayland")
        
        if has_atspi:
            print("✅ AT-SPI available - partial Wayland support possible!")
            print("   Basic keyboard injection may work with accessibility enabled")
        else:
            print("❌ AT-SPI not available")
            print("   Install with: pip3 install pyatspi")
        
        print("\nRecommendation:")
        print("-" * 60)
        print("For full Wayland support in AutoKey:")
        print("  1. Enable Accessibility features in your desktop environment")
        print("  2. Grant AutoKey permission to 'control another screen'")
        print("  3. Or switch to X11/Xorg session for complete functionality")
        
    else:
        print("✅ Running on X11 - current AutoKey implementation will work")
        print("   No changes needed")
    
    print("=" * 60)
    
    return is_wayland, has_atspi


def demonstrate_accessibility_usage(has_atspi):
    """Demonstrate how AT-SPI can be used for keyboard injection"""
    
    if not has_atspi:
        print("\n⚠️  Cannot demonstrate - AT-SPI not available")
        return
    
    print("\n" + "=" * 60)
    print("AT-SPI Keyboard Injection Demo")
    print("=" * 60)
    
    try:
        import pyatspi
        
        print("\nStep 1: Getting access to AT-SPI registry...")
        registry = pyatspi.Registry()
        print("   ✅ Successfully connected to AT-SPI")
        
        print("\nStep 2: Checking registered keystroke listeners...")
        # This is just informational - we won't actually register one
        print(f"   Info: AT-SPI can listen for global keystrokes via registry")
        print(f"   Methods: registry.registerKeystrokeListener(), deregister...")
        
        print("\nStep 3: Querying accessible applications...")
        apps = registry.getAppRegistry()
        if apps:
            n_apps = len(list(apps))
            print(f"   Found {n_apps} accessible applications")
        
        print("\nStep 4: Demonstrating potential keystroke simulation...")
        print("   Note: Actual key injection via AT-SPI requires more code.")
        print("   The API provides ATK interfaces for simulating events.")
        
        # Show example code
        print("\nExample implementation would look like:")
        print("-" * 60)
        print("""
from autokey.iomediator.wayland_backend import WaylandInputBackend

backend = WaylandInputBackend()

# Send simple text
backend.send_keys("Hello, Wayland!")

# Send special keys  
backend.send_keys("<ctrl>+<c>")  # Ctrl+C
backend.send_keys("<enter>")     # Enter key
""")
        
        print("\n✅ Demonstration complete!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)


def main():
    """Main function"""
    
    print("\n🦞 AutoKey Wayland Support - Prototype Tool 🦞\n")
    
    # Check system capabilities
    is_wayland, has_atspi = check_system()
    
    # If we're on Wayland and have AT-SPI, show demo
    if is_wayland and has_atspi:
        input("\nPress Enter to see AT-SPI demonstration...\n")
        demonstrate_accessibility_usage(has_atspi)
    
    print("\n🎯 Next Steps:\n")
    print("To implement Wayland support for AutoKey:")
    print("  1. Create IOMediator subclass that uses WaylandInputBackend")
    print("  2. Add configuration option to select backend")
    print("  3. Test keyboard injection on your specific compositor")
    print("  4. Document limitations clearly")
    print("\nSee lib/autokey/iomediator/wayland_backend.py for implementation")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    import subprocess
    
    # Change to the autokey source directory
    if os.path.exists('/tmp/autokey-wayland/lib/autokey'):
        os.chdir('/tmp/autokey-wayland')
        print(f"Working in: {os.getcwd()}\n")
    
    main()
