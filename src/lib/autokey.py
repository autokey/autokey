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


import sys, traceback, os.path, signal, logging, logging.handlers, subprocess, Queue
from PyKDE4.kdecore import KCmdLineArgs, KCmdLineOptions, KAboutData, ki18n, i18n
from PyKDE4.kdeui import KMessageBox, KApplication
from PyQt4.QtCore import SIGNAL, Qt, QObject, QEvent
from PyQt4.QtGui import QCursor

import service, ui.notifier, ui.popupmenu
from configmanager import *

CONFIG_DIR = os.path.expanduser("~/.config/autokey")
LOCK_FILE = CONFIG_DIR + "/autokey.pid"
LOG_FILE = CONFIG_DIR + "/autokey.log"
MAX_LOG_SIZE = 5 * 1024 * 1024 # 5 megabytes
MAX_LOG_COUNT = 3
LOG_FORMAT = "%(levelname)s - %(name)s - %(message)s"

APP_NAME = "AutoKey"
CATALOG = ""
PROGRAM_NAME = ki18n("AutoKey")
VERSION = "0.61.3"
DESCRIPTION = ki18n("Desktop automation utility")
LICENSE = KAboutData.License_GPL_V3
COPYRIGHT = ki18n("(c) 2009 Chris Dekter")
TEXT = ki18n("")
HOMEPAGE  = "http://autokey.sourceforge.net/"
BUG_EMAIL = "cdekter@gmail.com"



class Application:
    """
    Main application class; starting and stopping of the application is controlled
    from here, together with some interactions from the tray icon.
    """
    
    def __init__(self):
        
        aboutData = KAboutData(APP_NAME, CATALOG, PROGRAM_NAME, VERSION, DESCRIPTION,
                                    LICENSE, COPYRIGHT, TEXT, HOMEPAGE, BUG_EMAIL)

        aboutData.addAuthor(ki18n("Chris Dekter"), ki18n("Developer"), "cdekter@gmail.com", "")
        aboutData.addAuthor(ki18n("Sam Peterson"), ki18n("Original developer"), "peabodyenator@gmail.com", "")
        aboutData.setProgramIconName(ui.notifier.ICON_FILE)
        
        KCmdLineArgs.init(sys.argv, aboutData)
        options = KCmdLineOptions()
        options.add("l").add("verbose", ki18n("Enable verbose logging"))
        options.add("c").add("configure", ki18n("Show the configuration window on startup"))
        KCmdLineArgs.addCmdLineOptions(options)
        args = KCmdLineArgs.parsedArgs()
        
        
        self.app = KApplication()
        
        try:
            # Create configuration directory
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            # Initialise logger
            rootLogger = logging.getLogger()
            
            if args.isSet("verbose"):
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
                
            self.initialise(args.isSet("configure"))
            
        except Exception, e:
            self.show_error_dialog(i18n("Fatal error starting AutoKey.\n") + str(e))
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
            output = p.stdout.readlines()
            if len(output) > 1:
                # process exists
                if "autokey" in output[1]:
                    logging.error("AutoKey is already running - exiting")
                    self.show_error_dialog(i18n("AutoKey is already running as pid: ") + pid)
                    sys.exit(1)
         
        return True

    def main(self):
        self.app.exec_()

    def initialise(self, configure):
        logging.info("Initialising application")
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
            self.show_error_dialog(i18n("Error starting interface. Keyboard monitoring will be disabled.\n" +
                                    "Check your system/configuration."), str(e))
        
        self.notifier = ui.notifier.Notifier(self)
        self.configWindow = None
        
        if ConfigManager.SETTINGS[IS_FIRST_RUN] or configure:
            ConfigManager.SETTINGS[IS_FIRST_RUN] = False
            self.show_configure()
            
        self.handler = CallbackEventHandler()
            
    def init_global_hotkeys(self, configManager):
        logging.info("Initialise global hotkeys")
        configManager.toggleServiceHotkey.set_closure(self.toggle_service)
        configManager.configHotkey.set_closure(self.show_configure_async)
        
    def config_altered(self):
        self.configManager.config_altered()
        self.notifier.build_menu()
        
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
        logging.info("Shutting down")
        self.app.closeAllWindows()
        self.service.shutdown()
        self.app.quit()
        os.remove(LOCK_FILE)
            
    def show_notify(self, message, isError=False, details=''):
        """
        Show a notification popup.
        
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
        try:
            self.configWindow.showNormal()
            self.configWindow.activateWindow()            
        except:
            self.configWindow = ui.configwindow.ConfigWindow(self)
            self.configWindow.show()
            
    def show_configure_async(self):
        self.exec_in_main(self.show_configure)

    def show_error_dialog(self, message, details=None):
        """
        Convenience method for showing an error dialog.
        """
        if details is None:
            KMessageBox.error(None, message)
        else:
            KMessageBox.detailedError(None, message, details)
            
    def show_script_error(self):
        """
        Show the last script error (if any)
        """
        if self.service.scriptRunner.error != '':
            KMessageBox.information(None, self.service.scriptRunner.error, i18n("View Script Error Details"))
            self.service.scriptRunner.error = ''
        else:
            KMessageBox.information(None, i18n("No error information available"), i18n("View Script Error Details"))
        
    def show_popup_menu(self, folders=[], items=[], onDesktop=True, title=None):
        self.exec_in_main(self.__createMenu, folders, items, onDesktop, title)
        
    def hide_menu(self):
        self.exec_in_main(self.menu.hide)
        
    def __createMenu(self, folders, items, onDesktop, title):
        self.menu = ui.popupmenu.PopupMenu(self.service, folders, items, onDesktop, title)
        self.menu.popup(QCursor.pos())
        
    def exec_in_main(self, callback, *args):
        self.handler.postEventWithCallback(callback, *args)
        
        
class CallbackEventHandler(QObject):

    def __init__(self):
        QObject.__init__(self)
        self.queue = Queue.Queue()

    def customEvent(self, event):
        while True:
            try:
                callback, args = self.queue.get_nowait()
            except Queue.Empty:
                break
            try:
                callback(*args)
            except Exception:
                logging.warn("callback event failed: %r %r", callback, args, exc_info=True)

    def postEventWithCallback(self, callback, *args):
        self.queue.put((callback, args))
        app = KApplication.kApplication()
        app.postEvent(self, QEvent(QEvent.User))
