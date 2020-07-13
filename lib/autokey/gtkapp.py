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
common.USING_QT = False

import sys
import traceback
import os.path
import signal
import logging
import logging.handlers
import subprocess
import optparse
import time
import threading

import gettext
import dbus
import dbus.service
import dbus.mainloop.glib

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib

gettext.install("autokey")


from autokey import service, monitor
from autokey.gtkui.notifier import get_notifier
from autokey.gtkui.popupmenu import PopupMenu
from autokey.gtkui.configwindow import ConfigWindow
from autokey import configmanager as cm

PROGRAM_NAME = _("AutoKey")  # TODO: where does this _ named function come from? It must be one of those from x import *
DESCRIPTION = _("Desktop automation utility")
COPYRIGHT = _("(c) 2008-2011 Chris Dekter")


class Application:
    """
    Main application class; starting and stopping of the application is controlled
    from here, together with some interactions from the tray icon.
    """

    def __init__(self):
        GLib.threads_init()
        Gdk.threads_init()

        p = optparse.OptionParser()
        p.add_option("-l", "--verbose", help="Enable verbose logging", action="store_true", default=False)
        p.add_option("-c", "--configure", help="Show the configuration window on startup", action="store_true", default=False)
        options, args = p.parse_args()

        try:
            # Create configuration directory
            if not os.path.exists(common.CONFIG_DIR):
                os.makedirs(common.CONFIG_DIR)
            # Create data directory (for log file)
            if not os.path.exists(common.DATA_DIR):
                os.makedirs(common.DATA_DIR)
            # Create run directory (for lock file)
            if not os.path.exists(common.RUN_DIR):
                os.makedirs(common.RUN_DIR)

            # Initialise logger
            rootLogger = logging.getLogger()

            if options.verbose:
                rootLogger.setLevel(logging.DEBUG)
                handler = logging.StreamHandler(sys.stdout)
            else:
                rootLogger.setLevel(logging.INFO)
                handler = logging.handlers.RotatingFileHandler(common.LOG_FILE,
                                        maxBytes=common.MAX_LOG_SIZE, backupCount=common.MAX_LOG_COUNT)

            handler.setFormatter(logging.Formatter(common.LOG_FORMAT))
            rootLogger.addHandler(handler)

            if self.__verifyNotRunning():
                self.__createLockFile()

            self.initialise(options.configure)

        except Exception as e:
            traceback.print_exc()
            self.show_error_dialog(_("Fatal error starting AutoKey.\n") + str(e))
            logging.exception("Fatal error starting AutoKey: " + str(e))
            sys.exit(1)

    def __createLockFile(self):
        with open(common.LOCK_FILE, "w") as lock_file:
            lock_file.write(str(os.getpid()))

    def __verifyNotRunning(self):
        if os.path.exists(common.LOCK_FILE):
            pid = Application._read_pid_from_lock_file()

            # Check that the found PID is running and is autokey
            with subprocess.Popen(["ps", "-p", pid, "-o", "command"], stdout=subprocess.PIPE) as p:
                output = p.communicate()[0]

            if "autokey" in output.decode():
                logging.debug("AutoKey is already running as pid %s", pid)
                bus = dbus.SessionBus()

                try:
                    dbusService = bus.get_object("org.autokey.Service", "/AppService")
                    dbusService.show_configure(dbus_interface="org.autokey.Service")
                    sys.exit(0)
                except dbus.DBusException as e:
                    logging.exception("Error communicating with Dbus service")
                    self.show_error_dialog(_("AutoKey is already running as pid %s but is not responding") % pid, str(e))
                    sys.exit(1)

        return True

    @staticmethod
    def _read_pid_from_lock_file() -> str:
        with open(common.LOCK_FILE, 'r') as lock_file:
            return lock_file.read()

    def initialise(self, configure):
        logging.info("Initialising application")
        self.monitor = monitor.FileMonitor(self)
        self.configManager = cm.get_config_manager(self)
        self.service = service.Service(self)
        self.serviceDisabled = False

        # Initialise user code dir
        if self.configManager.userCodeDir is not None:
            sys.path.append(self.configManager.userCodeDir)

        try:
            self.service.start()
        except Exception as e:
            logging.exception("Error starting interface: " + str(e))
            self.serviceDisabled = True
            self.show_error_dialog(_("Error starting interface. Keyboard monitoring will be disabled.\n" +
                                    "Check your system/configuration."), str(e))

        self.notifier = get_notifier(self)
        self.configWindow = None
        self.monitor.start()

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.dbusService = common.AppService(self)

        if configure:
            self.show_configure()

    def init_global_hotkeys(self, configManager):
        logging.info("Initialise global hotkeys")
        configManager.toggleServiceHotkey.set_closure(self.toggle_service)
        configManager.configHotkey.set_closure(self.show_configure_async)

    def config_altered(self, persistGlobal):
        self.configManager.config_altered(persistGlobal)
        self.notifier.rebuild_menu()

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
        self.notifier.update_tool_tip()

    def pause_service(self):
        """
        Pause the expansion service (stop responding to keyboard and mouse events).
        """
        self.service.pause()
        self.notifier.update_tool_tip()

    def toggle_service(self):
        """
        Convenience method for toggling the expansion service on or off.
        """
        if self.service.is_running():
            self.pause_service()
        else:
            self.unpause_service()

    def shutdown(self):
        """
        Shut down the entire application.
        """
        if self.configWindow is not None:
            if self.configWindow.promptToSave():
                return

            self.configWindow.hide()

        self.notifier.hide_icon()

        t = threading.Thread(target=self.__completeShutdown)
        t.start()

    def __completeShutdown(self):
        logging.info("Shutting down")
        self.service.shutdown()
        self.monitor.stop()
        Gdk.threads_enter()
        Gtk.main_quit()
        Gdk.threads_leave()
        os.remove(common.LOCK_FILE)
        logging.debug("All shutdown tasks complete... quitting")

    def notify_error(self, message):
        """
        Show an error notification popup.

        @param message: Message to show in the popup
        """
        self.notifier.notify_error(message)

    def update_notifier_visibility(self):
        self.notifier.update_visible_status()

    def show_configure(self):
        """
        Show the configuration window, or deiconify (un-minimise) it if it's already open.
        """
        logging.info("Displaying configuration window")
        if self.configWindow is None:
            self.configWindow = ConfigWindow(self)
            self.configWindow.show()
        else:
            self.configWindow.deiconify()

    def show_configure_async(self):
        Gdk.threads_enter()
        self.show_configure()
        Gdk.threads_leave()

    def main(self):
        logging.info("Entering main()")
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

    def show_error_dialog(self, message, details=None):
        """
        Convenience method for showing an error dialog.
        """
        dlg = Gtk.MessageDialog(type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                 message_format=message)
        if details is not None:
            dlg.format_secondary_text(details)
        dlg.run()
        dlg.destroy()

    def show_script_error(self, parent):
        """
        Show the last script error (if any)
        """
        if self.service.scriptRunner.error != '':
            dlg = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                     message_format=self.service.scriptRunner.error)
            self.service.scriptRunner.error = ''
            # revert the tray icon
            self.notifier.set_icon(cm.ConfigManager.SETTINGS[cm.NOTIFICATION_ICON])
            self.notifier.errorItem.hide()
            self.notifier.update_visible_status()

        else:
            dlg = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                     message_format=_("No error information available"))

        dlg.set_title(_("View script error"))
        dlg.set_transient_for(parent)
        dlg.run()
        dlg.destroy()

    def show_popup_menu(self, folders: list=None, items: list=None, onDesktop=True, title=None):
        if items is None:
            items = []
        if folders is None:
            folders = []
        self.menu = PopupMenu(self.service, folders, items, onDesktop, title)
        self.menu.show_on_desktop()

    def hide_menu(self):
        self.menu.remove_from_desktop()
