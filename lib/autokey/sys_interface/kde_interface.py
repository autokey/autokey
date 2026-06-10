import dbus
import dbus.service
import time
import threading
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from autokey.sys_interface.abstract_interface import AbstractWindowInterface, WindowInfo

logger = __import__("autokey.logger").logger.get_logger(__name__)

class AutoKeyKDEListener(dbus.service.Object):
    """
    A temporary D-Bus server hosted by AutoKey to receive the window data
    pushed by the KWin script.
    """
    def __init__(self, bus):
        self.bus_name = dbus.service.BusName("org.autokey.WaylandBridge", bus=bus)
        super().__init__(self.bus_name, "/WindowData")
        self.current_title = ""
        self.current_class = ""
        self.data_ready = threading.Event()

    @dbus.service.method("org.autokey.WaylandBridge", in_signature="ss")
    def PushWindowInfo(self, title, wm_class):
        self.current_title = str(title)
        self.current_class = str(wm_class)
        self.data_ready.set()

class KDEWaylandInterface(AbstractWindowInterface):
    """
    Implementation of AbstractWindowInterface for KDE Plasma on Wayland
    using a two-way KWin D-Bus scripting bridge.
    """
    def __init__(self):
        # Initialize the D-Bus loop required for our listener to receive signals
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        
        # Setup the Python-side listener
        self.listener = AutoKeyKDEListener(self.bus)
        
        # Start GLib loop in a background thread to process incoming D-Bus calls
        self.loop = GLib.MainLoop()
        self.thread = threading.Thread(target=self.loop.run, daemon=True)
        self.thread.start()

        # Connect to the KWin scripting interface
        self.kwin_scripting = self.bus.get_object("org.kde.KWin", "/Scripting")
        self.interface = dbus.Interface(self.kwin_scripting, "org.kde.kwin.Scripting")

    def _query_kwin(self):
        """
        Injects a KWin script that reads the active window and immediately
        pushes the data back to our AutoKeyKDEListener via D-Bus.
        """
        self.listener.data_ready.clear()
        
        script_code = """
        var win = workspace.activeWindow;
        var title = win ? win.caption : "";
        var wmClass = win ? win.resourceClass : "";
        
        // Push data back to Python over D-Bus
        callDBus("org.autokey.WaylandBridge", "/WindowData", "org.autokey.WaylandBridge", "PushWindowInfo", title, wmClass);
        """
        
        try:
            # 1. Load the script
            script_path = self.interface.loadScript("autokey_spy", script_code)
            script_obj = self.bus.get_object("org.kde.KWin", script_path)
            script_interface = dbus.Interface(script_obj, "org.kde.kwin.Script")
            
            # 2. Run the script
            script_interface.run()
            
            # 3. Wait for the callback from KWin (timeout after 0.5s to prevent UI hangs)
            self.listener.data_ready.wait(timeout=0.5)
            
            # 4. Unload to keep the user's KDE session clean
            script_interface.stop()
            
        except Exception as e:
            logger.error(f"KDE Wayland D-Bus Error: {e}")

    def get_window_info(self, window=None, traverse: bool=True) -> WindowInfo:
        self._query_kwin()
        return WindowInfo(wm_title=self.listener.current_title, wm_class=self.listener.current_class)

    def get_window_title(self, window=None, traverse=True) -> str:
        self._query_kwin()
        return self.listener.current_title

    def get_window_class(self, window=None, traverse=True) -> str:
        self._query_kwin()
        return self.listener.current_class

    def get_window_list(self):
        return []