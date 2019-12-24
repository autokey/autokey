# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2019 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import dbus.service

logger = __import__("autokey.logger").logger.get_logger(__name__)


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
