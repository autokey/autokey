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


import atexit
import sys
import os.path
import dbus
import dbus.mainloop.glib
import signal
import subprocess
import hashlib
from typing import NamedTuple, Iterable
import re

import autokey.model.script
from autokey import common

from autokey import service, monitor

import autokey.argument_parser
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants
import autokey.dbus_service

from autokey.logger import get_logger, configure_root_logger
import autokey.UI_common_functions as UI_common

import autokey.wayland_checks as awc

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
        if awc.waylandChecks() :
            logger.debug('autokey.waylandChecks() succeeded')
        else:
            logger.error('autokey.waylandChecks() failed')
            sys.exit(1)
        self.__warn_about_missing_requirements()
        AutokeyApplication.create_storage_directories()
        if self.__verify_not_running():
            AutokeyApplication.create_lock_file()
            atexit.register(os.remove, common.LOCK_FILE)
			
        self.__initialise_services()
        self.__add_user_code_dir_to_path()
        self.__create_DBus_service()
        self.__register_ctrlc_handler()

        # process command line commands here?
        try:
            self.usage_statistics()
        except Exception as e:
            logger.error(f"Usage statistics failure: {e}")

        logger.info("Autokey application services ready")

    def usage_statistics(self):
        def get_digest(value):
            return hashlib.md5(str(value).encode()).hexdigest()[0:8]

        logger.info("----- AutoKey Usage Statistics -----")
        for item in self.configManager.allItems:
            if type(item) is autokey.model.phrase.Phrase:
                # logger.info(item.description, item.usageCount, item.phrase)
                logger.info(f"Phrase: {get_digest(item.description)}, Usage Count: {item.usageCount} {self.getMacroUsage(item.phrase)}")
            elif type(item) is autokey.model.script.Script:
                logger.info(f"Script: {get_digest(item.description)}, Usage Count: {item.usageCount} {self.getAPIUsage(item.code)}")
        
        for item in self.configManager.allFolders:
            
            logger.info(f"Folder: {get_digest(item.title)}, Usage Count: {item.usageCount}")

        logger.info("----- AutoKey Usage Statistics -----")

    def getAPIUsage(self, code):
        api_modules = ["engine","keyboard","mouse","highlevel","store","dialog","clipboard","system","window"]

        reg = re.compile("("+"|".join(api_modules)+")\\.(\\w*)\\(")

        results = re.findall(reg, code)

        # Create an empty dictionary to store the counts
        count_dict = {}

        # Loop through the list and count each item
        for item in results:
            if item in count_dict:
                count_dict[item] += 1
            else:
                count_dict[item] = 1

        return count_dict
    
    def getMacroUsage(self, phrase):
        macros = ["cursor", "script", "system", "date", "file", "clipboard"]

        reg = re.compile("<("+"|".join(macros)+")")

        results = re.findall(reg, phrase)
        return results


    def __create_DBus_service(self):
        logger.info("Creating DBus service")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.dbusService = autokey.dbus_service.AppService(self)
        logger.debug("DBus service created")

    def __add_user_code_dir_to_path(self):
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

    def __try_start_monitor(self):
        try:
            self.monitor.start()
        except Exception as e:
            logger.exception("Error starting file monitor. Error: " + str(e))
            self.UI.show_error_dialog("Error starting file monitor. Error: " + str(e))

    def ctrlc_interrupt_handler(self, signal, frame):
        logger.info("Recieved keyboard interrupt. Shutting down")
        self.UI.shutdown()

    def __register_ctrlc_handler(self):
        """
        Handles keyboard interrupts (ctrl-c) when run from command line.
        """
        signal.signal(signal.SIGINT, self.ctrlc_interrupt_handler)

    def __verify_not_running(self):
        if self.__is_existing_running_autokey():
            self.__try_to_show_existing_autokey_UI_and_exit()
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
            pid = AutokeyApplication.read_pid_from_lock_file()
            self.__exit_if_lock_file_corrupt(pid)
            pid_is_a_running_autokey = "autokey" in self.__get_process_details(pid)
            if pid_is_a_running_autokey:
                logger.debug("AutoKey is already running as pid %s", pid)
                return True
        return False

    @staticmethod
    def read_pid_from_lock_file() -> str:
        with open(common.LOCK_FILE, "r") as lock_file:
            pid = lock_file.read()
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
        logger.debug("Created hotkey: %r %s", item.modifiers, item.hotKey)
        self.service.mediator.grab_hotkey(item)

    def hotkey_removed(self, item):
        logger.debug("Removed hotkey: %r %s", item.modifiers, item.hotKey)
        self.service.mediator.ungrab_hotkey(item)

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
        if self.service.is_running():
            self.pause_service()
        else:
            self.unpause_service()

    def autokey_shutdown(self):
        """
        Shut down the entire application.
        """
        logger.debug("Shutting down service and file monitor...")
        self.monitor.stop()
        self.service.shutdown()
        self.dbusService.unregister()
        logger.debug("Finished shutting down service and file monitor...")
