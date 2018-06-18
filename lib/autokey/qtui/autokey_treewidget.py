# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem

from autokey import model


class AkTreeWidget(QTreeWidget):

    def edit(self, index, trigger, event):
        if index.column() == 0:
            super(QTreeWidget, self).edit(index, trigger, event)
        return False

    def keyPressEvent(self, event):
        if self.window().is_dirty() \
                and (event.matches(QKeySequence.MoveToNextLine) or event.matches(QKeySequence.MoveToPreviousLine)):
            veto = self.window().central_widget.promptToSave()
            if not veto:
                QTreeWidget.keyPressEvent(self, event)
            else:
                event.ignore()
        else:
            QTreeWidget.keyPressEvent(self, event)

    def mousePressEvent(self, event):
        if self.window().is_dirty():
            veto = self.window().central_widget.promptToSave()
            if not veto:
                QTreeWidget.mousePressEvent(self, event)
                QTreeWidget.mouseReleaseEvent(self, event)
            else:
                event.ignore()
        else:
            QTreeWidget.mousePressEvent(self, event)

    def dragMoveEvent(self, event):
        target = self.itemAt(event.pos())
        if isinstance(target, FolderWidgetItem):
            QTreeWidget.dragMoveEvent(self, event)
        else:
            event.ignore()

    def dropEvent(self, event):
        target = self.itemAt(event.pos())
        sources = self.selectedItems()
        self.window().move_items(sources, target)


class WidgetItemFactory:

    def __init__(self, rootFolders):
        self.folders = rootFolders

    def get_root_folder_list(self):
        rootItems = []

        for folder in self.folders:
            item = self.__buildItem(None, folder)
            rootItems.append(item)
            self.processFolder(item, folder)

        return rootItems

    def processFolder(self, parentItem, parentFolder):
        for folder in parentFolder.folders:
            item = self.__buildItem(parentItem, folder)
            self.processFolder(item, folder)

        for childModelItem in parentFolder.items:
            self.__buildItem(parentItem, childModelItem)

    def __buildItem(self, parent, item):
        if isinstance(item, model.Folder):
            return FolderWidgetItem(parent, item)
        elif isinstance(item, model.Phrase):
            return PhraseWidgetItem(parent, item)
        elif isinstance(item, model.Script):
            return ScriptWidgetItem(parent, item)


class FolderWidgetItem(QTreeWidgetItem):

    def __init__(self, parent, folder):
        QTreeWidgetItem.__init__(self)
        self.folder = folder
        self.setIcon(0, QIcon.fromTheme("folder"))
        self.setText(0, folder.title)
        self.setText(1, folder.get_abbreviations())
        self.setText(2, folder.get_hotkey_string())
        self.setData(3, Qt.UserRole, folder)
        if parent is not None:
            parent.addChild(self)

        self.setFlags(self.flags() | Qt.ItemIsEditable)

    def update(self):
        self.setText(0, self.folder.title)
        self.setText(1, self.folder.get_abbreviations())
        self.setText(2, self.folder.get_hotkey_string())

    def __ge__(self, other):
        if isinstance(other, ScriptWidgetItem):
            return QTreeWidgetItem.__ge__(self, other)
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, FolderWidgetItem):
            return QTreeWidgetItem.__lt__(self, other)
        else:
            return True


class PhraseWidgetItem(QTreeWidgetItem):

    def __init__(self, parent, phrase):
        QTreeWidgetItem.__init__(self)
        self.phrase = phrase
        self.setIcon(0, QIcon.fromTheme("text-x-generic"))
        self.setText(0, phrase.description)
        self.setText(1, phrase.get_abbreviations())
        self.setText(2, phrase.get_hotkey_string())
        self.setData(3, Qt.UserRole, phrase)
        if parent is not None:
            parent.addChild(self)

        self.setFlags(self.flags() | Qt.ItemIsEditable)

    def update(self):
        self.setText(0, self.phrase.description)
        self.setText(1, self.phrase.get_abbreviations())
        self.setText(2, self.phrase.get_hotkey_string())

    def __ge__(self, other):
        if isinstance(other, ScriptWidgetItem):
            return QTreeWidgetItem.__ge__(self, other)
        else:
            return True

    def __lt__(self, other):
        if isinstance(other, PhraseWidgetItem):
            return QTreeWidgetItem.__lt__(self, other)
        else:
            return False


class ScriptWidgetItem(QTreeWidgetItem):

    def __init__(self, parent, script):
        QTreeWidgetItem.__init__(self)
        self.script = script
        self.setIcon(0, QIcon.fromTheme("text-x-python"))
        self.setText(0, script.description)
        self.setText(1, script.get_abbreviations())
        self.setText(2, script.get_hotkey_string())
        self.setData(3, Qt.UserRole, script)
        if parent is not None:
            parent.addChild(self)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

    def update(self):
        self.setText(0, self.script.description)
        self.setText(1, self.script.get_abbreviations())
        self.setText(2, self.script.get_hotkey_string())

    def __ge__(self, other):
        if isinstance(other, ScriptWidgetItem):
            return QTreeWidgetItem.__ge__(self, other)
        else:
            return True

    def __lt__(self, other):
        if isinstance(other, ScriptWidgetItem):
            return QTreeWidgetItem.__lt__(self, other)
        else:
            return False
