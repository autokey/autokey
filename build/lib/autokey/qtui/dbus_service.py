# Copyright (C) 2018 Thomas Hess
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import Q_CLASSINFO, pyqtSlot
from PyQt5.QtDBus import QDBusAbstractAdaptor, QDBusConnection


class AppService(QDBusAbstractAdaptor):

    Q_CLASSINFO("D-Bus Interface", 'org.autokey.Service')

    Q_CLASSINFO(
        "D-Bus Introspection",
        '  <interface name="org.autokey.Service">\n'
        '    <method name="show_configure"/>\n'
        '    <method name="run_script">\n'
        '      <arg type="s" name="name" direction="in"/>\n'
        '    </method>\n'
        '    <method name="run_phrase">\n'
        '      <arg type="s" name="name" direction="in"/>\n'
        '    </method>\n'
        '    <method name="run_folder">\n'
        '      <arg type="s" name="name" direction="in"/>\n'
        '    </method>\n'
        '  </interface>\n'
    )

    def __init__(self, parent):
        super(AppService, self).__init__(parent)
        self.connection = QDBusConnection.sessionBus()
        path = '/AppService'
        service = 'org.autokey.Service'
        self.connection.registerObject(path, parent)
        self.connection.registerService(service)
        self.setAutoRelaySignals(True)

    @pyqtSlot()
    def show_configure(self):
        self.parent().show_configure()

    @pyqtSlot(str)
    def run_script(self, name):
        self.parent().service.run_script(name)

    @pyqtSlot(str)
    def run_phrase(self, name):
        self.parent().service.run_phrase(name)

    @pyqtSlot(str)
    def run_folder(self, name):
        self.parent().service.run_folder(name)

