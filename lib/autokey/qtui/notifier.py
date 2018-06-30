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
from typing import Optional, Callable, TYPE_CHECKING

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu

from autokey.qtui import popupmenu
import autokey.qtui.common as ui_common
from autokey import configmanager as cm

if TYPE_CHECKING:
    from autokey.qtapp import Application

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

        self.app = app  # type: Application
        self.config_manager = self.app.configManager
        self.setContextMenu(QMenu("AutoKey"))
        self.activated.connect(self.on_activate)
        self._create_static_actions()
        self.update_tool_tip(cm.ConfigManager.SETTINGS[cm.SERVICE_RUNNING])
        self.app.monitoring_disabled.connect(self.update_tool_tip)
        self.build_menu()
        if cm.ConfigManager.SETTINGS[cm.SHOW_TRAY_ICON]:
            logger.debug("About to show the tray icon.")
            self.show()
        logger.info("System tray icon notifier created.")
                        
    def update_tool_tip(self, service_running: bool):
        if service_running:
            self.setToolTip(TOOLTIP_RUNNING)
        else:
            self.setToolTip(TOOLTIP_PAUSED)

    def _create_action(
            self,
            icon_name: Optional[str],
            title: str,
            slot_function: Callable[[None], None],
            tool_tip: Optional[str]=None)-> QAction:
        """
        QAction factory.
        """
        action = QAction(title, self)
        if icon_name:
            action.setIcon(QIcon.fromTheme(icon_name))
        action.triggered.connect(slot_function)
        if tool_tip:
            action.setToolTip(tool_tip)
        return action

    def _create_static_actions(self):
        """
        Create all static menu actions. The created actions will be placed in the tray icon context menu.
        """
        logger.info("Creating static context menu actions.")
        self.action_hide_icon = self._create_action(
            "edit-clear", "Temporarily &Hide Icon", self.hide,
            "Temporarily hide the system tray icon.\nUse the settings to hide it permanently."
        )
        self.action_show_config_window = self._create_action(
            "configure", "&Show Main Window", self.app.show_configure,
            "Show the main AutoKey window. This does the same as left clicking the tray icon."
        )
        self.action_quit = self._create_action("application-exit", "Exit AutoKey", self.app.shutdown)
        # TODO: maybe import this from configwindow.py ? The exact same Action is defined in the main window.
        self.action_enable_monitoring = self._create_action(
            None, "&Enable Monitoring", self.app.toggle_service,
            "Pause the phrase expansion and script execution, both by abbreviations and hotkeys.\n"
            "The global hotkeys to show the main window and to toggle this setting, as defined in the AutoKey "
            "settings, are not affected and will work regardless."
        )
        self.action_enable_monitoring.setCheckable(True)
        self.action_enable_monitoring.setChecked(self.app.service.is_running())
        self.action_enable_monitoring.setEnabled(not self.app.serviceDisabled)
        # Sync action state with internal service state
        self.app.monitoring_disabled.connect(self.action_enable_monitoring.setChecked)

    def _fill_context_menu_with_model_item_actions(self):
        """
        Find all model items that should be available in the context menu and create QActions for each, by
        using the available logic in popupmenu.PopupMenu.
        """
        # Get phrase folders to add to main menu
        logger.info("Rebuilding model item actions, adding all items marked for access through the tray icon.")
        folders = [folder for folder in self.config_manager.allFolders if folder.show_in_tray_menu]
        items = [item for item in self.config_manager.allItems if item.show_in_tray_menu]
        # Only extract the QActions, but discard the PopupMenu instance.
        menu = popupmenu.PopupMenu(self.app.service, folders, items, False, "AutoKey")
        new_item_actions = menu.actions()
        context_menu = self.contextMenu()
        context_menu.addActions(new_item_actions)
        for action in new_item_actions:  # type: QAction
            # QMenu does not take the ownership when adding QActions, so manually re-parent all actions.
            action.setParent(context_menu)

        if items or folders:
            context_menu.addSeparator()

    def build_menu(self):
        """Rebuild the context menu."""
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

    def notify_error(self, message: str):
        self.showMessage("AutoKey Error", message)

    def on_activate(self, reason: QSystemTrayIcon.ActivationReason):
        logger.debug("Triggered system tray icon with reason: {}".format(reason))
        if reason == QSystemTrayIcon.ActivationReason(QSystemTrayIcon.Trigger):
            self.app.show_configure()
