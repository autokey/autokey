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

import pynotify, gobject, gtk, gettext
import popupmenu, abbrselector
from autokey.configmanager import *
from autokey import common

gettext.install("autokey")

TOOLTIP_RUNNING = _("AutoKey - running")
TOOLTIP_PAUSED = _("AutoKey - paused")

STATUS_ICON_FILE = "/usr/share/pixmaps/akicon.png"

def gthreaded(f):
    
    def wrapper(*args):
        gtk.gdk.threads_enter()
        f(*args)
        gtk.gdk.threads_leave()
        
    wrapper.__name__ = f.__name__
    wrapper.__dict__ = f.__dict__
    wrapper.__doc__ = f.__doc__
    return wrapper

class Notifier(gobject.GObject):
    """
    Encapsulates all functionality related to the notification icon, notifications, and tray menu.
    """

    __gsignals__ = { "show-notify" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                      (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)) }
    
    def __init__(self, autokeyApp):
        gobject.GObject.__init__(self)
        pynotify.init("AutoKey")
        self.app = autokeyApp
        self.configManager = autokeyApp.service.configManager
        
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            self.icon = gtk.status_icon_new_from_file(STATUS_ICON_FILE)
            self.update_tool_tip()
            self.icon.connect("popup_menu", self.on_popup_menu)
            self.icon.connect("activate", self.on_show_configure)
            
            self.connect("show-notify", self.on_show_notify)  
            
    def show_notify(self, message, isError=False, details=''):
        if isError:
            self.emit("show-notify", message, details, gtk.STOCK_DIALOG_ERROR)
        else:
            self.emit("show-notify", message, details, gtk.STOCK_DIALOG_INFO)
            
    def update_tool_tip(self):
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            if ConfigManager.SETTINGS[SERVICE_RUNNING]:
                self.icon.set_tooltip(TOOLTIP_RUNNING)
                #self.toggleAction.setChecked(True)
            else:
                self.icon.set_tooltip(TOOLTIP_PAUSED)
                #self.toggleAction.setChecked(False)
        
    # Signal Handlers ----
    
    #def on_activate(self, widget, data=None):
    #    self.app.show_abbr_selector()
        
    def on_popup_menu(self, status_icon, button, activate_time, data=None):
        # Main Menu items
        enableMenuItem = gtk.CheckMenuItem(_("Enable Expansions"))
        enableMenuItem.set_active(self.app.service.is_running())
        enableMenuItem.set_sensitive(not self.app.serviceDisabled)
        
        configureMenuItem = gtk.ImageMenuItem(_("Configure"))
        configureMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_MENU))
        
        removeMenuItem = gtk.ImageMenuItem(_("Remove icon"))
        removeMenuItem.set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU))
        
        quitMenuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
                
        # Menu signals
        enableMenuItem.connect("toggled", self.on_enable_toggled)
        configureMenuItem.connect("activate", self.on_show_configure)
        removeMenuItem.connect("activate", self.on_remove_icon)
        quitMenuItem.connect("activate", self.on_destroy_and_exit)
        
        # Get phrase folders to add to main menu
        folders = []
        items = []

        for folder in self.configManager.allFolders:
            if folder.showInTrayMenu:
                folders.append(folder)
        
        for item in self.configManager.allItems:
            if item.showInTrayMenu:
                items.append(item)
                    
        # Construct main menu
        menu = popupmenu.PopupMenu(self.app.service, folders, items, False)
        if len(items) > 0:
            menu.append(gtk.SeparatorMenuItem())
        menu.append(enableMenuItem)
        menu.append(configureMenuItem)
        menu.append(removeMenuItem)
        menu.append(quitMenuItem)
        menu.show_all()
        menu.popup(None, None, None, button, activate_time)
        
    def on_enable_toggled(self, widget, data=None):
        if widget.active:
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_show_configure(self, widget, data=None):
        self.app.show_configure()
            
    def on_remove_icon(self, widget, data=None):
        self.icon.set_visible(False)
        ConfigManager.SETTINGS[SHOW_TRAY_ICON] = False
                
    def on_destroy_and_exit(self, widget, data=None):
        self.app.shutdown()
        
    @gthreaded
    def on_show_notify(self, widget, message, details, iconName):
        n = pynotify.Notification("Autokey", message, iconName)
        n.set_urgency(pynotify.URGENCY_LOW)
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            n.attach_to_status_icon(self.icon)
        if details != '':
            n.add_action("details", _("Details"), self.__notifyClicked, details)
        self.__n = n
        self.__details = details
        n.show()
                    
    # Utility methods ----
    
    @gthreaded
    def __notifyClicked(self, notification, action, details):
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
                                 message_format=details)
        dlg.run()
        dlg.destroy()
        
gobject.type_register(Notifier)
