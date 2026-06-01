import threading
import queue
import time
import typing
import subprocess
try:
    import evdev
except ImportError:
    evdev = None

logger = __import__("autokey.logger").logger.get_logger(__name__)

class EvdevInterface(threading.Thread):
    """
    Wayland-compatible Evdev interface for AutoKey.
    Uses /dev/input/event* for key grabbing and /dev/uinput for synthetic keystrokes.
    """
    def __init__(self, mediator, app):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("EvdevInterface-thread")
        self.mediator = mediator
        self.app = app
        self.queue = queue.Queue()
        self.shutdown_flag = False
        self.hotkeys = {}
        
        # Initialize UInput device for synthetic events
        if evdev:
            try:
                self.ui = evdev.UInput()
            except Exception as e:
                logger.error(f"Failed to initialize UInput: {e}")
                self.ui = None
        else:
            self.ui = None
            logger.error("evdev module is not installed")
        
        self.eventThread = threading.Thread(target=self.__eventLoop)
        self.eventThread.start()
        
    def __eventLoop(self):
        while not self.shutdown_flag:
            try:
                method, args = self.queue.get(timeout=1.0)
                if method is None:
                    break
                method(*args)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.exception("Error in Evdev event loop")
                
    def __enqueue(self, method: typing.Callable, *args):
        self.queue.put_nowait((method, args))
        
    def shutdown(self):
        self.shutdown_flag = True
        self.__enqueue(None)
        
    # Window Information
    def get_window_title(self):
        return self._get_wayland_window_property("title")

    def get_window_class(self):
        return self._get_wayland_window_property("class")
        
    def _get_wayland_window_property(self, prop):
        # GNOME-specific Wayland window detection using dbus (Window Calls extension)
        # This is a fallback strategy for GNOME Wayland as standard Wayland lacks active window querying
        cmd = [
            "gdbus", "call", "--session",
            "--dest", "org.gnome.Shell",
            "--object-path", "/org/gnome/Shell/Extensions/Windows",
            "--method", "org.gnome.Shell.Extensions.Windows.List"
        ]
        try:
            output = subprocess.check_output(cmd, universal_newlines=True, stderr=subprocess.DEVNULL)
            import json
            # Parse the DBus variant string into JSON - this is a simplification
            # Actual parsing requires stripping the DBus type signatures like "( '[{...}]', )"
            start = output.find("[")
            end = output.rfind("]") + 1
            if start != -1 and end != 0:
                json_str = output[start:end]
                windows = json.loads(json_str)
                for w in windows:
                    if w.get("focus", False):
                        return w.get("wm_class", "") if prop == "class" else w.get("title", "")
        except Exception as e:
            logger.debug(f"Wayland window property fetch failed: {e}")
        return ""

    # Hotkey Management
    def grab_hotkey(self, item):
        self.__enqueue(self.__grab_hotkey, item)
        
    def __grab_hotkey(self, item):
        logger.debug(f"Evdev grabbing hotkey: {item}")
        # Evdev implementation would register the hook here
        
    def ungrab_hotkey(self, item):
        self.__enqueue(self.__ungrab_hotkey, item)
        
    def __ungrab_hotkey(self, item):
        logger.debug(f"Evdev ungrabbing hotkey: {item}")
        
    # Output Simulation
    def send_string(self, string):
        self.__enqueue(self.__send_string, string)
        
    def __send_string(self, string):
        logger.debug(f"Evdev sending string: {string}")
        if self.ui:
            # Basic character to keycode mapping would be done here
            pass
            
    def send_key(self, keyName):
        self.__enqueue(self.__send_key, keyName)
        
    def __send_key(self, keyName):
        logger.debug(f"Evdev sending key: {keyName}")
        if self.ui:
            pass
            
    def fake_keypress(self, keycode, modifiers=None):
        self.__enqueue(self.__fake_keypress, keycode, modifiers)
        
    def __fake_keypress(self, keycode, modifiers):
        if self.ui:
            # evdev uses e.g. evdev.ecodes.KEY_A
            pass
            
    def flush_events(self):
        pass
        
    def cancel(self):
        self.shutdown()
