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

import time, logging
from gi.repository import Gtk, Gdk

from .. import configmanager as cm

_logger = logging.getLogger("phrase-menu")

class PopupMenu(Gtk.Menu):
    """
    A popup menu that allows the user to select a phrase.
    """

    def __init__(self, service, folders: list=None, items: list=None, onDesktop=True, title=None):
        Gtk.Menu.__init__(self)
        #self.set_take_focus(cm.ConfigManager.SETTINGS[MENU_TAKES_FOCUS])
        if items is None:
            items = []
        if folders is None:
            folders = []
        self.__i = 1
        self.service = service
        
        if cm.ConfigManager.SETTINGS[cm.SORT_BY_USAGE_COUNT]:
            _logger.debug("Sorting phrase menu by usage count")
            folders.sort(key=lambda obj: obj.usageCount, reverse=True)
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            _logger.debug("Sorting phrase menu by item name/title")
            folders.sort(key=lambda obj: str(obj))
            items.sort(key=lambda obj: str(obj))      
        
        if cm.ConfigManager.SETTINGS[cm.TRIGGER_BY_INITIAL]:
            _logger.debug("Triggering menu item by first initial")
            self.triggerInitial = 1
        else:
            _logger.debug("Triggering menu item by position in list")
            self.triggerInitial = 0


        if len(folders) == 1 and not items and onDesktop:
            # Only one folder - create menu with just its folders and items
            for folder in folders[0].folders:
                menuItem = Gtk.MenuItem(label=self.__getMnemonic(folder.title, onDesktop))
                menuItem.set_submenu(PopupMenu(service, folder.folders, folder.items, onDesktop))
                menuItem.set_use_underline(True)
                self.append(menuItem)
    
            if len(folders[0].folders) > 0:
                self.append(Gtk.SeparatorMenuItem())
            
            self.__addItemsToSelf(folders[0].items, service, onDesktop)
        
        else:
            # Create phrase folder section
            for folder in folders:
                menuItem = Gtk.MenuItem(label=self.__getMnemonic(folder.title, onDesktop))
                menuItem.set_submenu(PopupMenu(service, folder.folders, folder.items, False))
                menuItem.set_use_underline(True)
                self.append(menuItem)
    
            if len(folders) > 0:
                self.append(Gtk.SeparatorMenuItem())
    
            self.__addItemsToSelf(items, service, onDesktop)
            
        self.show_all()
        
    def __getMnemonic(self, desc, onDesktop):
        if 1 < 10 and '_' not in desc and onDesktop:  # TODO: if 1 < 10 ??
            if self.triggerInitial:
                ret = str(desc)
            else:
                ret = "_{} - {}".format(self.__i, desc)
            self.__i += 1
            return ret
        else:
            return desc

    def show_on_desktop(self):
        Gdk.threads_enter()
        time.sleep(0.2)
        self.popup(None, None, None, None, 1, 0)
        Gdk.threads_leave()
        
    def remove_from_desktop(self):
        Gdk.threads_enter()
        self.popdown()
        Gdk.threads_leave()
        
    def __addItemsToSelf(self, items, service, onDesktop):
        # Create phrase section
        if cm.ConfigManager.SETTINGS[cm.SORT_BY_USAGE_COUNT]:
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            items.sort(key=lambda obj: str(obj))
        
        i = 1
        for item in items:
            #if onDesktop:
            #    menuItem = Gtk.MenuItem(item.get_description(service.lastStackState), False)
            #else:
            menuItem = Gtk.MenuItem(label=self.__getMnemonic(item.description, onDesktop))
            menuItem.connect("activate", self.__itemSelected, item)
            menuItem.set_use_underline(True)
            self.append(menuItem)
            
    def __itemSelected(self, widget, item):
        self.service.item_selected(item)
