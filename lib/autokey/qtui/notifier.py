# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
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


from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QSystemTrayIcon, QIcon, QAction

from . import popupmenu
from .. import configmanager as cm

TOOLTIP_RUNNING = "AutoKey - running"
TOOLTIP_PAUSED = "AutoKey - paused"


class Notifier:
    
    def __init__(self, app):
        self.action_enable_monitoring = None  # type: QAction
        self.app = app
        self.configManager = app.configManager
        
        self.icon = QSystemTrayIcon(QIcon.fromTheme(cm.ConfigManager.SETTINGS[cm.NOTIFICATION_ICON]))
        # TODO: New style connect()
        self.icon.connect(self.icon, SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.on_activate)

        self.build_menu()

        if cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]:
            self.update_tool_tip()
            self.icon.show()
                        
    def update_tool_tip(self):
        if cm.ConfigManager.SETTINGS[cm.SERVICE_RUNNING]:
            self.icon.setToolTip(TOOLTIP_RUNNING)
            self.action_enable_monitoring.setChecked(True)
        else:
            self.icon.setToolTip(TOOLTIP_PAUSED)
            self.action_enable_monitoring.setChecked(False)
            
    def build_menu(self):
        if cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]:
            # Get phrase folders to add to main menu

            folders = [folder for folder in self.configManager.allFolders if folder.showInTrayMenu]
            items = [item for item in self.configManager.allItems if item.showInTrayMenu]
                    
            # Construct main menu
            menu = popupmenu.PopupMenu(self.app.service, folders, items, False, "AutoKey")

            if items:
                menu.addSeparator()

            # TODO: maybe import this from configwindow.py ? The exact same thing is defined in the main window.
            self.action_enable_monitoring = QAction("&Enable Monitoring", menu)
            self.action_enable_monitoring.setCheckable(True)
            self.action_enable_monitoring.setChecked(self.app.service.is_running())
            self.action_enable_monitoring.setEnabled(not self.app.serviceDisabled)
            self.action_enable_monitoring.triggered.connect(self.on_enable_toggled)

            menu.addAction(self.action_enable_monitoring)
            menu.addAction(QIcon.fromTheme("edit-clear"), "&Hide Icon", self.on_hide_icon)
            menu.addAction(QIcon.fromTheme("configure"), "&Show Main Window", self.on_configure)
            menu.addAction(QIcon.fromTheme("application-quit"), "Exit AutoKey", self.on_quit)
            self.icon.setContextMenu(menu)

    def update_visible_status(self):
        self.icon.setVisible(cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON])
        self.build_menu()

    def hide_icon(self):
        if cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]:
            self.icon.hide()

    def notify_error(self, message):
        pass
        
    # ---- Signal handlers ----

    def on_show_error(self):
        self.app.exec_in_main(self.app.show_script_error)

    def on_quit(self):
        self.app.shutdown()

    def on_activate(self, reason):
        if reason == QSystemTrayIcon.ActivationReason(QSystemTrayIcon.Trigger):
            self.on_configure()

    def on_configure(self):
        self.app.show_configure()
        
    def on_enable_toggled(self):
        if self.action_enable_monitoring.isChecked():
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_hide_icon(self):
        self.icon.hide()
        cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON] = False
