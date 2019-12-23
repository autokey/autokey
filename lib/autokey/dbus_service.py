import dbus.service

from autokey.logger import get_logger

logger = get_logger(__name__)
del get_logger


class AppService(dbus.service.Object):
    """
    This class is used by the GTK GUI and provides the DBus interface.
    It can be used by external programs to communicate with the autokey process.
    """
    def __init__(self, app):
        busName = dbus.service.BusName('org.autokey.Service', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, "/AppService")
        self.app = app
        logger.debug("Created DBus service")

    @dbus.service.method(dbus_interface='org.autokey.Service', in_signature='', out_signature='')
    def show_configure(self):
        self.app.show_configure()

    @dbus.service.method(dbus_interface='org.autokey.Service', in_signature='s', out_signature='')
    def run_script(self, name):
        self.app.service.run_script(name)

    @dbus.service.method(dbus_interface='org.autokey.Service', in_signature='s', out_signature='')
    def run_phrase(self, name):
        self.app.service.run_phrase(name)

    @dbus.service.method(dbus_interface='org.autokey.Service', in_signature='s', out_signature='')
    def run_folder(self, name):
        self.app.service.run_folder(name)
