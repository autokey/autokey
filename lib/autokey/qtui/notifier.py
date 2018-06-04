# Copyright (C) 2011 Chris Dekter
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

import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu

from autokey.qtui import popupmenu
import autokey.qtui.common as ui_common
from autokey import configmanager as cm

TOOLTIP_RUNNING = "AutoKey - running"
TOOLTIP_PAUSED = "AutoKey - paused"

logger = ui_common.logger.getChild("System-tray-notifier")  # type: logging.Logger


class Notifier(QSystemTrayIcon):
    
    def __init__(self, app):
        logger.debug("Creating system tray icon notifier.")
        icon = QIcon.fromTheme(
            cm.ConfigManager.SETTINGS[cm.NOTIFICATION_ICON],
            ui_common.load_icon(ui_common.AutoKeyIcon.SYSTEM_TRAY)
        )
        super(Notifier, self).__init__(icon)
        # Actions
        self.action_hide_icon = None  # type: QAction
        self.action_show_config_window = None  # type: QAction
        self.action_quit = None  # type: QAction
        self.action_enable_monitoring = None  # type: QAction

        self.app = app
        self.configManager = app.configManager
        self.setContextMenu(QMenu("AutoKey"))
        self.activated.connect(self.on_activate)
        self._create_static_actions()
        self.update_tool_tip(cm.ConfigManager.SETTINGS[cm.SERVICE_RUNNING])
        self.app.monitoring_disabled.connect(self.update_tool_tip)

        if cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]:
            self.build_menu()
            logger.debug("About to show the tray icon.")
            self.show()
        logger.info("System tray icon notifier created.")
                        
    def update_tool_tip(self, service_running: bool):
        if service_running:
            self.setToolTip(TOOLTIP_RUNNING)
        else:
            self.setToolTip(TOOLTIP_PAUSED)

    def _create_action(self, icon_name: str, title: str, slot_function) -> QAction:
        """
        QAction factory.
        """
        action = QAction(title, self)
        action.setIcon(QIcon.fromTheme(icon_name))
        action.triggered.connect(slot_function)
        return action

    def _create_static_actions(self):
        """
        Create all static menu actions. The created actions will be placed in the tray icon context menu.
        """
        logger.info("Creating static context menu actions.")
        self.action_hide_icon = self._create_action("edit-clear", "&Hide Icon", self.on_hide_icon)
        self.action_show_config_window = self._create_action("configure", "&Show Main Window", self.on_configure)
        self.action_quit = self._create_action("application-exit", "Exit AutoKey", self.on_quit)
        # TODO: maybe import this from configwindow.py ? The exact same Action is defined in the main window.
        self.action_enable_monitoring = QAction("&Enable Monitoring", self)
        self.action_enable_monitoring.setCheckable(True)
        self.action_enable_monitoring.setChecked(self.app.service.is_running())
        self.action_enable_monitoring.setEnabled(not self.app.serviceDisabled)
        # Sync action state with internal service state
        self.action_enable_monitoring.triggered.connect(self.app.toggle_service)
        self.app.monitoring_disabled.connect(self.action_enable_monitoring.setChecked)

    def _fill_context_menu_with_model_item_actions(self):
        """
        Find all model items that should be available in the context menu and create QActions for each, by
        using the available logic in popupmenu.PopupMenu.
        """
        # Get phrase folders to add to main menu
        logger.info("Rebuilding model item actions, adding all items marked for access through the tray icon.")
        folders = [folder for folder in self.configManager.allFolders if folder.showInTrayMenu]
        items = [item for item in self.configManager.allItems if item.showInTrayMenu]
        # Only extract the QActions, but discard the PopupMenu instance.
        menu = popupmenu.PopupMenu(self.app.service, folders, items, False, "AutoKey")
        actions = menu.actions()
        context_menu = self.contextMenu()
        context_menu.addActions(actions)
        for action in actions:  # type: QAction
            action.setParent(context_menu)

        if items or folders:
            context_menu.addSeparator()

    def build_menu(self):
        logger.debug("Show tray icon enabled in settings: {}".format(cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]))
        if cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]:
            menu = self.contextMenu()
            menu.clear()
            self._fill_context_menu_with_model_item_actions()
            menu.addAction(self.action_enable_monitoring)
            menu.addAction(self.action_hide_icon)
            menu.addAction(self.action_show_config_window)
            menu.addAction(self.action_quit)

    def update_visible_status(self):
        self.build_menu()
        self.setVisible(cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON])

    def hide_icon(self):
        if cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]:
            self.hide()

    def notify_error(self, message):
        pass
        
    # ---- Signal handlers ----

    def on_show_error(self):
        self.app.exec_in_main(self.app.show_script_error)

    def on_quit(self):
        self.app.shutdown()

    def on_activate(self, reason):
        logger.debug("Triggered system tray icon with reason: {}".format(reason))
        if reason == QSystemTrayIcon.ActivationReason(QSystemTrayIcon.Trigger):
            self.on_configure()

    def on_configure(self):
        self.app.show_configure()
            
    def on_hide_icon(self):
        self.hide()
        cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON] = False
