# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess
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


import logging
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QMenu, QAction


from autokey import configmanager as cm
import autokey.model

_logger = logging.getLogger("phrase-menu")


class MenuBase:
    
    def __init__(self, service, folders: list=None, items: list=None, onDesktop=True, title=None):
        if items is None:
            items = []
        if folders is None:
            folders = []
        self.service = service
        self._onDesktop = onDesktop
        
        if title is not None:
            self.setTitle(title)
        
        if cm.ConfigManager.SETTINGS[cm.SORT_BY_USAGE_COUNT]:
            _logger.debug("Sorting phrase menu by usage count")
            folders.sort(key=lambda obj: obj.usageCount, reverse=True)
            items.sort(key=lambda obj: obj.usageCount, reverse=True)
        else:
            _logger.debug("Sorting phrase menu by item name/title")
            folders.sort(key=lambda obj: str(obj))
            items.sort(key=lambda obj: str(obj))      
        
        if len(folders) == 1 and len(items) == 0 and onDesktop:
            # Only one folder - create menu with just its folders and items
            self.setTitle(folders[0].title)
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
        if cm.ConfigManager.SETTINGS[cm.SORT_BY_USAGE_COUNT]:
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


class PopupMenu(QMenu, MenuBase):
    
    def __init__(self, service, folders: list=None, items: list=None, onDesktop=True, title=None):
        QMenu.__init__(self)
        MenuBase.__init__(self, service, folders, items, onDesktop, title)
        if items is None:
            items = []
        if folders is None:
            folders = []
        #if not ConfigManager.SETTINGS[MENU_TAKES_FOCUS]:

        self.setFocusPolicy(Qt.StrongFocus)
        # TODO - this doesn't always work - do something about this
            

class SubMenu(QAction, MenuBase):
    
    def __init__(self, title, parent, service, folders: list=None, items: list=None, onDesktop=True):
        QAction.__init__(self, title, parent)
        MenuBase.__init__(self, service, folders, items, onDesktop)
        if items is None:
            items = []
        if folders is None:
            folders = []


class ItemAction(QAction):

    action_sig = pyqtSignal([autokey.model.Script], name="action_sig")

    def __init__(self, parent, description, item, target):
        QAction.__init__(self, description, parent)
        self.item = item
        self.triggered.connect(self.on_triggered)
        self.action_sig.connect(target)

    def on_triggered(self):
        self.action_sig.emit(self.item)
