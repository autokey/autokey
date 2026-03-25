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

from typing import Union, List, Optional

from PyQt5.QtCore import Qt, QEvent, QModelIndex, QObject, QPoint
from PyQt5.QtGui import QKeySequence, QIcon, QKeyEvent, QMouseEvent, QDragMoveEvent, QDropEvent
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView, QHeaderView

import autokey.model.folder
import autokey.model.phrase
import autokey.model.script


def _sort_key(item: QTreeWidgetItem, col: int, reverse: bool):
    is_folder = isinstance(item, FolderWidgetItem)
    folder_bucket = (1 if reverse else 0) if is_folder else (0 if reverse else 1)
    return (folder_bucket, item.text(col).lower())


def _collect_expanded(item: QTreeWidgetItem, result: dict):
    """Walk tree and record expanded state by item id before any structural changes."""
    result[id(item)] = item.isExpanded()
    for i in range(item.childCount()):
        _collect_expanded(item.child(i), result)


def _restore_expanded(item: QTreeWidgetItem, saved: dict):
    """Restore expanded state after structural changes."""
    if id(item) in saved:
        item.setExpanded(saved[id(item)])
    for i in range(item.childCount()):
        _restore_expanded(item.child(i), saved)


def _sort_children(parent: QTreeWidgetItem, col: int, order: Qt.SortOrder, saved_expanded: dict):
    count = parent.childCount()
    if count == 0:
        return
    children = [parent.takeChild(0) for _ in range(count)]
    reverse = (order == Qt.DescendingOrder)
    children.sort(key=lambda item: _sort_key(item, col, reverse), reverse=reverse)
    for child in children:
        parent.addChild(child)
        _restore_expanded(child, saved_expanded)
        if isinstance(child, FolderWidgetItem):
            _sort_children(child, col, order, saved_expanded)


class HeaderClickFilter(QObject):
    """Event filter installed on the header view to intercept mouse clicks for sorting."""

    def __init__(self, tree: 'AkTreeWidget'):
        super().__init__(tree)
        self.tree = tree
        self._sort_col = 0
        self._sort_order = Qt.AscendingOrder

    def eventFilter(self, obj, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            header = self.tree.header()
            col = header.logicalIndexAt(event.pos())
            if col >= 0:
                if col == self._sort_col:
                    self._sort_order = (
                        Qt.DescendingOrder if self._sort_order == Qt.AscendingOrder
                        else Qt.AscendingOrder
                    )
                else:
                    self._sort_col = col
                    self._sort_order = Qt.AscendingOrder
                header.setSortIndicator(self._sort_col, self._sort_order)
                header.setSortIndicatorShown(True)
                self.tree._apply_sort(self._sort_col, self._sort_order)
                return True
        return False


class AkTreeWidget(QTreeWidget):

    def install_sort_filter(self):
        """Call this after setupUi to attach the header click filter."""
        self._header_filter = HeaderClickFilter(self)
        self.header().installEventFilter(self._header_filter)
        if self.header().viewport():
            self.header().viewport().installEventFilter(self._header_filter)
        self.header().setSortIndicatorShown(True)
        self.header().setSortIndicator(0, Qt.AscendingOrder)

    def sortItems(self, col: int, order: Qt.SortOrder):
        """Override to use Python-driven sort instead of Qt's internal comparator."""
        self.header().setSortIndicator(col, order)
        self.header().setSortIndicatorShown(True)
        if hasattr(self, '_header_filter'):
            self._header_filter._sort_col = col
            self._header_filter._sort_order = order
        self._apply_sort(col, order)

    def _apply_sort(self, col: int, order: Qt.SortOrder):
        reverse = (order == Qt.DescendingOrder)
        count = self.topLevelItemCount()
        if count == 0:
            return

        # Collect expanded state and current selection BEFORE touching the tree
        saved_expanded = {}
        for i in range(count):
            _collect_expanded(self.topLevelItem(i), saved_expanded)
        current = self.currentItem()

        # Sort top-level items
        items = [self.takeTopLevelItem(0) for _ in range(count)]
        items.sort(key=lambda item: _sort_key(item, col, reverse), reverse=reverse)
        for item in items:
            self.addTopLevelItem(item)
            _restore_expanded(item, saved_expanded)
            if isinstance(item, FolderWidgetItem):
                _sort_children(item, col, order, saved_expanded)

        # Restore selection
        if current is not None:
            self.setCurrentItem(current)

    def edit(self, index: QModelIndex, trigger: QAbstractItemView.EditTrigger, event: QEvent):
        if index.column() == 0:
            super(QTreeWidget, self).edit(index, trigger, event)
        return False

    def keyPressEvent(self, event: QKeyEvent):
        if self.window().is_dirty() \
                and (event.matches(QKeySequence.MoveToNextLine) or event.matches(QKeySequence.MoveToPreviousLine)):
            veto = self.window().central_widget.promptToSave()
            if not veto:
                QTreeWidget.keyPressEvent(self, event)
            else:
                event.ignore()
        else:
            QTreeWidget.keyPressEvent(self, event)

    def mousePressEvent(self, event: QMouseEvent):
        if self.window().is_dirty():
            veto = self.window().central_widget.promptToSave()
            if not veto:
                QTreeWidget.mousePressEvent(self, event)
                QTreeWidget.mouseReleaseEvent(self, event)
            else:
                event.ignore()
        else:
            QTreeWidget.mousePressEvent(self, event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        target = self.itemAt(event.pos())
        if isinstance(target, FolderWidgetItem):
            QTreeWidget.dragMoveEvent(self, event)
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        target = self.itemAt(event.pos())
        sources = self.selectedItems()
        self.window().central_widget.move_items(sources, target)


class FolderWidgetItem(QTreeWidgetItem):

    def __init__(self, parent: Optional[QTreeWidgetItem], folder: autokey.model.folder.Folder):
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


class PhraseWidgetItem(QTreeWidgetItem):

    def __init__(self, parent: Optional[FolderWidgetItem], phrase: autokey.model.phrase.Phrase):
        QTreeWidgetItem.__init__(self)
        self.phrase = phrase
        self.setIcon(0, QIcon.fromTheme("text-x-generic"))
        self.setText(0, phrase.description)
        self.setText(1, phrase.get_abbreviations())
        self.setText(2, phrase.get_hotkey_string())
        self.setData(3, Qt.UserRole, phrase)
        if parent is not None:  # TODO: Phrase without parent allowed? This is should be an error.
            parent.addChild(self)

        self.setFlags(self.flags() | Qt.ItemIsEditable)

    def update(self):
        self.setText(0, self.phrase.description)
        self.setText(1, self.phrase.get_abbreviations())
        self.setText(2, self.phrase.get_hotkey_string())


class ScriptWidgetItem(QTreeWidgetItem):

    def __init__(self, parent: Optional[FolderWidgetItem], script: autokey.model.script.Script):
        QTreeWidgetItem.__init__(self)
        self.script = script
        self.setIcon(0, QIcon.fromTheme("text-x-python"))
        self.setText(0, script.description)
        self.setText(1, script.get_abbreviations())
        self.setText(2, script.get_hotkey_string())
        self.setData(3, Qt.UserRole, script)
        if parent is not None:  # TODO: Script without parent allowed? This is should be an error.
            parent.addChild(self)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

    def update(self):
        self.setText(0, self.script.description)
        self.setText(1, self.script.get_abbreviations())
        self.setText(2, self.script.get_hotkey_string())


ItemType = Union[autokey.model.folder.Folder, autokey.model.phrase.Phrase, autokey.model.script.Script]
ItemWidgetType = Union[FolderWidgetItem, PhraseWidgetItem, ScriptWidgetItem]


class WidgetItemFactory:

    def __init__(self, root_folders: List[autokey.model.folder.Folder]):
        self.folders = root_folders

    def get_root_folder_list(self):
        root_items = []

        for folder in self.folders:
            item = WidgetItemFactory._build_item(None, folder)
            root_items.append(item)
            WidgetItemFactory.process_folder(item, folder)

        return root_items

    @staticmethod
    def process_folder(parent_item: ItemWidgetType, parent_folder: autokey.model.folder.Folder):
        for folder in parent_folder.folders:
            item = WidgetItemFactory._build_item(parent_item, folder)
            WidgetItemFactory.process_folder(item, folder)

        for childModelItem in parent_folder.items:
            WidgetItemFactory._build_item(parent_item, childModelItem)

    @staticmethod
    def _build_item(parent: Optional[FolderWidgetItem], item: ItemType) -> ItemWidgetType:
        if isinstance(item, autokey.model.folder.Folder):
            return FolderWidgetItem(parent, item)
        elif isinstance(item, autokey.model.phrase.Phrase):
            return PhraseWidgetItem(parent, item)
        elif isinstance(item, autokey.model.script.Script):
            return ScriptWidgetItem(parent, item)
