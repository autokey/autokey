#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2008 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


import pygtk
pygtk.require("2.0")
import sys, gtk, traceback, os.path, signal, logging, logging.handlers
import expansionservice, ui, configurationmanager
from configurationmanager import *

CONFIG_DIR = os.path.expanduser("~/.config/autokey")
LOCK_FILE = CONFIG_DIR + "/autokey.pid"
LOG_FILE = CONFIG_DIR + "/autokey.log"
MAX_LOG_SIZE = 5 * 1024 * 1024 # 5 megabytes
MAX_LOG_COUNT = 3
LOG_FORMAT = "%(levelname)s - %(name)s - %(message)s"

class AutoKeyApplication:
    """
    Main application class; starting and stopping of the application is controlled
    from here, together with some interactions from the tray icon.
    """

    def __init__(self, verbose, configure):
        # Initialise logger
        rootLogger = logging.getLogger()
        
        if verbose:
            rootLogger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stdout)
        else:           
            rootLogger.setLevel(logging.INFO)
            handler = logging.handlers.RotatingFileHandler(LOG_FILE, 
                                    maxBytes=MAX_LOG_SIZE, backupCount=MAX_LOG_COUNT)
        
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        rootLogger.addHandler(handler)
            
        
        
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            if os.path.exists(LOCK_FILE):
                f = open(LOCK_FILE, 'r')
                pid = f.read()
                f.close()
                if os.path.exists("/proc/" + pid):
                    logging.error("AutoKey is already running - exiting")
                    self.show_error_dialog("AutoKey is already running (pid %s)" % pid)
                    sys.exit(1)
                else:
                    self.__createLockFile()
            else:
                self.__createLockFile()
                
            self.initialise(configure)
            
        except Exception, e:
            self.show_error_dialog("Fatal error starting AutoKey.\n" + str(e))
            logging.exception("Fatal error starting AutoKey: " + str(e))
            sys.exit(1)
            
    def __createLockFile(self):
        f = open(LOCK_FILE, 'w')
        f.write(str(os.getpid()))
        f.close()
        
    def initialise(self, configure):
        logging.info("Initialising application")
        self.configManager = configurationmanager.get_config_manager(self)
        self.service = expansionservice.ExpansionService(self)
        self.serviceDisabled = False
        
        try:
            self.service.start()
        except Exception, e:
            logging.exception("Error starting interface: " + str(e))
            self.serviceDisabled = True
            self.show_error_dialog("Error starting interface. Keyboard monitoring will be disabled.\n" +
                                    "Check your system/configuration.\n" + str(e))
        
        signal.signal(signal.SIGTERM, self.shutdown)
        
        #self.init_global_hotkeys()
        self.notifier = ui.Notifier(self)
        self.configureWindow = None
        self.abbrPopup = None
        
        if ConfigurationManager.SETTINGS[IS_FIRST_RUN] or configure:
            ConfigurationManager.SETTINGS[IS_FIRST_RUN] = False
            self.show_configure()
            
    def init_global_hotkeys(self, configManager):
        logging.info("Initialise global hotkeys")
        configManager.toggleServiceHotkey.set_closure(self.toggle_service)
        configManager.configHotkey.set_closure(self.show_configure)
        configManager.showPopupHotkey.set_closure(self.show_abbr_selector)
        
    def unpause_service(self):
        """
        Unpause the expansion service (start responding to keyboard and mouse events).
        """
        self.notifier.set_tooltip(ui.TOOLTIP_RUNNING)
        self.service.unpause()
    
    def pause_service(self):
        """
        Pause the expansion service (stop responding to keyboard and mouse events).
        """
        self.notifier.set_tooltip(ui.TOOLTIP_PAUSED)
        self.service.pause()
        
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
        logging.info("Shutting down")
        self.service.shutdown()
        os.remove(LOCK_FILE)
            
    def show_notify(self, message, isError=False, details=''):
        """
        Show a libnotify popup.
        
        @param message: Message to show in the popup
        @param isError: Whether the message is an error (shows with an error icon)
        @param details: Error details, which the user can view in a dialog by clicking
        the "View Details" button.
        """
        self.notifier.show_notify(message, isError, details)
        
    def show_configure(self):
        """
        Show the configuration window, or deiconify (un-minimise) it if it's already open.
        """
        logging.info("Displaying configuration window")
        if self.configureWindow is None:
            self.configureWindow = ui.ConfigurationWindow(self)
            self.configureWindow.show()
        else:    
            self.configureWindow.deiconify()
            
    def show_abbr_selector(self):
        """
        Show the abbreviation autocompletion popup.
        """
        if self.abbrPopup is None:
            logging.info("Displaying abbreviation popup")
            self.abbrPopup = ui.AbbreviationSelectorDialog(self.service)
            self.abbrPopup.present()
                
    def main(self):
        logging.info("Entering main()")
        gtk.main()
            
    def show_error_dialog(self, message):
        """
        Convenience method for showing an error dialog.
        """
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                                 message_format=message)
        dlg.run()
        dlg.destroy()

if __name__ == "__main__":
    gtk.gdk.threads_init()
    a = AutoKeyApplication()
    try:
        a.main()
    except KeyboardInterrupt:
        a.shutdown()
    sys.exit(0)