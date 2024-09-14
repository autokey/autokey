
import dbus
import json
from dbus.mainloop.glib import DBusGMainLoop


from autokey.sys_interface.abstract_interface import AbstractSysInterface, AbstractMouseInterface, AbstractWindowInterface, WindowInfo

logger = __import__("autokey.logger").logger.get_logger(__name__)

class DBusInterface:
    def __init__(self):
        mainloop= DBusGMainLoop()
        session_bus = dbus.SessionBus(mainloop=mainloop)
        shell_obj = session_bus.get_object('org.gnome.Shell', '/org/gnome/Shell/Extensions/AutoKey')
        self.dbus_interface = dbus.Interface(shell_obj, 'org.gnome.Shell.Extensions.AutoKey')

        version = self.dbus_interface.CheckVersion()
        logger.debug("AutoKey Gnome Extension version: %s" % version)
        if version == "0.1":
            pass
        else:
            raise Exception("Incompatible version of AutoKey Gnome Extension")



class GnomeMouseReadInterface(DBusInterface):
    def __init__(self):
        super().__init__()

    def mouse_location(self):
        [x, y] = self.dbus_interface.GetMouseLocation()
        return [int(x), int(y)]

class GnomeExtensionWindowInterface(DBusInterface, AbstractWindowInterface):
    def __init__(self):
        super().__init__()

    def get_window_list(self):
        return self._dbus_window_list()

    def get_screen_size(self):
        x,y = self.dbus_interface.ScreenSize()
        return [int(x), int(y)]

    def get_window_info(self, window=None, traverse: bool=True) -> WindowInfo:
        """
        Returns a WindowInfo object containing the class and title.
        """
        window = self._active_window()
        return WindowInfo(wm_class=window['wm_class'], wm_title=window['wm_title'])

    def get_window_class(self, window=None, traverse=True) -> str:
        """
        Returns the window class of the currently focused window.
        """
        return self._active_window()['wm_class']
        
    
    def get_window_title(self, window=None, traverse=True) -> str:
        """
        Returns the active window title
        """
        return self._active_window()['wm_title']
    
    def close_window(self, window_id):
        self._dbus_close_window(window_id)

    def activate_window(self, window_id):
        self._dbus_activate_window(window_id)

    def _active_window(self):
        #TODO probably can be done more efficiently with an additional dbus method in the gnome extension
        window_list = self._dbus_window_list()
        for window in window_list:
            if window['focus']:
                return window
        # TODO seeing this a lot when I use a script to call `gnome-screenshot -a`, suspect it's just related to that focus behaves differently when that app runs?
        logger.error("Unable to determine the active window")
        return None
            
    def _dbus_window_list(self):
        #TODO consider how/if error handling can be implemented
        try:
            return json.loads(self.dbus_interface.List())
        except dbus.exceptions.DBusException as e:
            self.__init__() #reconnect to dbus
            return json.loads(self.dbus_interface.List())
            
    def _dbus_close_window(self, window_id):
        #TODO consider how/if error handling can be implemented
        try:
            self.dbus_interface.Close(window_id)
        except dbus.exceptions.DBusException as e:
            self.__init__()
            self.dbus_interface.Close(window_id)

    def _dbus_activate_window(self, window_id):
        try:
            self.dbus_interface.Activate(window_id)
        except dbus.exceptions.DBusException as e:  
            self.__init__()
            self.dbus_interface.Activate(window_id)

    def _dbus_move_window(self, window_id, x, y):
        try:
            self.dbus_interface.Move(window_id, x, y)
        except dbus.exceptions.DBusException as e:
            self.__init__()
            self.dbus_interface.Move(window_id, x, y)

    def _dbus_resize_window(self, window_id, width, height):
        try:
            self.dbus_interface.Resize(window_id, width, height)
        except dbus.exceptions.DBusException as e:
            self.__init__()
            self.dbus_interface.Resize(window_id, width, height)