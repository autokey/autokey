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


import logging, sys
from PyKDE4.kdeui import KMenu, KAction, KActionMenu, KApplication
#from PyKDE4.kdecore import ki18n, KAboutData, KCmdLineArgs
from PyQt4.QtGui import QCursor
from PyQt4.QtCore import SIGNAL, Qt

from autokey.configmanager import *

_logger = logging.getLogger("phrase-menu")

class MenuBase:
    
    def __init__(self, service, folders=[], items=[], onDesktop=True, title=None):
        self.service = service
        self.__i = 1
        self._onDesktop = onDesktop
        
        if title is not None:
            self.addTitle(title)        
        
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
            self.addTitle(folders[0].title)
            for folder in folders[0].folders:
                subMenuItem = SubMenu(self._getMnemonic(folder.title), self, service, folder.folders, folder.items, False)
                self.addAction(subMenuItem)
    
            if len(folders[0].folders) > 0:
                self.addSeparator()
            
            self._addItemsToSelf(folders[0].items, onDesktop)
        
        else:
            # Create folder section
            for folder in folders:
                subMenuItem = SubMenu(self._getMnemonic(folder.title), self, service, folder.folders, folder.items, False)
                self.addAction(subMenuItem)
    
            if len(folders) > 0:
                self.addSeparator()
    
            self._addItemsToSelf(items, onDesktop)        
        
    def _addItem(self, description, item):
        action = ItemAction(self, self._getMnemonic(description), item, self.service.item_selected)
        self.addAction(action)
        
    def _addItemsToSelf(self, items, onDesktop):
        # Create item (script/phrase) section
        if ConfigManager.SETTINGS[SORT_BY_USAGE_COUNT]:
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            items.sort(key=lambda obj: str(obj))
            
        for item in items:
            if onDesktop:
                self._addItem(item.get_description(self.service.lastStackState), item)
            else:
                self._addItem(item.description, item)

    def _getMnemonic(self, desc):
        #if 1 < 10 and '&' not in desc and self._onDesktop:
        #    ret = "&%d - %s" % (self.__i, desc)
        #    self.__i += 1
        #    return ret
        #else:
        # FIXME - menu does not get keyboard focus, so mnemonic is useless
        return desc
        
class PopupMenu(KMenu, MenuBase):
    
    def __init__(self, service, folders=[], items=[], onDesktop=True, title=None):
        KMenu.__init__(self)
        MenuBase.__init__(self, service, folders, items, onDesktop, title)

        #if not ConfigManager.SETTINGS[MENU_TAKES_FOCUS]:
        self.setFocusPolicy(Qt.StrongFocus)
        # TODO - this doesn't always work - do something about this
            

class SubMenu(KActionMenu, MenuBase):
    
    def __init__(self, title, parent, service, folders=[], items=[], onDesktop=True):
        KActionMenu.__init__(self, title, parent)
        MenuBase.__init__(self, service, folders, items, onDesktop)

        
class ItemAction(KAction):
    
    def __init__(self, parent, description, item, target):
        KAction.__init__(self, description, parent)
        self.item = item
        self.connect(self, SIGNAL("triggered()"), self.on_triggered)
        self.connect(self, SIGNAL("actionSig"), target)

    def on_triggered(self):
        self.emit(SIGNAL("actionSig"), self.item)

        
# ---- TODO Testing stuff - remove later  

class MockFolder:

    def __init__(self, title):
        self.title = title
        self.items = []
        self.folders = []

    def add_item(self, item):
        self.items.append(item)

class MockPhrase:

    def __init__(self, description):
        self.description = description

    def get_description(self, buffer):
        return self.description


class MockExpansionService:

    lastStackState = ""
    def __init__(self, app):
        self.app = app

    def item_selected(self, item):
        print item.description
        self.app.quit()
        

if __name__ == "__main__":
    
    myFolder = MockFolder("Some phrases")
    myFolder.add_item(MockPhrase("phrase 1"))
    myFolder.add_item(MockPhrase("phrase 2"))
    myFolder.add_item(MockPhrase("phrase 3"))

    myPhrases = []
    myPhrases.append(MockPhrase("phrase 1"))
    myPhrases.append(MockPhrase("phrase 2"))
    myPhrases.append(MockPhrase("phrase 3"))    
    
    appName     = "KApplication"
    catalog     = ""
    programName = ki18n ("KApplication")
    version     = "1.0"
    description = ki18n ("KApplication/KMainWindow/KAboutData example")
    license     = KAboutData.License_GPL
    copyright   = ki18n ("(c) 2007 Jim Bublitz")
    text        = ki18n ("none")
    homePage    = "www.riverbankcomputing.com"
    bugEmail    = "jbublitz@nwinternet.com"
    
    aboutData   = KAboutData (appName, catalog, programName, version, description,
                                license, copyright, text, homePage, bugEmail)
    
        
    KCmdLineArgs.init (sys.argv, aboutData)
    app = KApplication()
    
    menu = PopupMenu(MockExpansionService(app), [myFolder], myPhrases)
    #menu.show()
    time.sleep(3)
    menu.exec_(QCursor.pos())
    print "shown"
    
    #app.exec_()
    #print "done"
    sys.exit()    
