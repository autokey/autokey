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
import os.path
import logging

from PyQt4.QtCore import Qt, QUrl
from PyQt4.QtGui import QHeaderView, QMessageBox, QFileDialog

from autokey import iomediator
from autokey import model
from autokey import configmanager as cm

from . import common
from . import autokey_treewidget as ak_tree


logger = common.logger.getChild("CentralWidget")  # type: logging.Logger


class CentralWidget(*common.inherits_from_ui_file_with_name("centralwidget")):

    def __init__(self, parent):
        super(CentralWidget, self).__init__(parent)
        logger.debug("CentralWidget instance created.")
        self.setupUi(self)
        self.dirty = False
        self.configManager = None
        self.recorder = iomediator.Recorder(self.scriptPage)

        self.cutCopiedItems = []

        [self.treeWidget.setColumnWidth(x, cm.ConfigManager.SETTINGS[cm.COLUMN_WIDTHS][x]) for x in range(3)]
        hView = self.treeWidget.header()
        hView.setResizeMode(QHeaderView.ResizeMode(QHeaderView.Interactive | QHeaderView.ResizeToContents))

        self.logHandler = None
        self.listWidget.hide()

        self.factory = None  # type: ak_tree.WidgetItemFactory

        # TODO: Move into the CentralWidget class. This configures CentralWidget component, so should be moved there.
        """
        # Log view context menu
        action_clear_log = QAction()
        self.listWidget

        act = self.__createAction("clear-log", i18n("Clear Log"), None, self.centralWidget.on_clear_log)
        self.centralWidget.listWidget.addAction(act)
        act = self.__createAction("clear-log", i18n("Save Log As..."), None, self.centralWidget.on_save_log)
        self.centralWidget.listWidget.addAction(act)
        """
        # TODO Up until here

    def init(self, app):
        self.configManager = app.configManager
        self.logHandler = ak_tree.ListWidgetHandler(self.listWidget, app)

    def populate_tree(self, config):
        self.factory = ak_tree.WidgetItemFactory(config.folders)
        root_folders = self.factory.get_root_folder_list()
        for item in root_folders:
            self.treeWidget.addTopLevelItem(item)

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(0))
        self.on_treeWidget_itemSelectionChanged()

    def set_splitter(self, window_size):
        pos = cm.ConfigManager.SETTINGS[cm.HPANE_POSITION]
        self.splitter.setSizes([pos, window_size.width() - pos])

    def set_dirty(self, dirty: bool):
        self.dirty = dirty

    def promptToSave(self):
        if cm.ConfigManager.SETTINGS[cm.PROMPT_TO_SAVE]:
            # TODO: i18n
            result = QMessageBox.question(
                self.topLevelWidget(),
                "Save changes?",
                "There are unsaved changes. Would you like to save them?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if result == QMessageBox.Yes:
                return self.on_save()
            elif result == QMessageBox.Cancel:
                return True
            else:
                return False
        else:
            # don't prompt, just save
            return self.on_save()

    # ---- Signal handlers

    def on_treeWidget_customContextMenuRequested(self, position):
        menu = self.factory.container("Context", self.topLevelWidget())
        menu.popup(position)  # Previously used QCursor.pos()

    def on_treeWidget_itemChanged(self, item, column):
        if item is self.treeWidget.selectedItems()[0] and column == 0:
            newText = str(item.text(0))
            if common.validate(
                    not common.EMPTY_FIELD_REGEX.match(newText),
                    "The name can't be empty.",
                    None,
                    self.topLevelWidget()):
                self.topLevelWidget().app.monitor.suspend()
                self.stack.currentWidget().set_item_title(newText)
                self.stack.currentWidget().rebuild_item_path()

                persistGlobal = self.stack.currentWidget().save()
                self.topLevelWidget().app.monitor.unsuspend()
                self.topLevelWidget().app.config_altered(persistGlobal)

                self.treeWidget.sortItems(0, Qt.AscendingOrder)
            else:
                item.update()

    def on_treeWidget_itemSelectionChanged(self):
        modelItems = self.__getSelection()

        if len(modelItems) == 1:
            modelItem = modelItems[0]
            if isinstance(modelItem, model.Folder):
                self.stack.setCurrentIndex(0)
                self.folderPage.load(modelItem)

            elif isinstance(modelItem, model.Phrase):
                self.stack.setCurrentIndex(1)
                self.phrasePage.load(modelItem)

            elif isinstance(modelItem, model.Script):
                self.stack.setCurrentIndex(2)
                self.scriptPage.load(modelItem)

            self.topLevelWidget().update_actions(modelItems, True)
            self.set_dirty(False)
            self.topLevelWidget().cancel_record()

        else:
            self.topLevelWidget().update_actions(modelItems, False)

    def on_new_topfolder(self):
        logger.info("User initiates top-level folder creation")
        message_box = QMessageBox(
            QMessageBox.Question,
            "Create Folder",
            "Create folder in the default location?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            self.topLevelWidget()

        )
        message_box.button(QMessageBox.No).setText("Create elsewhere")  # TODO: i18n
        result = message_box.exec_()

        self.topLevelWidget().app.monitor.suspend()

        if result == QMessageBox.Yes:
            logger.debug("User creates a new top-level folder.")
            self.__createFolder(None)

        elif result == QMessageBox.No:
            logger.debug("User creates a new folder and chose to create it elsewhere")
            path = QFileDialog.getExistingDirectory(
                self.topLevelWidget(),
                "Where should the folder be created?"
            )
            if path != "":
                path = str(path)
                name = os.path.basename(path)
                folder = model.Folder(name, path=path)
                newItem = ak_tree.FolderWidgetItem(None, folder)
                self.treeWidget.addTopLevelItem(newItem)
                self.configManager.folders.append(folder)
                self.topLevelWidget().app.config_altered(True)

            self.topLevelWidget().app.monitor.unsuspend()
        else:
            logger.debug("User canceled top-level folder creation.")
            self.topLevelWidget().app.monitor.unsuspend()


    def on_new_folder(self):
        parentItem = self.treeWidget.selectedItems()[0]
        self.__createFolder(parentItem)

    def __createFolder(self, parentItem):
        folder = model.Folder("New Folder")
        newItem = ak_tree.FolderWidgetItem(parentItem, folder)
        self.topLevelWidget().app.monitor.suspend()

        if parentItem is not None:
            parentFolder = self.__extractData(parentItem)
            parentFolder.add_folder(folder)
        else:
            self.treeWidget.addTopLevelItem(newItem)
            self.configManager.folders.append(folder)

        folder.persist()
        self.topLevelWidget().app.monitor.unsuspend()

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()

    def on_new_phrase(self):
        self.topLevelWidget().app.monitor.suspend()
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)

        phrase = model.Phrase("New Phrase", "Enter phrase contents")
        newItem = ak_tree.PhraseWidgetItem(parentItem, phrase)
        parent.add_item(phrase)
        phrase.persist()

        self.topLevelWidget().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.treeWidget.setItemSelected(parentItem, False)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()

    def on_new_script(self):
        self.topLevelWidget().app.monitor.suspend()
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)

        script = model.Script("New Script", "#Enter script code")
        newItem = ak_tree.ScriptWidgetItem(parentItem, script)
        parent.add_item(script)
        script.persist()

        self.topLevelWidget().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.treeWidget.setItemSelected(parentItem, False)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()

    def on_undo(self):
        self.stack.currentWidget().undo()

    def on_redo(self):
        self.stack.currentWidget().redo()

    def on_copy(self):
        sourceObjects = self.__getSelection()

        for source in sourceObjects:
            if isinstance(source, model.Phrase):
                newObj = model.Phrase('', '')
            else:
                newObj = model.Script('', '')
            newObj.copy(source)
            self.cutCopiedItems.append(newObj)

    def on_clone(self):
        sourceObject = self.__getSelection()[0]
        parentItem = self.treeWidget.selectedItems()[0].parent()
        parent = self.__extractData(parentItem)

        if isinstance(sourceObject, model.Phrase):
            newObj = model.Phrase('', '')
            newObj.copy(sourceObject)
            newItem = ak_tree.PhraseWidgetItem(parentItem, newObj)
        else:
            newObj = model.Script('', '')
            newObj.copy(sourceObject)
            newItem = ak_tree.ScriptWidgetItem(parentItem, newObj)

        parent.add_item(newObj)
        self.topLevelWidget().app.monitor.suspend()
        newObj.persist()

        self.topLevelWidget().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItem)
        self.treeWidget.setItemSelected(parentItem, False)
        self.on_treeWidget_itemSelectionChanged()
        self.topLevelWidget().app.config_altered(False)

    def on_cut(self):
        self.cutCopiedItems = self.__getSelection()
        self.topLevelWidget().app.monitor.suspend()

        sourceItems = self.treeWidget.selectedItems()
        result = [f for f in sourceItems if f.parent() not in sourceItems]
        for item in result:
            self.__removeItem(item)

        self.topLevelWidget().app.monitor.unsuspend()
        self.topLevelWidget().app.config_altered(False)

    def on_paste(self):
        parentItem = self.treeWidget.selectedItems()[0]
        parent = self.__extractData(parentItem)
        self.topLevelWidget().app.monitor.suspend()

        newItems = []
        for item in self.cutCopiedItems:
            if isinstance(item, model.Folder):
                f = ak_tree.WidgetItemFactory(None)
                newItem = ak_tree.FolderWidgetItem(parentItem, item)
                f.processFolder(newItem, item)
                parent.add_folder(item)
            elif isinstance(item, model.Phrase):
                newItem = ak_tree.PhraseWidgetItem(parentItem, item)
                parent.add_item(item)
            else:
                newItem = ak_tree.ScriptWidgetItem(parentItem, item)
                parent.add_item(item)

            item.persist()

            newItems.append(newItem)

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(newItems[-1])
        self.on_treeWidget_itemSelectionChanged()
        self.cutCopiedItems = []
        for item in newItems:
            self.treeWidget.setItemSelected(item, True)
        self.topLevelWidget().app.monitor.unsuspend()
        self.topLevelWidget().app.config_altered(False)

    def on_delete(self):
        widgetItems = self.treeWidget.selectedItems()
        self.topLevelWidget().app.monitor.suspend()

        if len(widgetItems) == 1:
            widgetItem = widgetItems[0]
            data = self.__extractData(widgetItem)
            if isinstance(data, model.Folder):
                header = "Delete Folder?"
                msg = "Are you sure you want to delete the '{deleted_folder}' folder and all the items in it?".format(
                    deleted_folder=data.title)
            else:
                header = "Delete Script/Phrase?"  # TODO: Determine actual type
                msg = "Are you sure you want to delete '{element}'?".format(element=data.description)
        else:
            item_count = len(widgetItems)
            header = "Delete {item_count} selected items?".format(item_count=item_count)
            msg = "Are you sure you want to delete the {item_count} selected folders/items?".format(
                item_count=item_count)
        result = QMessageBox.question(self.topLevelWidget(), header, msg, QMessageBox.Yes | QMessageBox.No)

        if result == QMessageBox.Yes:
            for widgetItem in widgetItems:
                self.__removeItem(widgetItem)

        self.topLevelWidget().app.monitor.unsuspend()
        if result == QMessageBox.Yes:
            self.topLevelWidget().app.config_altered(False)

    def on_rename(self):
        widgetItem = self.treeWidget.selectedItems()[0]
        self.treeWidget.editItem(widgetItem, 0)

    def on_save(self):
        logger.info("User requested file save.")
        if self.stack.currentWidget().validate():
            self.topLevelWidget().app.monitor.suspend()
            persist_global = self.stack.currentWidget().save()
            self.topLevelWidget().save_completed(persist_global)
            self.set_dirty(False)

            item = self.treeWidget.selectedItems()[0]
            item.update()
            self.treeWidget.update()
            self.treeWidget.sortItems(0, Qt.AscendingOrder)
            self.topLevelWidget().app.monitor.unsuspend()
            return False

        return True

    def on_reset(self):
        self.stack.currentWidget().reset()
        self.set_dirty(False)
        self.topLevelWidget().cancel_record()

    def on_save_log(self):
        file_name = QFileDialog.getSaveFileName(
            self.topLevelWidget(),
            "Save log file",
            QUrl(),
            ""  # TODO: File type filter. Maybe "*.log"?
        )
        # TODO: with-statement instead of try-except
        if file_name != "":
            try:
                f = open(file_name, 'w')
                for i in range(self.listWidget.count()):
                    text = self.listWidget.item(i).text()
                    f.write(text)
                    f.write('\n')
            except:
                logger.exception("Error saving log file")
            finally:
                f.close()

    def on_clear_log(self):
        self.listWidget.clear()

    def move_items(self, sourceItems, target):
        targetModelItem = self.__extractData(target)

        # Filter out any child objects that belong to a parent already in the list
        result = [f for f in sourceItems if f.parent() not in sourceItems]

        self.topLevelWidget().app.monitor.suspend()

        for source in result:
            self.__removeItem(source)
            sourceModelItem = self.__extractData(source)

            if isinstance(sourceModelItem, model.Folder):
                targetModelItem.add_folder(sourceModelItem)
                self.__moveRecurseUpdate(sourceModelItem)
            else:
                targetModelItem.add_item(sourceModelItem)
                sourceModelItem.path = None
                sourceModelItem.persist()

            target.addChild(source)

        self.topLevelWidget().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.topLevelWidget().app.config_altered(True)

    def __moveRecurseUpdate(self, folder):
        folder.path = None
        folder.persist()

        for subfolder in folder.folders:
            self.__moveRecurseUpdate(subfolder)

        for child in folder.items:
            child.path = None
            child.persist()

    # ---- Private methods

    def get_selected_item(self):
        return self.__getSelection()

    def __getSelection(self):
        items = self.treeWidget.selectedItems()
        ret = []
        for item in items:
            ret.append(self.__extractData(item))

        # Filter out any child objects that belong to a parent already in the list
        result = [f for f in ret if f.parent not in ret]
        return result

    def __extractData(self, item):
        variant = item.data(3, Qt.UserRole)
        return variant

    def __removeItem(self, widgetItem):
        parent = widgetItem.parent()
        item = self.__extractData(widgetItem)
        self.__deleteHotkeys(item)

        if parent is None:
            removedIndex = self.treeWidget.indexOfTopLevelItem(widgetItem)
            self.treeWidget.takeTopLevelItem(removedIndex)
            self.configManager.folders.remove(item)
        else:
            removedIndex = parent.indexOfChild(widgetItem)
            parent.removeChild(widgetItem)

            if isinstance(item, model.Folder):
                item.parent.remove_folder(item)
            else:
                item.parent.remove_item(item)

        item.remove_data()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)

        if parent is not None:
            if parent.childCount() > 0:
                newIndex = min([removedIndex, parent.childCount() - 1])
                self.treeWidget.setCurrentItem(parent.child(newIndex))
            else:
                self.treeWidget.setCurrentItem(parent)
        else:
            newIndex = min([removedIndex, self.treeWidget.topLevelItemCount() - 1])
            self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(newIndex))

    def __deleteHotkeys(self, theItem):
        if model.TriggerMode.HOTKEY in theItem.modes:
            self.topLevelWidget().app.hotkey_removed(theItem)

        if isinstance(theItem, model.Folder):
            for subFolder in theItem.folders:
                self.__deleteHotkeys(subFolder)

            for item in theItem.items:
                if model.TriggerMode.HOTKEY in item.modes:
                    self.topLevelWidget().app.hotkey_removed(item)
