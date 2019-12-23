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
import os.path
import logging
import logging.handlers
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

from autokey.baseapp import BaseApp
import autokey.argument_parser
from autokey import service, monitor
from autokey.gtkui.notifier import get_notifier
from autokey.gtkui.popupmenu import PopupMenu
from autokey.gtkui.configwindow import ConfigWindow
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants


# TODO: this _ named function is initialised by gettext.install(), which is for
# localisation. It marks the string as a candidate for translation, but I don't
# know what else.
PROGRAM_NAME = _("AutoKey")
DESCRIPTION = _("Desktop automation utility")
COPYRIGHT = _("(c) 2008-2011 Chris Dekter")


class UI:
    """
    Main UI class; starting and stopping of the application is controlled
    from here, together with some interactions from the tray icon.
    """

    def __init__(self):
        GLib.threads_init()
        Gdk.threads_init()
        self.app = BaseApp(self)
        self.app.initialise(self.app.args.show_config_window)

    def initialise(self):
        self.notifier = get_notifier(self.app)


    def main(self):
        logging.info("Entering main()")
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()


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

    def notify_error(self, message):
        """
        Show an error notification popup.

        @param message: Message to show in the popup
        """
        self.notifier.notify_error(message)

    def update_notifier_visibility(self):
        self.notifier.update_visible_status()


