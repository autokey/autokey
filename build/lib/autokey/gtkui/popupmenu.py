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

import time
from gi.repository import Gtk, Gdk

import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants


logger = __import__("autokey.logger").logger.get_logger(__name__)

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

        folders, items = self.sort_popup_items(folders, items)
        self.set_up_trigger_position()

        single_desktop_folder = len(folders) == 1 and not items and onDesktop
        if single_desktop_folder:
            # Only one folder - create menu with just its folders and items
            self.create_menu_item(folders[0].folders, service, onDesktop)
            self.__addItemsToSelf(folders[0].items, onDesktop)

        else:
            # Create phrase folder section
            self.create_menu_item(folders, service, onDesktop,
                                  multiple_folders=True)
            self.__addItemsToSelf(items, onDesktop)

        self.show_all()

    def create_menu_item(self, folders, service, onDesktop, multiple_folders=False):
        for folder in folders:
            menuItem = Gtk.MenuItem(label=self.__getMnemonic(folder.title, onDesktop))
            if multiple_folders:
                onDesktop=False
            menuItem.set_submenu(PopupMenu(service, folder.folders, folder.items, onDesktop))
            menuItem.set_use_underline(True)
            self.append(menuItem)
        if len(folders) > 0:
            self.append(Gtk.SeparatorMenuItem())

    def set_up_trigger_position(self):
        if cm.ConfigManager.SETTINGS[cm_constants.TRIGGER_BY_INITIAL]:
            self.triggerInitial = 1
        else:
            logger.debug("Triggering menu item by position in list")
            self.triggerInitial = 0

    def sort_popup_items(self, folders, items):
        if cm.ConfigManager.SETTINGS[cm_constants.SORT_BY_USAGE_COUNT]:
            logger.debug("Sorting phrase menu by usage count")
            folders.sort(key=lambda obj: obj.usageCount, reverse=True)
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            logger.debug("Sorting phrase menu by item name/title")
            folders.sort(key=lambda obj: str(obj))
            items.sort(key=lambda obj: str(obj))
        return folders, items

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

    def __addItemsToSelf(self, items, onDesktop):
        # Create phrase section
        if cm.ConfigManager.SETTINGS[cm_constants.SORT_BY_USAGE_COUNT]:
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            items.sort(key=lambda obj: str(obj))

        for item in items:
            menuItem = Gtk.MenuItem(label=self.__getMnemonic(item.description, onDesktop))
            menuItem.connect("activate", self.__itemSelected, item)
            menuItem.set_use_underline(True)
            self.append(menuItem)

    def __itemSelected(self, widget, item):
        self.service.item_selected(item)
