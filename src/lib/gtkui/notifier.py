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
# along with this program.  If not, see <http://www.gnu.org/licenses/>..

#import pynotify, gtk, gettext
from gi.repository import Gtk, Notify
import gettext

import popupmenu
from autokey.configmanager import *
from autokey import common

HAVE_APPINDICATOR = False
#try:
#    import appindicator
#    HAVE_APPINDICATOR = True
#except ImportError:
#    pass

gettext.install("autokey")

TOOLTIP_RUNNING = _("AutoKey - running")
TOOLTIP_PAUSED = _("AutoKey - paused")

def get_notifier(app):
    if HAVE_APPINDICATOR:
        return IndicatorNotifier(app)
    else:
        return Notifier(app)

class Notifier:
    """
    Encapsulates all functionality related to the notification icon, notifications, and tray menu.
    """

    def __init__(self, autokeyApp):
        Notify.init("AutoKey")
        self.app = autokeyApp
        self.configManager = autokeyApp.service.configManager
        
        self.icon = Gtk.StatusIcon.new_from_icon_name(ConfigManager.SETTINGS[NOTIFICATION_ICON])
        self.update_tool_tip()
        self.icon.connect("popup_menu", self.on_popup_menu)
        self.icon.connect("activate", self.on_show_configure)
        self.errorItem = None

        self.update_visible_status()

    def update_visible_status(self):
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            self.icon.set_visible(True)
        else:
            self.icon.set_visible(False)
            
    def update_tool_tip(self):
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            if ConfigManager.SETTINGS[SERVICE_RUNNING]:
                self.icon.set_tooltip_text(TOOLTIP_RUNNING)
            else:
                self.icon.set_tooltip_text(TOOLTIP_PAUSED)
                
    def hide_icon(self):
        self.icon.set_visible(False)
        
    def rebuild_menu(self):
        pass
        
    # Signal Handlers ----
        
    def on_popup_menu(self, status_icon, button, activate_time, data=None):
        # Main Menu items
        enableMenuItem = Gtk.CheckMenuItem(_("Enable Expansions"))
        enableMenuItem.set_active(self.app.service.is_running())
        enableMenuItem.set_sensitive(not self.app.serviceDisabled)
        
        configureMenuItem = Gtk.ImageMenuItem(_("Show Main Window"))
        configureMenuItem.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_PREFERENCES, Gtk.IconSize.MENU))
        
        removeMenuItem = Gtk.ImageMenuItem(_("Remove icon"))
        removeMenuItem.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU))
        
        quitMenuItem = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_QUIT, None)
                
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
            menu.append(Gtk.SeparatorMenuItem())
        menu.append(enableMenuItem)
        if self.errorItem is not None:
            menu.append(self.errorItem)
        menu.append(configureMenuItem)
        menu.append(removeMenuItem)
        menu.append(quitMenuItem)
        menu.show_all()
        menu.popup(None, None, None, None, button, activate_time)
        
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
        
    def notify_error(self, message):
        self.show_notify(message, Gtk.STOCK_DIALOG_ERROR)
        self.errorItem = Gtk.MenuItem(_("View script error"))
        self.errorItem.connect("activate", self.on_show_error)
        self.icon.set_from_icon_name(common.ICON_FILE_NOTIFICATION_ERROR)
        
    def on_show_error(self, widget, data=None):
        self.app.show_script_error()
        self.errorItem = None
        self.icon.set_from_icon_name(ConfigManager.SETTINGS[NOTIFICATION_ICON])
        
    def show_notify(self, message, iconName):
        Gdk.threads_enter()
        n = Notify.Notification("AutoKey", message, iconName)
        n.set_urgency(Notify.URGENCY_LOW)
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            n.attach_to_status_icon(self.icon)
        n.show()
        Gdk.threads_leave()
        
                    

class IndicatorNotifier:
    
    def __init__(self, autokeyApp):
        Notify.init("AutoKey")
        self.app = autokeyApp
        self.configManager = autokeyApp.service.configManager

        self.indicator = appindicator.Indicator("AutoKey", ConfigManager.SETTINGS[NOTIFICATION_ICON],
                                                appindicator.CATEGORY_APPLICATION_STATUS)
                                                
        
        self.indicator.set_attention_icon(common.ICON_FILE_NOTIFICATION_ERROR)
        self.update_visible_status()           
        self.rebuild_menu()
        
    def update_visible_status(self):
        if ConfigManager.SETTINGS[SHOW_TRAY_ICON]:
            self.indicator.set_status(appindicator.STATUS_ACTIVE)
        else:
            self.indicator.set_status(appindicator.STATUS_PASSIVE)   
            
    def hide_icon(self):     
        self.indicator.set_status(appindicator.STATUS_PASSIVE)
        
    def rebuild_menu(self):
        # Main Menu items
        self.errorItem = Gtk.MenuItem(_("View script error"))
        
        enableMenuItem = Gtk.CheckMenuItem(_("Enable Expansions"))
        enableMenuItem.set_active(self.app.service.is_running())
        enableMenuItem.set_sensitive(not self.app.serviceDisabled)
        
        configureMenuItem = Gtk.ImageMenuItem(_("Show Main Window"))
        configureMenuItem.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_PREFERENCES, Gtk.IconSize.MENU))
        
        
        
        removeMenuItem = Gtk.ImageMenuItem(_("Remove icon"))
        removeMenuItem.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU))
        
        quitMenuItem = Gtk.ImageMenuItem(Gtk.STOCK_QUIT)
                
        # Menu signals
        enableMenuItem.connect("toggled", self.on_enable_toggled)
        configureMenuItem.connect("activate", self.on_show_configure)
        removeMenuItem.connect("activate", self.on_remove_icon)
        quitMenuItem.connect("activate", self.on_destroy_and_exit)
        self.errorItem.connect("activate", self.on_show_error)
        
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
        self.menu = popupmenu.PopupMenu(self.app.service, folders, items, False)
        if len(items) > 0:
            self.menu.append(Gtk.SeparatorMenuItem())
        self.menu.append(self.errorItem)
        self.menu.append(enableMenuItem)
        self.menu.append(configureMenuItem)
        self.menu.append(removeMenuItem)
        self.menu.append(quitMenuItem)
        self.menu.show_all()
        self.errorItem.hide()
        self.indicator.set_menu(self.menu)
        
    def notify_error(self, message):
        self.show_notify(message, Gtk.STOCK_DIALOG_ERROR)
        self.errorItem.show()
        self.indicator.set_status(appindicator.STATUS_ATTENTION)
        
    def show_notify(self, message, iconName):
        Gdk.threads_enter()
        n = Notify.Notification("AutoKey", message, iconName)
        n.set_urgency(Notify.URGENCY_LOW)
        n.show()
        Gdk.threads_leave()
        
    def update_tool_tip(self):
        pass
        
    def on_show_error(self, widget, data=None):
        self.app.show_script_error()
        self.errorItem.hide()
        self.update_visible_status()
            
    def on_enable_toggled(self, widget, data=None):
        if widget.active:
            self.app.unpause_service()
        else:
            self.app.pause_service()
            
    def on_show_configure(self, widget, data=None):
        self.app.show_configure()

    def on_remove_icon(self, widget, data=None):
        self.indicator.set_status(appindicator.STATUS_PASSIVE)
        ConfigManager.SETTINGS[SHOW_TRAY_ICON] = False
                
    def on_destroy_and_exit(self, widget, data=None):
        self.app.shutdown()
        
        
class UnityLauncher(IndicatorNotifier):

    SHOW_ITEM_STRING = _("Add to quicklist/notification menu")
    
    #def __init__(self, autokeyApp):
    #    IndicatorNotifier.__init__(self, autokeyApp)
        
    def __getQuickItem(self, label):
        item = Dbusmenu.Menuitem.new()
        item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, label)
        item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        return item
        
    def rebuild_menu(self):
        IndicatorNotifier.rebuild_menu(self)
        print threading.currentThread().name
        
        #try:
        from gi.repository import Unity, Dbusmenu
        HAVE_UNITY = True
        print "have unity"
        #except ImportError:
        #    return

        print "rebuild unity menu"
        self.launcher = Unity.LauncherEntry.get_for_desktop_id ("autokey-gtk.desktop")   
    
        # Main Menu items
        enableMenuItem = self.__getQuickItem(_("Enable Expansions"))
        enableMenuItem.property_set(Dbusmenu.MENUITEM_PROP_TOGGLE_TYPE, Dbusmenu.MENUITEM_TOGGLE_CHECK)
        #if self.app.service.is_running():
        #    enableMenuItem.property_set_int(Dbusmenu.MENUITEM_PROP_TOGGLE_STATE, Dbusmenu.MENUITEM_TOGGLE_STATE_CHECKED)
        #else:
        #    enableMenuItem.property_set_int(Dbusmenu.MENUITEM_PROP_TOGGLE_STATE, Dbusmenu.MENUITEM_TOGGLE_STATE_UNCHECKED)
        enableMenuItem.property_set_int(Dbusmenu.MENUITEM_PROP_TOGGLE_STATE, int(self.app.service.is_running()))
        
        enableMenuItem.property_set_bool(Dbusmenu.MENUITEM_PROP_ENABLED, not self.app.serviceDisabled)
        
        configureMenuItem = self.__getQuickItem(_("Show Main Window"))
        
        # Menu signals
        enableMenuItem.connect("item-activated", self.on_ql_enable_toggled, None)
        configureMenuItem.connect("item-activated", self.on_show_configure, None)
        
        # Get phrase folders to add to main menu
#        folders = []
#        items = []

#        for folder in self.configManager.allFolders:
#            if folder.showInTrayMenu:
#                folders.append(folder)
#        
#        for item in self.configManager.allItems:
#            if item.showInTrayMenu:
#                items.append(item)
                    
        # Construct main menu
        quicklist = Dbusmenu.Menuitem.new()
        #if len(items) > 0:
        #    self.menu.append(Gtk.SeparatorMenuItem())
        quicklist.child_append(enableMenuItem)
        quicklist.child_append(configureMenuItem)
        self.launcher.set_property ("quicklist", quicklist)        
        
    def on_ql_enable_toggled(self, menuitem, data=None):
        if menuitem.property_get_int(Menuitem.MENUITEM_PROP_TOGGLE_STATE) == Menuitem.MENUITEM_TOGGLE_STATE_CHECKED:
            self.app.unpause_service()
        else:
            self.app.pause_service()
            





