# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018, 2020 Thomas Hess <thomas.hess@udo.edu>

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

import logging
import pathlib
import typing

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QCursor, QBrush
from PyQt5.QtWidgets import QHeaderView, QMessageBox, QFileDialog, QAction, QWidget, QMenu
from PyQt5.QtWidgets import QListWidget, QListWidgetItem

import autokey.model.folder
import autokey.model.helpers
import autokey.model.phrase
import autokey.model.script
import autokey.iomediator.keygrabber
import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants

from autokey.qtui import common as ui_common
from autokey.qtui import autokey_treewidget as ak_tree
from autokey.logger import get_logger, root_logger

logger = get_logger(__name__)
del get_logger


class CentralWidget(*ui_common.inherits_from_ui_file_with_name("centralwidget")):

    def __init__(self, parent):
        super(CentralWidget, self).__init__(parent)
        logger.debug("CentralWidget instance created.")
        self.setupUi(self)
        self.dirty = False
        self.configManager = None
        self.recorder = autokey.iomediator.keygrabber.Recorder(self.scriptPage)

        self.cutCopiedItems = []
        for column_index in range(3):
            self.treeWidget.setColumnWidth(
                column_index, cm.ConfigManager.SETTINGS[cm_constants.COLUMN_WIDTHS][column_index]
            )

        h_view = self.treeWidget.header()
        h_view.setSectionResizeMode(QHeaderView.ResizeMode(QHeaderView.Interactive | QHeaderView.ResizeToContents))

        self.logHandler = None
        self.listWidget.hide()

        self.factory = None  # type: ak_tree.WidgetItemFactory
        self.context_menu = None  # type: QMenu
        self.action_clear_log = self._create_action("edit-clear-history", "Clear Log", None, self.on_clear_log)
        self.listWidget.addAction(self.action_clear_log)
        self.action_save_log = self._create_action("edit-clear-history", "Save Log As…", None, self.on_save_log)
        self.listWidget.addAction(self.action_save_log)

    @staticmethod
    def _create_action(icon_name: str, text: str, parent: QWidget=None, to_be_called_slot_function=None) -> QAction:
        icon = QIcon.fromTheme(icon_name)
        action = QAction(icon, text, parent)
        action.triggered.connect(to_be_called_slot_function)
        return action

    def init(self, app):
        self.configManager = app.configManager
        self.logHandler = ListWidgetHandler(self.listWidget, app)
        # Create and connect the custom context menu
        self.context_menu = self._create_treewidget_context_menu()
        self.treeWidget.customContextMenuRequested.connect(lambda position: self.context_menu.popup(QCursor.pos()))

    def _create_treewidget_context_menu(self) -> QMenu:
        main_window = self.window()
        context_menu = QMenu()
        context_menu.addAction(main_window.action_create)
        context_menu.addAction(main_window.action_rename_item)
        context_menu.addAction(main_window.action_clone_item)
        context_menu.addAction(main_window.action_cut_item)
        context_menu.addAction(main_window.action_copy_item)
        context_menu.addAction(main_window.action_paste_item)
        context_menu.addSeparator()
        context_menu.addAction(main_window.action_delete_item)
        context_menu.addSeparator()
        context_menu.addAction(main_window.action_run_script)
        return context_menu

    def populate_tree(self, config):
        self.factory = ak_tree.WidgetItemFactory(config.folders)
        root_folders = self.factory.get_root_folder_list()
        for item in root_folders:
            self.treeWidget.addTopLevelItem(item)

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(0))
        self.on_treeWidget_itemSelectionChanged()

    def set_splitter(self, window_size):
        pos = cm.ConfigManager.SETTINGS[cm_constants.HPANE_POSITION]
        self.splitter.setSizes([pos, window_size.width() - pos])

    def set_dirty(self, dirty: bool):
        self.dirty = dirty

    def promptToSave(self):
        if cm.ConfigManager.SETTINGS[cm_constants.PROMPT_TO_SAVE]:
            # TODO: i18n
            result = QMessageBox.question(
                self.window(),
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

    def on_treeWidget_itemChanged(self, item, column):
        if item is self._get_current_treewidget_item() and column == 0:
            newText = str(item.text(0))
            if ui_common.validate(
                    not ui_common.EMPTY_FIELD_REGEX.match(newText),
                    "The name can't be empty.",
                    None,
                    self.window()):
                self.window().app.monitor.suspend()
                self.stack.currentWidget().set_item_title(newText)
                self.stack.currentWidget().rebuild_item_path()

                persistGlobal = self.stack.currentWidget().save()
                self.window().app.monitor.unsuspend()
                self.window().app.config_altered(persistGlobal)

                self.treeWidget.sortItems(0, Qt.AscendingOrder)
            else:
                item.update()

    def on_treeWidget_itemSelectionChanged(self):
        model_items = self.__getSelection()

        if len(model_items) == 1:
            model_item = model_items[0]
            if isinstance(model_item, autokey.model.folder.Folder):
                self.stack.setCurrentIndex(0)
                self.folderPage.load(model_item)

            elif isinstance(model_item, autokey.model.phrase.Phrase):
                self.stack.setCurrentIndex(1)
                self.phrasePage.load(model_item)

            elif isinstance(model_item, autokey.model.script.Script):
                self.stack.setCurrentIndex(2)
                self.scriptPage.load(model_item)

            self.window().update_actions(model_items, True)
            self.set_dirty(False)
            self.window().cancel_record()

        else:
            self.window().update_actions(model_items, False)

    def on_new_topfolder(self):
        logger.info("User initiates top-level folder creation")
        message_box = QMessageBox(
            QMessageBox.Question,
            "Create Folder",
            "Create folder in the default location?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            self.window()

        )
        message_box.button(QMessageBox.No).setText("Create elsewhere")  # TODO: i18n
        result = message_box.exec_()

        self.window().app.monitor.suspend()

        if result == QMessageBox.Yes:
            logger.debug("User creates a new top-level folder.")
            self.__createFolder(None)

        elif result == QMessageBox.No:
            logger.debug("User creates a new folder and chose to create it elsewhere")
            QMessageBox.warning(
                self.window(), "Beware",
                "AutoKey will take the full ownership of the directory you are about to select or create. "
                "It is advisable to only choose empty directories or directories that contain data created by AutoKey "
                "previously.\n\nIf you delete or move the directory from within AutoKey "
                "(for example by using drag and drop), all files unknown to AutoKey will be deleted.",
                QMessageBox.Ok)
            path = QFileDialog.getExistingDirectory(
                self.window(),
                "Where should the folder be created?"
            )
            if path != "":
                path = pathlib.Path(path)
                if list(path.glob("*")):
                    result = QMessageBox.warning(
                        self.window(), "The chosen directory already contains files",
                        "The selected directory already contains files. "
                        "If you continue, AutoKey will take the ownership.\n\n"
                        "You may lose all files in '{}' that are not related to AutoKey if you select this directory.\n"
                        "Continue?".format(path),
                        QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes
                else:
                    result = True
                if result:
                    folder = autokey.model.folder.Folder(path.name, path=str(path))
                    new_item = ak_tree.FolderWidgetItem(None, folder)
                    self.treeWidget.addTopLevelItem(new_item)
                    self.configManager.folders.append(folder)
                    self.window().app.config_altered(True)

            self.window().app.monitor.unsuspend()
        else:
            logger.debug("User canceled top-level folder creation.")
            self.window().app.monitor.unsuspend()

    def on_new_folder(self):
        parent_item = self._get_current_treewidget_item()
        self.__createFolder(parent_item)

    def __createFolder(self, parent_item):
        folder = autokey.model.folder.Folder("New Folder")
        new_item = ak_tree.FolderWidgetItem(parent_item, folder)
        self.window().app.monitor.suspend()

        if parent_item is not None:
            parentFolder = self.__extractData(parent_item)
            parentFolder.add_folder(folder)
        else:
            self.treeWidget.addTopLevelItem(new_item)
            self.configManager.folders.append(folder)

        folder.persist()
        self.window().app.monitor.unsuspend()

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(new_item)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()

    def on_new_phrase(self):
        self.window().app.monitor.suspend()
        tree_widget = self.treeWidget  # type: ak_tree.AkTreeWidget
        parent_item = tree_widget.selectedItems()[0]  # type: ak_tree.ItemWidgetType
        parent = self.__extractData(parent_item)

        phrase = autokey.model.phrase.Phrase("New Phrase", "Enter phrase contents")
        new_item = ak_tree.PhraseWidgetItem(parent_item, phrase)
        parent.add_item(phrase)
        phrase.persist()

        self.window().app.monitor.unsuspend()

        tree_widget.sortItems(0, Qt.AscendingOrder)
        tree_widget.setCurrentItem(new_item)
        parent_item.setSelected(False)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()

    def on_new_script(self):
        self.window().app.monitor.suspend()
        tree_widget = self.treeWidget  # type: ak_tree.AkTreeWidget
        parent_item = tree_widget.selectedItems()[0]  # type: ak_tree.ItemWidgetType
        parent = self.__extractData(parent_item)

        script = autokey.model.script.Script("New Script", "#Enter script code")
        new_item = ak_tree.ScriptWidgetItem(parent_item, script)
        parent.add_item(script)
        script.persist()

        self.window().app.monitor.unsuspend()
        tree_widget.sortItems(0, Qt.AscendingOrder)
        tree_widget.setCurrentItem(new_item)
        parent_item.setSelected(False)
        self.on_treeWidget_itemSelectionChanged()
        self.on_rename()

    def on_undo(self):
        self.stack.currentWidget().undo()

    def on_redo(self):
        self.stack.currentWidget().redo()

    def on_copy(self):
        source_objects = self.__getSelection()

        for source in source_objects:
            if isinstance(source, autokey.model.phrase.Phrase):
                new_obj = autokey.model.phrase.Phrase('', '')
            else:
                new_obj = autokey.model.script.Script('', '')
            new_obj.copy(source)
            self.cutCopiedItems.append(new_obj)

    def on_clone(self):
        source_object = self.__getSelection()[0]
        tree_widget = self.treeWidget  # type: ak_tree.AkTreeWidget
        parent_item = tree_widget.selectedItems()[0].parent()  # type: ak_tree.ItemWidgetType
        parent = self.__extractData(parent_item)

        if isinstance(source_object, autokey.model.phrase.Phrase):
            new_obj = autokey.model.phrase.Phrase('', '')
            new_obj.copy(source_object)
            new_item = ak_tree.PhraseWidgetItem(parent_item, new_obj)
        else:
            new_obj = autokey.model.script.Script('', '')
            new_obj.copy(source_object)
            new_item = ak_tree.ScriptWidgetItem(parent_item, new_obj)

        parent.add_item(new_obj)
        self.window().app.monitor.suspend()
        new_obj.persist()

        self.window().app.monitor.unsuspend()
        tree_widget.sortItems(0, Qt.AscendingOrder)
        tree_widget.setCurrentItem(new_item)
        parent_item.setSelected(False)
        self.on_treeWidget_itemSelectionChanged()
        self.window().app.config_altered(False)

    def on_cut(self):
        self.cutCopiedItems = self.__getSelection()
        self.window().app.monitor.suspend()

        source_items = self.treeWidget.selectedItems()
        result = [f for f in source_items if f.parent() not in source_items]
        for item in result:
            self.__removeItem(item)

        self.window().app.monitor.unsuspend()
        self.window().app.config_altered(False)

    def on_paste(self):
        parent_item = self._get_current_treewidget_item()
        parent = self.__extractData(parent_item)
        self.window().app.monitor.suspend()

        new_items = []
        for item in self.cutCopiedItems:
            if isinstance(item, autokey.model.folder.Folder):
                new_item = ak_tree.FolderWidgetItem(parent_item, item)
                ak_tree.WidgetItemFactory.process_folder(new_item, item)
                parent.add_folder(item)
            elif isinstance(item, autokey.model.phrase.Phrase):
                new_item = ak_tree.PhraseWidgetItem(parent_item, item)
                parent.add_item(item)
            else:
                new_item = ak_tree.ScriptWidgetItem(parent_item, item)
                parent.add_item(item)

            item.persist()

            new_items.append(new_item)

        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.treeWidget.setCurrentItem(new_items[-1])
        self.on_treeWidget_itemSelectionChanged()
        self.cutCopiedItems = []
        for item in new_items:
            item.setSelected(True)
        self.window().app.monitor.unsuspend()
        self.window().app.config_altered(False)

    def on_delete(self):
        widget_items = self.treeWidget.selectedItems()
        self.window().app.monitor.suspend()

        if len(widget_items) == 1:
            widget_item = widget_items[0]
            data = self.__extractData(widget_item)
            if isinstance(data, autokey.model.folder.Folder):
                header = "Delete Folder?"
                msg = "Are you sure you want to delete the '{deleted_folder}' folder and all the items in it?".format(
                    deleted_folder=data.title)
            else:
                entity_type = "Script" if isinstance(data, autokey.model.script.Script) else "Phrase"
                header = "Delete {}?".format(entity_type)
                msg = "Are you sure you want to delete '{element}'?".format(element=data.description)
        else:
            item_count = len(widget_items)
            header = "Delete {item_count} selected items?".format(item_count=item_count)
            msg = "Are you sure you want to delete the {item_count} selected folders/items?".format(
                item_count=item_count)
        result = QMessageBox.question(self.window(), header, msg, QMessageBox.Yes | QMessageBox.No)

        if result == QMessageBox.Yes:
            for widget_item in widget_items:
                self.__removeItem(widget_item)

        self.window().app.monitor.unsuspend()
        if result == QMessageBox.Yes:
            self.window().app.config_altered(False)

    def on_rename(self):
        widget_item = self._get_current_treewidget_item()
        self.treeWidget.editItem(widget_item, 0)

    def on_save(self):
        logger.info("User requested file save.")
        if self.stack.currentWidget().validate():
            self.window().app.monitor.suspend()
            persist_global = self.stack.currentWidget().save()
            self.window().save_completed(persist_global)
            self.set_dirty(False)
            item = self._get_current_treewidget_item()
            item.update()
            self.treeWidget.update()
            self.treeWidget.sortItems(0, Qt.AscendingOrder)
            self.window().app.monitor.unsuspend()
            return False

        return True

    def on_reset(self):
        self.stack.currentWidget().reset()
        self.set_dirty(False)
        self.window().cancel_record()

    def on_save_log(self):
        file_name, _ = QFileDialog.getSaveFileName(  # second return value contains the used file type filter.
            self.window(),
            "Save log file",
            "",
            ""  # TODO: File type filter. Maybe "*.log"?
        )
        del _  # We are only interested in the selected file name
        if file_name:
            list_widget = self.listWidget  # type: QListWidget
            item_texts = (list_widget.item(row).text() for row in range(list_widget.count()))
            log_text = "\n".join(item_texts) + "\n"
            try:
                with open(file_name, "w") as log_file:
                    log_file.write(log_text)
            except IOError:
                logger.exception("Error saving log file")
            else:
                self.on_clear_log()  # Error log saved, so clear the previously saved entries

    def on_clear_log(self):
        self.listWidget.clear()

    def move_items(self, sourceItems, target):
        target_model_item = self.__extractData(target)

        # Filter out any child objects that belong to a parent already in the list
        result = [f for f in sourceItems if f.parent() not in sourceItems]

        self.window().app.monitor.suspend()

        for source in result:
            self.__removeItem(source)
            source_model_item = self.__extractData(source)

            if isinstance(source_model_item, autokey.model.folder.Folder):
                target_model_item.add_folder(source_model_item)
                self.__moveRecurseUpdate(source_model_item)
            else:
                target_model_item.add_item(source_model_item)
                source_model_item.path = None
                source_model_item.persist()

            target.addChild(source)

        self.window().app.monitor.unsuspend()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)
        self.window().app.config_altered(True)

    def __moveRecurseUpdate(self, folder):
        folder.path = None
        folder.persist()

        for subfolder in folder.folders:
            self.__moveRecurseUpdate(subfolder)

        for child in folder.items:
            child.path = None
            child.persist()

    # ---- Private methods
    def _get_current_treewidget_item(self) -> ak_tree.ItemWidgetType:
        """
        This method gets the TreeItem instance of the currently opened Item. Normally, this is just the selected item,
        but the user can deselect it by clicking in the whitespace below the tree.
        Some functions require the TreeItem of the currently opened Item. For example when renaming it, the name in the
        tree has to be updated.
        This function makes sure to always retrieve the required TreeItem instance.
        """
        selected_items = self.treeWidget.selectedItems()  # type: typing.List[ak_tree.ItemWidgetType]
        if selected_items:
            return selected_items[0]
        else:
            # The user deselected the item, so fall back to scan the whole tree for the desired item
            currently_edited_item = self.stack.currentWidget().get_current_item()
            if currently_edited_item is None:
                raise RuntimeError("Tried to perform an action on an item, while none is opened.")

            tree = self.treeWidget  # type: ak_tree.AkTreeWidget
            item_widgets = [
                tree.topLevelItem(top_level_index) for top_level_index in range(tree.topLevelItemCount())
            ]  # type: typing.List[ak_tree.ItemWidgetType]

            # Use a queue to iterate through the whole tree.
            while item_widgets:
                item_widget = item_widgets.pop(0)
                # The actual model data is stored in column 3
                found_item = item_widget.data(3, Qt.UserRole)  # type: ak_tree.ItemType
                if found_item is currently_edited_item:  # Use identity to identify the right model instance.
                    return item_widget
                if isinstance(item_widget, ak_tree.FolderWidgetItem):
                    for child_index in range(item_widget.childCount()):
                        item_widgets.append(item_widget.child(child_index))
            raise RuntimeError("Expected item {} not found in the tree!".format(currently_edited_item))

    def get_selected_item(self):
        return self.__getSelection()

    def __getSelection(self):
        items = self.treeWidget.selectedItems()
        ret = [self.__extractData(item) for item in items]

        # Filter out any child objects that belong to a parent already in the list
        result = [f for f in ret if f.parent not in ret]
        return result

    @staticmethod
    def __extractData(item):
        variant = item.data(3, Qt.UserRole)
        return variant

    def __removeItem(self, widgetItem):
        parent = widgetItem.parent()
        item = self.__extractData(widgetItem)
        self.__deleteHotkeys(item)

        if parent is None:
            removed_index = self.treeWidget.indexOfTopLevelItem(widgetItem)
            self.treeWidget.takeTopLevelItem(removed_index)
            self.configManager.folders.remove(item)
        else:
            removed_index = parent.indexOfChild(widgetItem)
            parent.removeChild(widgetItem)

            if isinstance(item, autokey.model.folder.Folder):
                item.parent.remove_folder(item)
            else:
                item.parent.remove_item(item)

        item.remove_data()
        self.treeWidget.sortItems(0, Qt.AscendingOrder)

        if parent is not None:
            if parent.childCount() > 0:
                new_index = min((removed_index, parent.childCount() - 1))
                self.treeWidget.setCurrentItem(parent.child(new_index))
            else:
                self.treeWidget.setCurrentItem(parent)
        else:
            new_index = min((removed_index, self.treeWidget.topLevelItemCount() - 1))
            self.treeWidget.setCurrentItem(self.treeWidget.topLevelItem(new_index))

    def __deleteHotkeys(self, removed_item):
        self.configManager.delete_hotkeys(removed_item)

class ListWidgetHandler(logging.Handler):

    def __init__(self, list_widget: QListWidget, app):
        logging.Handler.__init__(self)
        self.widget = list_widget
        self.app = app
        self.level = logging.DEBUG

        log_format = "%(message)s"
        root_logger.addHandler(self)
        self.setFormatter(logging.Formatter(log_format))

    def flush(self):
        pass

    def emit(self, record):
        try:
            item = QListWidgetItem(self.format(record))
            if record.levelno > logging.INFO:
                item.setIcon(QIcon.fromTheme("dialog-warning"))
                item.setForeground(QBrush(Qt.red))

            else:
                item.setIcon(QIcon.fromTheme("dialog-information"))

            self.app.exec_in_main(self._add_item, item)

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def _add_item(self, item):
        self.widget.addItem(item)

        if self.widget.count() > 50:
            delItem = self.widget.takeItem(0)
            del delItem

        self.widget.scrollToBottom()
