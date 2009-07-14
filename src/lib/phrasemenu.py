# -*- coding: utf-8 -*-
import gtk, time, logging
from configmanager import *

from phrase import PhraseFolder # TODO remove later

_logger = logging.getLogger("phrase-menu")

class PopupMenu(gtk.Menu):
    """
    A popup menu that allows the user to select a phrase or script.
    """

    def __init__(self, service, folders=[], items=[], onDesktop=True):
        gtk.Menu.__init__(self)
        self.set_take_focus(ConfigManager.SETTINGS[MENU_TAKES_FOCUS])
        
        if ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT]:
            _logger.debug("Sorting phrase menu by usage count")
            folders.sort(key=lambda obj: obj.usageCount, reverse=True)
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
            #folders.sort(reverse=True)
            #items.sort(reverse=True)
        else:
            _logger.debug("Sorting phrase menu by item name/title")
            folders.sort(key=lambda obj: str(obj))
            items.sort(key=lambda obj: str(obj))      
        
        if len(folders) == 1 and len(items) == 0 and onDesktop:
            # Only one folder - create menu with just its folders and items
            for folder in folders[0].folders:
                menuItem = gtk.MenuItem(folder.title, False)
                menuItem.set_submenu(PopupMenu(service, folder.folders, folder.items, False))
                self.append(menuItem)
    
            if len(folders[0].folders) > 0:
                self.append(gtk.SeparatorMenuItem())
            
            self.__addItemsToSelf(folders[0].items, service, onDesktop)
        
        else:
            # Create folder section
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
        self.popup(None, None, None, 1, 0)
        gtk.gdk.threads_leave()
        
    def remove_from_desktop(self):
        gtk.gdk.threads_enter()
        self.popdown()
        gtk.gdk.threads_leave()
        
    def __addItemsToSelf(self, items, service, onDesktop):
        # Create item (script/phrase) section
        if ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT]:
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            items.sort(key=lambda obj: str(obj))
            
        for item in items:
            if onDesktop:
                menuItem = gtk.MenuItem(item.get_description(service.lastStackState), False)
            else:
                menuItem = gtk.MenuItem(item.description, False)
            menuItem.connect("activate", service.phrase_selected, item) # TODO handle different types of items
            self.append(menuItem)        

# TODO Testing stuff - remove later ----

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

    menu = PopupMenu(MockExpansionService(), [myFolder], myPhrases)
    menu.show_on_desktop()
    
    gtk.main()
