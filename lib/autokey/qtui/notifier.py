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

import logging

from PyQt4.QtGui import QSystemTrayIcon, QIcon, QAction

from autokey.qtui import popupmenu
import autokey.qtui.common
from autokey import configmanager as cm

TOOLTIP_RUNNING = "AutoKey - running"
TOOLTIP_PAUSED = "AutoKey - paused"

logger = autokey.qtui.common.logger.getChild("System-tray-notifier")  # type: logging.Logger


class Notifier:
    
    def __init__(self, app):
        self.action_enable_monitoring = None  # type: QAction
        self.app = app
        self.configManager = app.configManager
        
        self.icon = QSystemTrayIcon(QIcon.fromTheme(cm.ConfigManager.SETTINGS[cm.NOTIFICATION_ICON]))
        self.icon.activated.connect(self.on_activate)
        logger.info("Notifier created.")
        self.build_menu()

        if cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]:
            self.update_tool_tip(cm.ConfigManager.SETTINGS[cm.SERVICE_RUNNING])
            self.app.monitoring_disabled.connect(self.update_tool_tip)
            self.icon.show()
                        
    def update_tool_tip(self, service_running: bool):
        if service_running:
            self.icon.setToolTip(TOOLTIP_RUNNING)
        else:
            self.icon.setToolTip(TOOLTIP_PAUSED)

    def build_menu(self):
        logger.debug("Show tray icon enabled in settings: {}".format(cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]))
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
            # Sync action state with internal service state
            self.action_enable_monitoring.triggered.connect(self.app.toggle_service)
            self.app.monitoring_disabled.connect(self.action_enable_monitoring.setChecked)

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
        logger.debug("on_activate called with reason: {}".format(reason))
        if reason == QSystemTrayIcon.ActivationReason(QSystemTrayIcon.Trigger):
            self.on_configure()

    def on_configure(self):
        self.app.show_configure()
            
    def on_hide_icon(self):
        self.icon.hide()
        cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON] = False
