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

from . import common
common.USING_QT = True

import sys
import os.path
import logging
import logging.handlers
import subprocess
import queue
import time
import dbus
import argparse
from typing import NamedTuple, Iterable

from PyQt5.QtCore import QObject, QEvent, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QMessageBox, QApplication

from autokey import service, monitor
from autokey.qtui import common as ui_common
from autokey.qtui.notifier import Notifier
from autokey.qtui.popupmenu import PopupMenu
from autokey.qtui.configwindow import ConfigWindow
from autokey import configmanager as cm
from autokey.qtui.dbus_service import AppService

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


def generate_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Desktop automation ")
    parser.add_argument(
        "-l", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "-c", "--configure",
        action="store_true",
        dest="show_config_window",
        help="Show the configuration window on startup"
    )
    return parser


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
        parser = generate_argument_parser()
        self.args = parser.parse_args()
        try:
            self._create_storage_directories()
            self._configure_root_logger()
        except Exception as e:
            logging.exception("Fatal error starting AutoKey: " + str(e))
            self.show_error_dialog("Fatal error starting AutoKey.", str(e))
            sys.exit(1)
        logging.info("Initialising application")
        self.setWindowIcon(QIcon.fromTheme(common.ICON_FILE, ui_common.load_icon(ui_common.AutoKeyIcon.AUTOKEY)))
        try:

            # Initialise logger

            if self._verify_not_running():
                self._create_lock_file()

            self.monitor = monitor.FileMonitor(self)
            self.configManager = cm.get_config_manager(self)
            self.service = service.Service(self)
            self.serviceDisabled = False
            self._try_start_service()
            self.notifier = Notifier(self)
            self.configWindow = ConfigWindow(self)
            self.monitor.start()
            # Initialise user code dir
            if self.configManager.userCodeDir is not None:
                sys.path.append(self.configManager.userCodeDir)
            logging.debug("Creating DBus service")
            self.dbus_service = AppService(self)
            logging.debug("Service created")
            self.show_configure_signal.connect(self.show_configure, Qt.QueuedConnection)
            if cm.ConfigManager.SETTINGS[cm.IS_FIRST_RUN]:
                cm.ConfigManager.SETTINGS[cm.IS_FIRST_RUN] = False
                self.args.show_config_window = True
            if self.args.show_config_window:
                self.show_configure()

            self.installEventFilter(KeyboardChangeFilter(self.service.mediator.interface))

        except Exception as e:
            logging.exception("Fatal error starting AutoKey: " + str(e))
            self.show_error_dialog("Fatal error starting AutoKey.", str(e))
            sys.exit(1)
        else:
            sys.exit(self.exec_())

    def _try_start_service(self):
        try:
            self.service.start()
        except Exception as e:
            logging.exception("Error starting interface: " + str(e))
            self.serviceDisabled = True
            self.show_error_dialog("Error starting interface. Keyboard monitoring will be disabled.\n" +
                                   "Check your system/configuration.", str(e))

    def _configure_root_logger(self):
        """Initialise logging system"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        if self.args.verbose:
            handler = logging.StreamHandler(sys.stdout)
        else:
            handler = logging.handlers.RotatingFileHandler(
                common.LOG_FILE,
                maxBytes=common.MAX_LOG_SIZE,
                backupCount=common.MAX_LOG_COUNT
            )
            handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(common.LOG_FORMAT))
        root_logger.addHandler(handler)

    @staticmethod
    def _create_storage_directories():
        """Create various storage directories, if those do not exist."""
        # Create configuration directory
        if not os.path.exists(common.CONFIG_DIR):
            os.makedirs(common.CONFIG_DIR)
        # Create data directory (for log file)
        if not os.path.exists(common.DATA_DIR):
            os.makedirs(common.DATA_DIR)
        # Create run directory (for lock file)
        if not os.path.exists(common.RUN_DIR):
            os.makedirs(common.RUN_DIR)

    @staticmethod
    def _create_lock_file():
        with open(common.LOCK_FILE, "w") as lock_file:
            lock_file.write(str(os.getpid()))

    def _verify_not_running(self):
        if os.path.exists(common.LOCK_FILE):
            with open(common.LOCK_FILE, "r") as lock_file:
                pid = lock_file.read()
            try:
                # Check if the pid file contains garbage
                int(pid)
            except ValueError:
                logging.exception("AutoKey pid file contains garbage instead of a usable process id: " + pid)
                sys.exit(1)

            # Check that the found PID is running and is autokey
            with subprocess.Popen(["ps", "-p", pid, "-o", "command"], stdout=subprocess.PIPE) as p:
                output = p.communicate()[0].decode()
            if "autokey" in output:
                logging.debug("AutoKey is already running as pid " + pid)
                bus = dbus.SessionBus()

                try:
                    dbus_service = bus.get_object("org.autokey.Service", "/AppService")
                    dbus_service.show_configure(dbus_interface="org.autokey.Service")
                    sys.exit(0)
                except dbus.DBusException as e:
                    logging.exception("Error communicating with Dbus service")
                    self.show_error_dialog(
                        message="AutoKey is already running as pid {} but is not responding".format(pid),
                        details=str(e))
                    sys.exit(1)

        return True

    def init_global_hotkeys(self, configManager):
        logging.info("Initialise global hotkeys")
        configManager.toggleServiceHotkey.set_closure(self.toggle_service)
        configManager.configHotkey.set_closure(self.show_configure_signal.emit)

    def config_altered(self, persistGlobal):
        self.configManager.config_altered(persistGlobal)
        self.notifier.create_assign_context_menu()

    def hotkey_created(self, item):
        logging.debug("Created hotkey: %r %s", item.modifiers, item.hotKey)
        self.service.mediator.interface.grab_hotkey(item)

    def hotkey_removed(self, item):
        logging.debug("Removed hotkey: %r %s", item.modifiers, item.hotKey)
        self.service.mediator.interface.ungrab_hotkey(item)

    def path_created_or_modified(self, path):
        time.sleep(0.5)
        changed = self.configManager.path_created_or_modified(path)
        if changed and self.configWindow is not None:
            self.configWindow.config_modified()

    def path_removed(self, path):
        time.sleep(0.5)
        changed = self.configManager.path_removed(path)
        if changed and self.configWindow is not None:
            self.configWindow.config_modified()

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
        logging.info("Shutting down")
        self.closeAllWindows()
        self.notifier.hide()
        self.service.shutdown()
        self.monitor.stop()
        self.quit()
        os.remove(common.LOCK_FILE)  # TODO: maybe use atexit to remove the lock/pid file?
        logging.debug("All shutdown tasks complete... quitting")

    def notify_error(self, message):
        """
        Show an error notification popup.

        @param message: Message to show in the popup
        """
        self.exec_in_main(self.notifier.notify_error, message)

    def update_notifier_visibility(self):
        self.notifier.update_visible_status()

    def show_configure(self):
        """
        Show the configuration window, or deiconify (un-minimise) it if it's already open.
        """
        logging.info("Displaying configuration window")
        self.configWindow.show()
        self.configWindow.showNormal()
        self.configWindow.activateWindow()

    @staticmethod
    def show_error_dialog(message: str, details: str=None):
        """
        Convenience method for showing an error dialog.
        """
        # TODO: i18n
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

    def show_script_error(self):
        """
        Show the last script error (if any)
        """
        # TODO: i18n
        if self.service.scriptRunner.error:
            details = self.service.scriptRunner.error
            self.service.scriptRunner.error = ''
        else:
            details = "No error information available"
        QMessageBox.information(None, "View Script Error Details", details)

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
                logging.exception("callback event failed: %r %r", callback, args, exc_info=True)

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
