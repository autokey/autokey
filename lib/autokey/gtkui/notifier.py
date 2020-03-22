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

import datetime
import threading

import gi


gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, Gdk, Notify, AppIndicator3
import gettext

from . import popupmenu

import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants

from .. import common


gettext.install("autokey")

TOOLTIP_RUNNING = _("AutoKey - running")
TOOLTIP_PAUSED = _("AutoKey - paused")

def get_notifier(app):
    return IndicatorNotifier(app)

class IndicatorNotifier:
    
    def __init__(self, autokeyApp):
        Notify.init("AutoKey")
        # Used to rate-limit error notifications to 1 per second. Without this, two notifications per second cause the
        # following exception, which in turn completely locks up the GUI:
        # gi.repository.GLib.GError: g-io-error-quark:
        # GDBus.Error:org.freedesktop.Notifications.Error.ExcessNotificationGeneration:
        # Created too many similar notifications in quick succession (36)
        self.last_notification_timestamp = datetime.datetime.now()
        self.app = autokeyApp
        self.configManager = autokeyApp.service.configManager

        self.indicator = AppIndicator3.Indicator.new(
            "AutoKey",
            cm.ConfigManager.SETTINGS[cm_constants.NOTIFICATION_ICON],
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
                                                
        self.indicator.set_attention_icon(common.ICON_FILE_NOTIFICATION_ERROR)
        self.update_visible_status()           
        self.rebuild_menu()
        
    def update_visible_status(self):
        if cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON]:
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        else:
            self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)   
            
    def hide_icon(self):     
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        
    def set_icon(self,name):
        self.indicator.set_icon(name)

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
        
        quitMenuItem = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_QUIT, None)
                
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
            if folder.show_in_tray_menu:
                folders.append(folder)
        
        for item in self.configManager.allItems:
            if item.show_in_tray_menu:
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
        now = datetime.datetime.now()
        if self.last_notification_timestamp + datetime.timedelta(seconds=1) < now:
            self.show_notify(message, Gtk.STOCK_DIALOG_ERROR)
            self.last_notification_timestamp = now
        self.errorItem.show()
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ATTENTION)
        
    def show_notify(self, message, iconName):
        Gdk.threads_enter()
        n = Notify.Notification.new("AutoKey", message, iconName)
        n.set_urgency(Notify.Urgency.LOW)
        n.show()
        Gdk.threads_leave()
        
    def update_tool_tip(self):
        pass
        
    def on_show_error(self, widget, data=None):
        # Work around the current GUI design: the UI is destroyed when the main window is closed.
        # This causes the show_script_error method below to fail because self.app.configWindow.ui doesn’t exist
        if self.app.configWindow is not None:
            self.app.show_script_error(self.app.configWindow.ui)
        else:
            self.app.show_script_error(None)
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
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        cm.ConfigManager.SETTINGS[cm_constants.SHOW_TRAY_ICON] = False
                
    def on_destroy_and_exit(self, widget, data=None):
        self.app.shutdown()


class UnityLauncher(IndicatorNotifier):

    SHOW_ITEM_STRING = _("Add to quicklist/notification menu")
    
    #def __init__(self, autokeyApp):
    #    IndicatorNotifier.__init__(self, autokeyApp)
        
    def __getQuickItem(self, label):
        from gi.repository import Dbusmenu
        item = Dbusmenu.Menuitem.new()
        item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, label)
        item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        return item
        
    def rebuild_menu(self):
        IndicatorNotifier.rebuild_menu(self)
        print(threading.currentThread().name)
        
        #try:
        from gi.repository import Unity, Dbusmenu
        HAVE_UNITY = True
        print("have unity")
        #except ImportError:
        #    return

        print("rebuild unity menu")
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
#            if folder.show_in_tray_menu:
#                folders.append(folder)
#        
#        for item in self.configManager.allItems:
#            if item.show_in_tray_menu:
#                items.append(item)
                    
        # Construct main menu
        quicklist = Dbusmenu.Menuitem.new()
        #if len(items) > 0:
        #    self.menu.append(Gtk.SeparatorMenuItem())
        quicklist.child_append(enableMenuItem)
        quicklist.child_append(configureMenuItem)
        self.launcher.set_property ("quicklist", quicklist)        
        
    def on_ql_enable_toggled(self, menuitem, data=None):
        from gi.repository import Dbusmenu
        if menuitem.property_get_int(Dbusmenu.Menuitem.MENUITEM_PROP_TOGGLE_STATE) == Dbusmenu.Menuitem.MENUITEM_TOGGLE_STATE_CHECKED:
            self.app.unpause_service()
        else:
            self.app.pause_service()
            





