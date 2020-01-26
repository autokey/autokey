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

from typing import Optional, Callable, TYPE_CHECKING

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu

from autokey.qtui import popupmenu
import autokey.qtui.common as ui_common
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants

if TYPE_CHECKING:
    from autokey.qtapp import Application

logger = __import__("autokey.logger").logger.get_logger(__name__)
TOOLTIP_RUNNING = "AutoKey - running"
TOOLTIP_PAUSED = "AutoKey - paused"


class Notifier(QSystemTrayIcon):
    
    def __init__(self, app):
        logger.debug("Creating system tray icon notifier.")
        icon = self._load_default_icon()
        super(Notifier, self).__init__(icon, app)
        # Actions
        self.action_view_script_error = None  # type: QAction
        self.action_hide_icon = None  # type: QAction
        self.action_show_config_window = None  # type: QAction
        self.action_quit = None  # type: QAction
        self.action_enable_monitoring = None  # type: QAction

        self.app = app  # type: Application
        self.config_manager = self.app.configManager
        self.activated.connect(self.on_activate)

        self._create_static_actions()
        self.create_assign_context_menu()
        self.update_tool_tip(cm.ConfigManager.SETTINGS[cm_constants.SERVICE_RUNNING])
        self.app.monitoring_disabled.connect(self.update_tool_tip)
        if cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON]:
            logger.debug("About to show the tray icon.")
            self.show()
        logger.info("System tray icon notifier created.")

    def create_assign_context_menu(self):
        """
        Create a context menu, then set the created QMenu as the context menu.
        This builds the menu with all required actions and signal-slot connections.
        """
        menu = QMenu("AutoKey")
        self._build_menu(menu)
        self.setContextMenu(menu)

    def update_tool_tip(self, service_running: bool):
        """Slot function that updates the tooltip when the user activates or deactivates the expansion service."""
        if service_running:
            self.setToolTip(TOOLTIP_RUNNING)
        else:
            self.setToolTip(TOOLTIP_PAUSED)

    @staticmethod
    def _load_default_icon() -> QIcon:
        return QIcon.fromTheme(
            cm.ConfigManager.SETTINGS[cm.NOTIFICATION_ICON],
            ui_common.load_icon(ui_common.AutoKeyIcon.SYSTEM_TRAY)
        )

    @staticmethod
    def _load_error_state_icon() -> QIcon:
        return QIcon.fromTheme(
            "autokey-status-error",
            ui_common.load_icon(ui_common.AutoKeyIcon.SYSTEM_TRAY_ERROR)
        )

    def _create_action(
            self,
            icon_name: Optional[str],
            title: str,
            slot_function: Callable[[None], None],
            tool_tip: Optional[str]=None)-> QAction:
        """
        QAction factory. All items created belong to the calling instance, i.e. created QAction parent is self.
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
        self.action_view_script_error = self._create_action(
            None, "&View script error", self.reset_tray_icon,
            "View the last script error."
        )
        # The action should disable itself
        self.action_view_script_error.setDisabled(True)
        self.action_view_script_error.triggered.connect(self.action_view_script_error.setEnabled)
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
        self.action_enable_monitoring.setDisabled(self.app.serviceDisabled)
        # Sync action state with internal service state
        self.app.monitoring_disabled.connect(self.action_enable_monitoring.setChecked)

    def _fill_context_menu_with_model_item_actions(self, context_menu: QMenu):
        """
        Find all model items that should be available in the context menu and create QActions for each, by
        using the available logic in popupmenu.PopupMenu.
        """
        # Get phrase folders to add to main menu
        logger.info("Rebuilding model item actions, adding all items marked for access through the tray icon.")
        folders = [folder for folder in self.config_manager.allFolders if folder.show_in_tray_menu]
        items = [item for item in self.config_manager.allItems if item.show_in_tray_menu]
        # Only extract the QActions, but discard the PopupMenu instance.
        # This is done, because the PopupMenu class is not directly usable as a context menu here.
        menu = popupmenu.PopupMenu(self.app.service, folders, items, False, "AutoKey")
        new_item_actions = menu.actions()
        context_menu.addActions(new_item_actions)
        for action in new_item_actions:  # type: QAction
            # QMenu does not take the ownership when adding QActions, so manually re-parent all actions.
            # This causes the QActions to be destroyed when the context menu is cleared or re-created.
            action.setParent(context_menu)

        if not context_menu.isEmpty():
            # Avoid a stray separator line, if no items are marked for display in the context menu.
            context_menu.addSeparator()

    def _build_menu(self, context_menu: QMenu):
        """Build the context menu."""
        logger.debug("Show tray icon enabled in settings: {}".format(
            cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON])
        )
        # Items selected for display are shown on top
        self._fill_context_menu_with_model_item_actions(context_menu)
        # The static actions are added at the bottom
        context_menu.addAction(self.action_view_script_error)
        context_menu.addAction(self.action_enable_monitoring)
        context_menu.addAction(self.action_hide_icon)
        context_menu.addAction(self.action_show_config_window)
        context_menu.addAction(self.action_quit)

    def update_visible_status(self):
        visible = cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON]
        if visible:
            self.create_assign_context_menu()
        self.setVisible(visible)
        logger.info("Updated tray icon visibility. Is icon shown: {}".format(visible))

    def notify_error(self, message: str):
        self.setIcon(self._load_error_state_icon())
        self.action_view_script_error.setEnabled(True)
        self.showMessage("AutoKey Error", message)

    def reset_tray_icon(self):
        """
        Slot function that resets the icon to the default, as configured in the settings.
        Used when the user switches the icon theme in the settings and when a script error condition is cleared.
        """
        self.setIcon(self._load_default_icon())

    def on_activate(self, reason: QSystemTrayIcon.ActivationReason):
        logger.debug("Triggered system tray icon with reason: {}".format(reason))
        if reason == QSystemTrayIcon.ActivationReason(QSystemTrayIcon.Trigger):
            self.app.show_configure()
