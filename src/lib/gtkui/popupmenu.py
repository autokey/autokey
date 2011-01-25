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

import gtk, time, logging
from autokey.configmanager import *

from autokey.model import Folder # TODO remove later

_logger = logging.getLogger("phrase-menu")

class PopupMenu(gtk.Menu):
    """
    A popup menu that allows the user to select a phrase.
    """

    def __init__(self, service, folders=[], items=[], onDesktop=True, title=None):
        gtk.Menu.__init__(self)
        #self.set_take_focus(ConfigManager.SETTINGS[MENU_TAKES_FOCUS])
        self.service = service
        
        if title is not None:
            self.add_title(title)
        
        if ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT]:
            _logger.debug("Sorting phrase menu by usage count")
            folders.sort(key=lambda obj: obj.usageCount, reverse=True)
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            _logger.debug("Sorting phrase menu by item name/title")
            folders.sort(key=lambda obj: str(obj))
            items.sort(key=lambda obj: str(obj))      
        
        if len(folders) == 1 and len(items) == 0 and onDesktop:
            # Only one folder - create menu with just its folders and items
            self.add_title(folders[0].title)
            for folder in folders[0].folders:
                menuItem = gtk.MenuItem(folder.title, False)
                menuItem.set_submenu(PopupMenu(service, folder.folders, folder.items, False))
                self.append(menuItem)
    
            if len(folders[0].folders) > 0:
                self.append(gtk.SeparatorMenuItem())
            
            self.__addItemsToSelf(folders[0].items, service, onDesktop)
        
        else:
            # Create phrase folder section
            for folder in folders:
                menuItem = gtk.MenuItem(folder.title, False)
                menuItem.set_submenu(PopupMenu(service, folder.folders, folder.items, False))
                self.append(menuItem)
    
            if len(folders) > 0:
                self.append(gtk.SeparatorMenuItem())
    
            self.__addItemsToSelf(items, service, onDesktop)
            
        self.show_all()


    def show_on_desktop(self):
        gtk.gdk.threads_enter()
        time.sleep(0.2)
        self.popup(None, None, None, 1, 0)
        gtk.gdk.threads_leave()
        
    def remove_from_desktop(self):
        gtk.gdk.threads_enter()
        self.popdown()
        gtk.gdk.threads_leave()
        
    def add_title(self, title):
        titleItem = gtk.MenuItem()
        button = gtk.Button(title)
        #button.set_sensitive(False)
        titleItem.add(button)
        titleItem.set_sensitive(False)
        self.append(titleItem)
        
    def __addItemsToSelf(self, items, service, onDesktop):
        # Create phrase section
        if ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT]:
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            items.sort(key=lambda obj: str(obj))
            
        for item in items:
            #if onDesktop:
            #    menuItem = gtk.MenuItem(item.get_description(service.lastStackState), False)
            #else:
            menuItem = gtk.MenuItem(item.description, False)
            menuItem.connect("activate", self.__itemSelected, item)
            self.append(menuItem)
            
    def __itemSelected(self, widget, item):
        self.service.item_selected(item)

# Testing stuff - remove later ----

class MockPhrase:

    def __init__(self, description):
        self.description = description


class MockExpansionService:

    def phrase_selected(self, event, phrase):
        print phrase.description


if __name__ == "__main__":
    gtk.gdk.threads_init()
    
    myFolder = PhraseFolder("Some phrases")
    myFolder.add_phrase(MockPhrase("phrase 1"))
    myFolder.add_phrase(MockPhrase("phrase 2"))
    myFolder.add_phrase(MockPhrase("phrase 3"))

    myPhrases = []
    myPhrases.append(MockPhrase("phrase 1"))
    myPhrases.append(MockPhrase("phrase 2"))
    myPhrases.append(MockPhrase("phrase 3"))

    menu = PhraseMenu(MockExpansionService(), [myFolder], myPhrases)
    menu.show_on_desktop()
    
    gtk.main()
