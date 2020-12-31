#!/usr/bin/env python
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


import sys
import os.path
import queue
import time
import dbus
from typing import NamedTuple, Iterable

from PyQt5.QtCore import QObject, QEvent, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QMessageBox, QApplication

import autokey.model.script
from autokey import common
common.USING_QT = True

from autokey import service, monitor

import autokey.argument_parser
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants

from autokey.qtui import common as ui_common
from autokey.qtui.notifier import Notifier
from autokey.qtui.popupmenu import PopupMenu
from autokey.qtui.configwindow import ConfigWindow
from autokey.qtui.dbus_service import AppService
from autokey.logger import get_logger, configure_root_logger
from autokey.UI_common_functions import checkRequirements, checkOptionalPrograms, create_storage_directories
import autokey.UI_common_functions as UI_common

logger = get_logger(__name__)
del get_logger

AuthorData = NamedTuple("AuthorData", (("name", str), ("role", str), ("email", str)))
AboutData = NamedTuple("AboutData", (
    ("program_name", str),
    ("version", str),
    ("program_description", str),
    ("license_text", str),
    ("copyright_notice", str),
    ("homepage_url", str),
    ("bug_report_email", str),
    ("author_list", Iterable[AuthorData])
))

COPYRIGHT = """(c) 2009-2012 Chris Dekter
(c) 2014 GuoCi
(c) 2017, 2018 Thomas Hess
"""

author_data = (
    AuthorData("Thomas Hess", "PyKDE4 to PyQt5 port", "thomas.hess@udo.edu"),
    AuthorData("GuoCi", "Python 3 port maintainer", "guociz@gmail.com"),
    AuthorData("Chris Dekter", "Developer", "cdekter@gmail.com"),
    AuthorData("Sam Peterson", "Original developer", "peabodyenator@gmail.com")
)
about_data = AboutData(
   program_name="AutoKey",
   version=common.VERSION,
   program_description="Desktop automation utility",
   license_text="GPL v3",  # TODO: load actual license text from disk somewhere
   copyright_notice=COPYRIGHT,
   homepage_url=common.HOMEPAGE,
   bug_report_email=common.BUG_EMAIL,
   author_list=author_data
)


class Application(QApplication):
    """
    Main application class; starting and stopping of the application is controlled
    from here, together with some interactions from the tray icon.
    """

    monitoring_disabled = pyqtSignal(bool, name="monitoring_disabled")
    show_configure_signal = pyqtSignal()

    def __init__(self, argv: list=sys.argv):
        super().__init__(argv)
        self.handler = CallbackEventHandler()
        self.args = autokey.argument_parser.parse_args()
        try:
            create_storage_directories()
            configure_root_logger(self.args)
        except Exception as e:
            logger.exception("Fatal error starting AutoKey: " + str(e))
            self.show_error_dialog("Fatal error starting AutoKey.", str(e))
            sys.exit(1)

        checkOptionalPrograms()
        missing_reqs = checkRequirements()
        if len(missing_reqs)>0:
            self.show_error_dialog("AutoKey Requires the following programs or python modules to be installed to function properly\n\n"+missing_reqs)
            sys.exit("Missing required programs and/or python modules, exiting")

        logger.info("Initialising application")
        self.setWindowIcon(QIcon.fromTheme(common.ICON_FILE, ui_common.load_icon(ui_common.AutoKeyIcon.AUTOKEY)))
        try:
            if self._verify_not_running():
                UI_common.create_lock_file()

            self.monitor = monitor.FileMonitor(self)
            self.configManager = cm.create_config_manager_instance(self)
            self.service = service.Service(self)
            self.serviceDisabled = False
            self._try_start_service()
            self.notifier = Notifier(self)
            self.configWindow = ConfigWindow(self)
            # Connect the mutual connections between the tray icon and the main window
            self.configWindow.action_show_last_script_errors.triggered.connect(self.notifier.reset_tray_icon)
            self.notifier.action_view_script_error.triggered.connect(
                self.configWindow.show_script_errors_dialog.update_and_show)

            self.monitor.start()
            # Initialise user code dir
            if self.configManager.userCodeDir is not None:
                sys.path.append(self.configManager.userCodeDir)
            logger.debug("Creating DBus service")
            self.dbus_service = AppService(self)
            logger.debug("Service created")
            self.show_configure_signal.connect(self.show_configure, Qt.QueuedConnection)
            if cm.ConfigManager.SETTINGS[cm_constants.IS_FIRST_RUN]:
                cm.ConfigManager.SETTINGS[cm_constants.IS_FIRST_RUN] = False
                self.args.show_config_window = True
            if self.args.show_config_window:
                self.show_configure()

            self.installEventFilter(KeyboardChangeFilter(self.service.mediator.interface))

        except Exception as e:
            logger.exception("Fatal error starting AutoKey: " + str(e))
            self.show_error_dialog("Fatal error starting AutoKey.", str(e))
            sys.exit(1)
        else:
            sys.exit(self.exec_())

    def _try_start_service(self):
        try:
            self.service.start()
        except Exception as e:
            logger.exception("Error starting interface: " + str(e))
            self.serviceDisabled = True
            self.show_error_dialog("Error starting interface. Keyboard monitoring will be disabled.\n" +
                                   "Check your system/configuration.", str(e))

    @staticmethod
    def _create_lock_file():
        with open(common.LOCK_FILE, "w") as lock_file:
            lock_file.write(str(os.getpid()))

    def _verify_not_running(self):
        if UI_common.is_existing_running_autokey():
            UI_common.test_Dbus_response(self)
        return True

    def init_global_hotkeys(self, configManager):
        logger.info("Initialise global hotkeys")
        configManager.toggleServiceHotkey.set_closure(self.toggle_service)
        configManager.configHotkey.set_closure(self.show_configure_signal.emit)

    def config_altered(self, persistGlobal):
        self.configManager.config_altered(persistGlobal)
        self.notifier.create_assign_context_menu()

    def hotkey_created(self, item):
        UI_common.hotkey_created(self.service, item)

    def hotkey_removed(self, item):
        UI_common.hotkey_removed(self.service, item)

    def path_created_or_modified(self, path):
        UI_common.path_created_or_modified(self.configManager, self.configWindow, path)

    def path_removed(self, path):
        UI_common.path_removed(self.configManager, self.configWindow, path)
    def unpause_service(self):
        """
        Unpause the expansion service (start responding to keyboard and mouse events).
        """
        self.service.unpause()

    def pause_service(self):
        """
        Pause the expansion service (stop responding to keyboard and mouse events).
        """
        self.service.pause()

    def toggle_service(self):
        """
        Convenience method for toggling the expansion service on or off. This is called by the global hotkey.
        """
        self.monitoring_disabled.emit(not self.service.is_running())
        if self.service.is_running():
            self.pause_service()
        else:
            self.unpause_service()

    def shutdown(self):
        """
        Shut down the entire application.
        """
        logger.info("Shutting down")
        self.closeAllWindows()
        self.notifier.hide()
        self.service.shutdown()
        self.monitor.stop()
        self.quit()
        os.remove(common.LOCK_FILE)  # TODO: maybe use atexit to remove the lock/pid file?
        logger.debug("All shutdown tasks complete... quitting")

    def notify_error(self, error: autokey.model.script.ScriptErrorRecord):
        """
        Show an error notification popup.

        @param error: The error that occurred in a Script
        """
        message = "The script '{}' encountered an error".format(error.script_name)
        self.exec_in_main(self.notifier.notify_error, message)
        self.configWindow.script_errors_available.emit(True)

    def update_notifier_visibility(self):
        self.notifier.update_visible_status()

    def show_configure(self):
        """
        Show the configuration window, or deiconify (un-minimise) it if it's already open.
        """
        logger.info("Displaying configuration window")
        self.configWindow.show()
        self.configWindow.showNormal()
        self.configWindow.activateWindow()

    @staticmethod
    def show_error_dialog(message: str, details: str=None):
        """
        Convenience method for showing an error dialog.
        """
        # TODO: i18n
        logger.debug("Displaying Error Dialog")
        message_box = QMessageBox(
            QMessageBox.Critical,
            "Error",
            message,
            QMessageBox.Ok,
            None
        )
        if details:
            message_box.setDetailedText(details)
        message_box.exec_()

    def show_popup_menu(self, folders: list=None, items: list=None, onDesktop=True, title=None):
        if items is None:
            items = []
        if folders is None:
            folders = []
        self.exec_in_main(self.__createMenu, folders, items, onDesktop, title)

    def hide_menu(self):
        self.exec_in_main(self.menu.hide)

    def __createMenu(self, folders, items, onDesktop, title):
        self.menu = PopupMenu(self.service, folders, items, onDesktop, title)
        self.menu.popup(QCursor.pos())
        self.menu.setFocus()

    def exec_in_main(self, callback, *args):
        self.handler.postEventWithCallback(callback, *args)


class CallbackEventHandler(QObject):

    def __init__(self):
        QObject.__init__(self)
        self.queue = queue.Queue()

    def customEvent(self, event):
        while True:
            try:
                callback, args = self.queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback(*args)
            except Exception:
                logger.exception("callback event failed: %r %r", callback, args, exc_info=True)

    def postEventWithCallback(self, callback, *args):
        self.queue.put((callback, args))
        app = QApplication.instance()
        app.postEvent(self, QEvent(QEvent.User))


class KeyboardChangeFilter(QObject):

    def __init__(self, interface):
        QObject.__init__(self)
        self.interface = interface

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyboardLayoutChange:
            self.interface.on_keys_changed()

        return QObject.eventFilter(obj, event)
