#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2020 BlueDrink9
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
import dbus.mainloop.glib
import subprocess
from typing import NamedTuple, Iterable

import autokey.model.script
from autokey import common

from autokey import service, monitor

import autokey.argument_parser
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants
import autokey.dbus_service

from autokey.logger import get_logger, configure_root_logger
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


class AutokeyApplication:
    """
    Main application interface; starting and stopping of the application is controlled
    from here, together with some interactions from the tray icon.
    Handles starting service and responding to dbus requests. Should have an
    associated UI that does nothing except interface with the user. All
    interaction with the system or X for hotkeys etc should go via this
    class. Exceptions might be made for async?
    """

    def __init__(self, argv: list=sys.argv, UI=None):
        super().__init__() # Forward any arguments
        # self.handler = CallbackEventHandler()
        self.args = autokey.argument_parser.parse_args()
        self.UI = UI  # Should be overridden by child UIs
        try:
            self.__initialise()
        except Exception as e:
            logger.exception("Fatal error starting AutoKey: " + str(e))
            if self.UI is not None:
                self.UI.show_error_dialog("Fatal error starting AutoKey.", str(e))
            sys.exit(1)

    def __initialise(self):
        configure_root_logger(self.args)
        self.__warn_about_missing_requirements()
        AutokeyApplication.create_storage_directories()
        if self.__verify_not_running():
            AutokeyApplication.create_lock_file()

        self.__initialise_services()
        # self.notifier = Notifier(self)
        # self.configWindow = ConfigWindow(self)

        self.__initialise_user_code_dir()

        self.__create_DBus_service()
        # self.show_configure_signal.connect(self.show_configure, Qt.QueuedConnection)

        # self.installEventFilter(KeyboardChangeFilter(self.service.mediator.interface))

    def __create_DBus_service(self):
        logger.info("Creating DBus service")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.dbusService = autokey.dbus_service.AppService(self)
        logger.debug("DBus service created")

    def __initialise_user_code_dir(self):
        if self.configManager.userCodeDir is not None:
            sys.path.append(self.configManager.userCodeDir)

    def __initialise_services(self):
        logger.info("Initialising application")
        self.monitor = monitor.FileMonitor(self)
        self.configManager = cm.create_config_manager_instance(self)
        self.service = service.Service(self)
        self.serviceDisabled = False
        self.__try_start_service()
        self.__try_start_monitor()

    def __warn_about_missing_requirements(self):
        UI_common.checkOptionalPrograms()
        missing_reqs = UI_common.checkRequirements()
        if len(missing_reqs)>0:
            self.UI.show_error_dialog("AutoKey Requires the following programs or python modules to be installed to function properly\n\n"+missing_reqs)
            sys.exit("Missing required programs and/or python modules, exiting")

    def __try_start_service(self):
        try:
            self.service.start()
        except Exception as e:
            logger.exception("Error starting interface: " + str(e))
            self.serviceDisabled = True
            self.UI.show_error_dialog("Error starting interface. Keyboard monitoring will be disabled.\n" +
                                   "Check your system/configuration.", str(e))

    def ctrlc_interrupt_handler(self, signal, frame):
        logger.info("Recieved keyboard interrupt. Shutting down")
        self.UI.shutdown()

    def __register_ctrlc_handler(self):
        """
        Handles keyboard interrupts (ctrl-c) when run from command line.
        """
        signal.signal(signal.SIGINT, self.ctrlc_interrupt_handler)

    def __try_start_monitor(self):
        try:
            self.monitor.start()
        except Exception as e:
            logger.exception("Error starting file monitor. Error: " + str(e))
            self.UI.show_error_dialog("Error starting file monitor. Error: " + str(e))

    def __verify_not_running(self):
        if self.__is_existing_running_autokey():
            UI_common.test_Dbus_response(self)
        return True

    def __try_to_show_existing_autokey_UI_and_exit(self):
        try:
            self.__show_running_autokey_window()
            sys.exit(0)
        except dbus.DBusException as e:
            pid = AutokeyApplication.read_pid_from_lock_file()
            message="AutoKey is already running as pid {} but is not responding".format(pid)
            logger.exception(
                "Error communicating with Dbus service. {}".format(message))
            self.UI.show_error_dialog(
                message=message,
                details=str(e))
            sys.exit(1)

    def __show_running_autokey_window(self):
        bus = dbus.SessionBus()
        dbus_service = bus.get_object("org.autokey.Service", "/AppService")
        dbus_service.show_configure(dbus_interface="org.autokey.Service")
        # return dbus_service

    @staticmethod
    def create_storage_directories():
        """Create various storage directories, if those do not exist."""
        # Create configuration directory
        os.makedirs(common.CONFIG_DIR, exist_ok=True)
        # Create data directory (for log file)
        os.makedirs(common.DATA_DIR, exist_ok=True)
        # Create run directory (for lock file)
        os.makedirs(common.RUN_DIR, exist_ok=True)

    @staticmethod
    def create_lock_file():
        with open(common.LOCK_FILE, "w") as lock_file:
            lock_file.write(str(os.getpid()))

    def __is_existing_running_autokey(self):
        if os.path.exists(common.LOCK_FILE):
            pid = self.__read_pid_from_lock_file()
            pid_is_a_running_autokey = "autokey" in self.__get_process_details(pid)
            if pid_is_a_running_autokey:
                logger.debug("AutoKey is already running as pid %s", pid)
                return True
        return False

    def __read_pid_from_lock_file(self) -> str:
        with open(common.LOCK_FILE, "r") as lock_file:
            pid = lock_file.read()
        self.__exit_if_lock_file_corrupt(pid)
        return pid

    def __exit_if_lock_file_corrupt(self, pid):
        try:
            # Check if the pid file contains garbage
            int(pid)
        except ValueError:
            logger.exception("AutoKey pid file contains garbage instead of a usable process id: " + pid)
            sys.exit(1)

    def __get_process_details(self, pid):
        with subprocess.Popen(["ps", "-p", pid, "-o", "command"], stdout=subprocess.PIPE) as p:
            output = p.communicate()[0].decode()
        return output

    def init_global_hotkeys(self, configManager):
        logger.info("Initialise global hotkeys")
        configManager.toggleServiceHotkey.set_closure(self.toggle_service)
        # configManager.configHotkey.set_closure(self.show_configure_signal.emit)

    def config_altered(self, persistGlobal):
        self.configManager.config_altered(persistGlobal)
        # self.notifier.create_assign_context_menu()

    def hotkey_created(self, item):
        UI_common.hotkey_created(self.service, item)

    def hotkey_removed(self, item):
        UI_common.hotkey_removed(self.service, item)

    # def path_created_or_modified(self, path):
        # UI_common.path_created_or_modified(self.configManager, self.configWindow, path)

    # def path_removed(self, path):
        # UI_common.path_removed(self.configManager, self.configWindow, path)
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

    # def update_notifier_visibility(self):
    #     self.notifier.update_visible_status()

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
        logger.info("Displaying Error Dialog")
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


# class CallbackEventHandler(QObject):

#     def __init__(self):
#         QObject.__init__(self)
#         self.queue = queue.Queue()

#     def customEvent(self, event):
#         while True:
#             try:
#                 callback, args = self.queue.get_nowait()
#             except queue.Empty:
#                 break
#             try:
#                 callback(*args)
#             except Exception:
#                 logger.exception("callback event failed: %r %r", callback, args, exc_info=True)

#     def postEventWithCallback(self, callback, *args):
#         self.queue.put((callback, args))
#         app = QApplication.instance()
#         app.postEvent(self, QEvent(QEvent.User))


# class KeyboardChangeFilter(QObject):

#     def __init__(self, interface):
#         QObject.__init__(self)
#         self.interface = interface

#     def eventFilter(self, obj, event):
#         if event.type() == QEvent.KeyboardLayoutChange:
#             self.interface.on_keys_changed()

#         return QObject.eventFilter(obj, event)
