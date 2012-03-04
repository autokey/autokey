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

import common
common.USING_QT = False

import sys, traceback, os.path, signal, logging, logging.handlers, subprocess, optparse, time
import gettext, gtk, dbus, dbus.service, dbus.mainloop.glib
gettext.install("autokey")

import service, monitor
from gtkui.notifier import get_notifier
from gtkui.popupmenu import PopupMenu
from gtkui.configwindow import ConfigWindow
from gtkui.abbrselector import AbbrSelectorDialog
from configmanager import *
from common import *

PROGRAM_NAME = _("AutoKey")
DESCRIPTION = _("Desktop automation utility")
COPYRIGHT = _("(c) 2008-2011 Chris Dekter")


class Application:
    """
    Main application class; starting and stopping of the application is controlled
    from here, together with some interactions from the tray icon.
    """
    
    def __init__(self):
        gtk.gdk.threads_init()
        
        p = optparse.OptionParser()
        p.add_option("-l", "--verbose", help="Enable verbose logging", action="store_true", default=False)
        p.add_option("-c", "--configure", help="Show the configuration window on startup", action="store_true", default=False)
        options, args = p.parse_args()
        
        try:
            # Create configuration directory
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
                
            # Initialise logger
            rootLogger = logging.getLogger()
            
            if options.verbose:
                rootLogger.setLevel(logging.DEBUG)
                handler = logging.StreamHandler(sys.stdout)
            else:
                rootLogger.setLevel(logging.INFO)
                handler = logging.handlers.RotatingFileHandler(LOG_FILE, 
                                        maxBytes=MAX_LOG_SIZE, backupCount=MAX_LOG_COUNT)
            
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            rootLogger.addHandler(handler)
            
            
            if self.__verifyNotRunning():
                self.__createLockFile()
                
            self.initialise(options.configure)
            
        except Exception, e:
            self.show_error_dialog(_("Fatal error starting AutoKey.\n") + str(e))
            logging.exception("Fatal error starting AutoKey: " + str(e))
            sys.exit(1)
            
            
    def __createLockFile(self):
        f = open(LOCK_FILE, 'w')
        f.write(str(os.getpid()))
        f.close()
        
    def __verifyNotRunning(self):
        if os.path.exists(LOCK_FILE):
            f = open(LOCK_FILE, 'r')
            pid = f.read()
            f.close()
            
            # Check that the found PID is running and is autokey
            p = subprocess.Popen(["ps", "-p", pid, "-o", "command"], stdout=subprocess.PIPE)
            p.wait()
            output = p.stdout.read()
            if "autokey" in output:
                logging.debug("AutoKey is already running as pid %s", pid)
                bus = dbus.SessionBus()
                
                try:
                    dbusService = bus.get_object("org.autokey.Service", "/AppService")
                    dbusService.show_configure(dbus_interface = "org.autokey.Service")
                    sys.exit(0)
                except dbus.DBusException, e:
                    logging.exception("Error communicating with Dbus service")
                    self.show_error_dialog(_("AutoKey is already running as pid %s but is not responding") % pid, str(e))
                    sys.exit(1)
         
        return True

    def main(self):
        gtk.main()

    def initialise(self, configure):
        logging.info("Initialising application")
        self.monitor = monitor.FileMonitor(self)
        self.configManager = get_config_manager(self)
        self.service = service.Service(self)
        self.serviceDisabled = False
        
        # Initialise user code dir
        if self.configManager.userCodeDir is not None:
            sys.path.append(self.configManager.userCodeDir)
                
        try:
            self.service.start()
        except Exception, e:
            logging.exception("Error starting interface: " + str(e))
            self.serviceDisabled = True
            self.show_error_dialog(_("Error starting interface. Keyboard monitoring will be disabled.\n" +
                                    "Check your system/configuration."), str(e))
        
        self.notifier = get_notifier(self)
        self.configWindow = None
        self.abbrPopup = None
        self.monitor.start()
        
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.dbusService = common.AppService(self)
        
        if ConfigManager.SETTINGS[IS_FIRST_RUN] or configure:
            ConfigManager.SETTINGS[IS_FIRST_RUN] = False
            self.show_configure()
            
    def init_global_hotkeys(self, configManager):
        logging.info("Initialise global hotkeys")
        configManager.toggleServiceHotkey.set_closure(self.toggle_service)
        configManager.configHotkey.set_closure(self.show_configure_async)
        configManager.showPopupHotkey.set_closure(self.show_abbr_async)        
        
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
            #if doReload:
            #    self.configWindow.hide()
            #    self.show_configure_async()
        
    def path_removed(self, path):
        time.sleep(0.5)
        changed = self.configManager.path_removed(path)        
        if changed and self.configWindow is not None: 
            self.configWindow.config_modified()
            #if doReload:
            #    self.configWindow.hide()
            #    self.configWindow = None
            #    self.show_configure()
        
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
        gtk.gdk.threads_enter()
        gtk.main_quit()
        gtk.gdk.threads_leave()
        os.remove(LOCK_FILE)
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
        gtk.gdk.threads_enter()
        self.show_configure()
        gtk.gdk.threads_leave()

    def show_abbr_selector(self):
        """
        Show the abbreviation autocompletion popup.
        """
        if self.abbrPopup is None:
            logging.info("Displaying abbreviation popup")
            self.abbrPopup = AbbrSelectorDialog(self)
            self.abbrPopup.present()
            
    def show_abbr_async(self):
        gtk.gdk.threads_enter()
        self.show_abbr_selector()
        gtk.gdk.threads_leave()
                
    def main(self):
        logging.info("Entering main()")
        gtk.main()
            
    def show_error_dialog(self, message, details=None):
        """
        Convenience method for showing an error dialog.
        """
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
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
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
                                     message_format=self.service.scriptRunner.error)
            self.service.scriptRunner.error = ''
        else:
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
                                     message_format=_("No error information available"))
        
        dlg.set_title(_("View script error"))
        dlg.set_transient_for(parent) 
        dlg.run()
        dlg.destroy()        
        
    def show_popup_menu(self, folders=[], items=[], onDesktop=True, title=None):
        self.menu = PopupMenu(self.service, folders, items, onDesktop, title)
        self.menu.show_on_desktop()
    
    def hide_menu(self):
        self.menu.remove_from_desktop()
    
