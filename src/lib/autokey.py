#!/usr/bin/env python

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
import sys, gtk, traceback, os.path
import expansionservice, ui
from configurationmanager import *

LOCK_FILE = "../../config/autokey.pid"

class AutoKeyApplication:

    def __init__(self):
        try:
            if os.path.exists(LOCK_FILE):
                f = open(LOCK_FILE, 'r')
                pid = f.read()
                f.close()
                if os.path.exists("/proc/" + pid):
                    self.show_error_dialog("AutoKey is already running (pid %s)" % pid)
                    sys.exit(1)
                else:
                    self.__createLockFile()
            else:
                self.__createLockFile()
                
            self.initialise()
            
        except Exception, e:
            self.show_error_dialog("Fatal error starting AutoKey.\n" + str(e))
            traceback.print_exc()
            sys.exit(1)
            
    def __createLockFile(self):
        f = open(LOCK_FILE, 'w')
        f.write(str(os.getpid()))
        f.close()
        
    def initialise(self):
        self.service = expansionservice.ExpansionService()
        self.service.start()
        
        self.notifier = ui.Notifier(self)
        self.configureWindow = None
        
        if ConfigurationManager.SETTINGS[IS_FIRST_RUN]:
            ConfigurationManager.SETTINGS[IS_FIRST_RUN] = False
            self.show_configure() 
        
    def unpause_service(self):
        self.service.unpause()
    
    def pause_service(self):
        self.service.pause()
        
    def shutdown(self):
        self.service.shutdown()
        os.remove(LOCK_FILE)
            
    def show_notify(self, message, isError=False, details=''):
        self.notifier.show_notify(message, isError, details)
        
    def show_configure(self):
        if self.configureWindow is None:
            self.configureWindow = ui.ConfigurationWindow(self)
            self.configureWindow.show()
        else:    
            self.configureWindow.deiconify()
        
    def main(self):
        gtk.main()        
            
    def show_error_dialog(self, message):
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                                 message_format=message)
        dlg.run()
        dlg.destroy()

if __name__ == "__main__":
    gtk.gdk.threads_init()
    a = AutoKeyApplication()
    a.main()