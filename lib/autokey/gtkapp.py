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
import autokey.dbus_service
import autokey.model.script
from . import common
common.USING_QT = False

import sys
import os.path
import subprocess
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

import autokey.argument_parser
from autokey import service, monitor
from autokey.gtkui.notifier import get_notifier
from autokey.gtkui.popupmenu import PopupMenu
from autokey.gtkui.configwindow import ConfigWindow
from autokey.gtkui.dialogs import ShowScriptErrorsDialog
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants
from autokey.logger import get_logger, configure_root_logger

logger = get_logger(__name__)

# TODO: this _ named function is initialised by gettext.install(), which is for
# localisation. It marks the string as a candidate for translation, but I don't
# know what else.
PROGRAM_NAME = _("AutoKey")
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

        #import testing (this wouldn't necessarily catch import errors that happen at the top of this file)
        # however those are not really the errors we are having issues with
        # based on this https://docs.python.org/3/py-modindex.html
        # it is safe to assume that a number of modules will always be available on any
        # normal python3 installation. This includes re, importlib, subprocess, shutil, sys, os etc. etc.
        # I guess we will still check for them however because it can't hurt?
        import importlib
        from shutil import which

        #these seem to be "default" python modules used by the program
        python_modules = ['argparse', 'collections', 'enum', 'faulthandler', 
            'gettext', 'inspect', 'itertools', 'logging', 'os', 'select', 'shlex',
            'shutil', 'subprocess', 'sys', 'threading', 'time', 'traceback', 'typing',
            'warnings', 'webbrowser']

        #modules that have to be installed
        modules = ['Xlib', 'dbus', 'pyinotify']

        #modules specific to gtk
        gtk_modules = ['gi']

        missing_modules = []
        for module in python_modules+modules+gtk_modules:
            spec = importlib.util.find_spec(module)
            if spec is None: #module has not been imported/found correctly
                missing_modules.append(module)

        #test for if command line programs used by AutoKey are installed on the system
        # visgrep comes from xautomation
        # import, png2pat from imagemagick.
        # ps is a command that most if not all systems will have installed fwik
        # zenity and xdg-open are pretty bog standard gnome/gtk stuff

        linux_programs = ['ps']

        programs = ['wmctrl']

        gtk_programs = ['zenity']

        missing_programs = []
        for program in linux_programs+programs+gtk_programs:
            if which(program) is None:
                # file not found by shell
                missing_programs.append(program)

        missing_optional_programs = []
        optional_programs = ['visgrep', 'import', 'png2pat', 'xte', 'wmctrl', 'xmousepos']
        for program in optional_programs:
            if which(program) is None:
                missing_optional_programs.append(program)

        if len(missing_programs)>0 or len(missing_modules)>0:
            error_message = ""
            for item in missing_programs:
                error_message+= "Program: "+item+"\n"
            for item in missing_modules:
                error_message+= "Python Module: "+item+"\n"

            #might not be required to enter and leave thread probably best practice to even tho the app exits immediately after.
            Gdk.threads_enter()
            self.show_error_dialog("AutoKey Requires the following programs or python modules to be installed to function properly", error_message)
            Gdk.threads_leave()
            sys.exit("missing programs or modules:\n"+str(missing_programs)+str(missing_modules))

        if len(missing_optional_programs)>0:
            error_message = ""
            for item in missing_optional_programs:
                error_message += "Program: "+item+"\n"

            #entering and leaving thread appears to be required to not hang main window
            Gdk.threads_enter()
            self.show_warning_dialog("Some optional dependencies for AutoKey were not detected on your system", error_message)
            Gdk.threads_leave()

        args = autokey.argument_parser.parse_args()

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

            configure_root_logger(args)
            if self.__verifyNotRunning():
                self.__createLockFile()

            self.initialise(args.show_config_window)

        except Exception as e:
            self.show_error_dialog(_("Fatal error starting AutoKey.\n") + str(e))
            logger.exception("Fatal error starting AutoKey: " + str(e))
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
                logger.debug("AutoKey is already running as pid %s", pid)
                bus = dbus.SessionBus()

                try:
                    dbusService = bus.get_object("org.autokey.Service", "/AppService")
                    dbusService.show_configure(dbus_interface="org.autokey.Service")
                    sys.exit(0)
                except dbus.DBusException as e:
                    logger.exception("Error communicating with Dbus service")
                    self.show_error_dialog(_("AutoKey is already running as pid %s but is not responding") % pid, str(e))
                    sys.exit(1)

        return True

    @staticmethod
    def _read_pid_from_lock_file() -> str:
        with open(common.LOCK_FILE, 'r') as lock_file:
            return lock_file.read()

    def initialise(self, configure):
        logger.info("Initialising application")
        self.monitor = monitor.FileMonitor(self)
        self.configManager = cm.create_config_manager_instance(self)
        self.service = service.Service(self)
        self.serviceDisabled = False

        # Initialise user code dir
        if self.configManager.userCodeDir is not None:
            sys.path.append(self.configManager.userCodeDir)

        try:
            self.service.start()
        except Exception as e:
            logger.exception("Error starting interface: " + str(e))
            self.serviceDisabled = True
            self.show_error_dialog(_("Error starting interface. Keyboard monitoring will be disabled.\n" +
                                     "Check your system/configuration."), str(e))

        self.notifier = get_notifier(self)
        self.configWindow = None
        self.monitor.start()

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.dbusService = autokey.dbus_service.AppService(self)

        if configure:
            self.show_configure()

    def init_global_hotkeys(self, configManager):
        logger.info("Initialise global hotkeys")
        configManager.toggleServiceHotkey.set_closure(self.toggle_service)
        configManager.configHotkey.set_closure(self.show_configure_async)

    def config_altered(self, persistGlobal):
        self.configManager.config_altered(persistGlobal)
        self.notifier.rebuild_menu()

    def hotkey_created(self, item):
        logger.debug("Created hotkey: %r %s", item.modifiers, item.hotKey)
        self.service.mediator.interface.grab_hotkey(item)

    def hotkey_removed(self, item):
        logger.debug("Removed hotkey: %r %s", item.modifiers, item.hotKey)
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
        logger.info("Shutting down")
        self.service.shutdown()
        self.monitor.stop()
        Gdk.threads_enter()
        Gtk.main_quit()
        Gdk.threads_leave()
        os.remove(common.LOCK_FILE)
        logger.debug("All shutdown tasks complete... quitting")

    def notify_error(self, error: autokey.model.script.ScriptErrorRecord):
        """
        Show an error notification popup.

        @param error: The error that occurred in a Script
        """
        message = "The script '{}' encountered an error".format(error.script_name)
        self.notifier.notify_error(message)

    def update_notifier_visibility(self):
        self.notifier.update_visible_status()

    def show_configure(self):
        """
        Show the configuration window, or deiconify (un-minimise) it if it's already open.
        """
        logger.info("Displaying configuration window")
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
        logger.info("Entering main()")
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

    def show_warning_dialog(self, message, details=None):
        """
        Another convenience method for showing info dialog
        """
        dlg = Gtk.MessageDialog(type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
                                 message_format=message)
        if details is not None:
            dlg.format_secondary_text(details)
        dlg.run()
        dlg.destroy()

    def show_script_error(self, parent):
        """
        Show the last script error (if any)
        """
        if self.service.scriptRunner.error_records:
            dlg = ShowScriptErrorsDialog(self)
            # revert the tray icon
            self.notifier.set_icon(cm.ConfigManager.SETTINGS[cm_constants.NOTIFICATION_ICON])
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
