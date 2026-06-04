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

import locale
import os
import threading
import time
import webbrowser

from gi import require_version

import autokey.model.folder
import autokey.model.helpers
import autokey.model.phrase
import autokey.model.script
from autokey.model.triggermode import TriggerMode

require_version('Gtk', '3.0')
require_version('GtkSource', '3.0')

from gi.repository import Gtk, Pango, GtkSource, Gdk, Gio



GETTEXT_DOMAIN = 'autokey'

locale.setlocale(locale.LC_ALL, '')


from . import dialogs
from .autocomplete import FileCompletionProvider
from .settingsdialog import SettingsDialog

import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants

import autokey.iomediator.keygrabber
from autokey import common

CONFIG_WINDOW_TITLE = "AutoKey"

UI_DESCRIPTION_FILE = os.path.join(os.path.dirname(__file__), "data/menus.xml")


logger = __import__("autokey.logger").logger.get_logger(__name__)

PROBLEM_MSG_PRIMARY = _("Some problems were found")
PROBLEM_MSG_SECONDARY = _("%s\n\nYour changes have not been saved.")

from .shared import get_ui


def set_linkbutton(button, path, filename_only=False):
    label = button.get_child()
    label.set_sensitive(True)
    
    if path.startswith(cm_constants.CONFIG_DEFAULT_FOLDER):
        text = path.replace(cm_constants.CONFIG_DEFAULT_FOLDER, _("(Default folder)"))
    else:
        text = path.replace(os.path.expanduser("~"), "~")

    if filename_only:
        filename = os.path.basename(path)
        label.set_label(filename)
    else:
        label.set_label(text)

    button.set_uri("file://" + path)
    label.set_ellipsize(Pango.EllipsizeMode.START)


class RenameDialog:

    def __init__(self, parentWindow, oldName, isNew, title=_("Rename '%s'")):
        builder = get_ui("renamedialog.xml")
        self.ui = builder.get_object("dialog")
        builder.connect_signals(self)
        self.ui.set_transient_for(parentWindow)

        self.nameEntry = builder.get_object("nameEntry")
        self.checkButton = builder.get_object("checkButton")
        self.image = builder.get_object("image")

        self.nameEntry.set_text(oldName)
        self.checkButton.set_active(True)

        if isNew:
            self.checkButton.hide()
            self.set_title(title)
        else:
            self.set_title(title % oldName)

    def get_name(self):
        return self.nameEntry.get_text()#.decode("utf-8")

    def get_update_fs(self):
        return self.checkButton.get_active()

    def set_image(self, stockId):
        self.image.set_from_stock(stockId, Gtk.IconSize.DIALOG)

    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)


class SettingsWidget:
    KEY_MAP = dialogs.HotkeySettingsDialog.KEY_MAP
    REVERSE_KEY_MAP = dialogs.HotkeySettingsDialog.REVERSE_KEY_MAP

    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("settingswidget.xml")
        self.ui = builder.get_object("settingswidget")
        builder.connect_signals(self)

        self.abbrDialog = dialogs.AbbrSettingsDialog(parentWindow.ui, parentWindow.app.configManager, self.on_abbr_response)
        self.hotkeyDialog = dialogs.HotkeySettingsDialog(parentWindow.ui, parentWindow.app.configManager, self.on_hotkey_response)
        self.filterDialog = dialogs.WindowFilterSettingsDialog(parentWindow.ui, self.on_filter_dialog_response)

        self.abbrLabel = builder.get_object("abbrLabel")
        self.clearAbbrButton = builder.get_object("clearAbbrButton")
        self.hotkeyLabel = builder.get_object("hotkeyLabel")
        self.clearHotkeyButton = builder.get_object("clearHotkeyButton")
        self.windowFilterLabel = builder.get_object("windowFilterLabel")
        self.clearFilterButton = builder.get_object("clearFilterButton")

    def load(self, item):
        self.currentItem = item

        self.abbrDialog.load(self.currentItem)
        if TriggerMode.ABBREVIATION in item.modes:
            self.abbrLabel.set_text(item.get_abbreviations())
            self.clearAbbrButton.set_sensitive(True)
            self.abbrEnabled = True
        else:
            self.abbrLabel.set_text(_("(None configured)"))
            self.clearAbbrButton.set_sensitive(False)
            self.abbrEnabled = False

        self.hotkeyDialog.load(self.currentItem)
        if TriggerMode.HOTKEY in item.modes:
            self.hotkeyLabel.set_text(item.get_hotkey_string())
            self.clearHotkeyButton.set_sensitive(True)
            self.hotkeyEnabled = True
        else:
            self.hotkeyLabel.set_text(_("(None configured)"))
            self.clearHotkeyButton.set_sensitive(False)
            self.hotkeyEnabled = False

        self.filterDialog.load(self.currentItem)
        self.filterEnabled = False
        self.clearFilterButton.set_sensitive(False)
        if item.has_filter() or item.inherits_filter():
            self.windowFilterLabel.set_text(item.get_filter_regex())

            if not item.inherits_filter():
                self.clearFilterButton.set_sensitive(True)
                self.filterEnabled = True

        else:
            self.windowFilterLabel.set_text(_("(None configured)"))

    def save(self):
        # Perform hotkey ungrab
        if TriggerMode.HOTKEY in self.currentItem.modes:
            self.parentWindow.app.hotkey_removed(self.currentItem)

        self.currentItem.set_modes([])
        if self.abbrEnabled:
            self.abbrDialog.save(self.currentItem)
        if self.hotkeyEnabled:
            self.hotkeyDialog.save(self.currentItem)
        else:
            self.currentItem.unset_hotkey()
        if self.filterEnabled:
            self.filterDialog.save(self.currentItem)
        else:
            self.currentItem.set_window_titles(None)

        if self.hotkeyEnabled:
            self.parentWindow.app.hotkey_created(self.currentItem)

    def set_dirty(self):
        self.parentWindow.set_dirty(True)

    def validate(self):
        # Start by getting all applicable information
        abbreviations, modifiers, key, filterExpression = self.get_item_details()
        # Validate
        ret = []

        configManager = self.parentWindow.app.configManager

        for abbr in abbreviations:
            unique, conflicting = configManager.check_abbreviation_unique(abbr, filterExpression, self.currentItem)
            if not unique:
                ret.append(self.build_msg_for_item_in_use(conflicting,
                                                     "abbreviation"))

        unique, conflicting = configManager.check_hotkey_unique(modifiers, key, filterExpression, self.currentItem)
        if not unique:
            ret.append(self.build_msg_for_item_in_use(conflicting, "hotkey"))

        return ret

    def get_item_details(self):
        if self.abbrEnabled:
            abbreviations = self.abbrDialog.get_abbrs()
        else:
            abbreviations = []

        if self.hotkeyEnabled:
            modifiers = self.hotkeyDialog.get_active_modifiers()
            key = self.hotkeyDialog.key
        else:
            modifiers = []
            key = None

        filterExpression = None
        if self.filterEnabled:
            filterExpression = self.filterDialog.get_filter_text()
        elif self.currentItem.parent is not None:
            r = self.currentItem.parent.get_applicable_regex(True)
            if r is not None:
                filterExpression = r.pattern
        return abbreviations, modifiers, key, filterExpression

    def build_msg_for_item_in_use(self, conflicting, itemtype):
        msg = _("The %s '%s' is already in use by the %s") % (itemtype, conflicting.get_hotkey_string(), str(conflicting))
        f = conflicting.get_applicable_regex()
        if f is not None:
            msg += _(" for windows matching '%s'.") % f.pattern
        return msg


    # ---- Signal handlers

    def on_setAbbrButton_clicked(self, widget, data=None):
        self.abbrDialog.reset_focus()
        self.abbrDialog.show()

    def on_abbr_response(self, res):
        if res == Gtk.ResponseType.OK:
            self.set_dirty()
            self.abbrEnabled = True
            self.abbrLabel.set_text(self.abbrDialog.get_abbrs_readable())
            self.clearAbbrButton.set_sensitive(True)

    def on_clearAbbrButton_clicked(self, widget, data=None):
        self.set_dirty()
        self.abbrEnabled = False
        self.clearAbbrButton.set_sensitive(False)
        self.abbrLabel.set_text(_("(None configured)"))
        self.abbrDialog.reset()

    def on_setHotkeyButton_clicked(self, widget, data=None):
        self.hotkeyDialog.show()

    def on_hotkey_response(self, res):
        if res == Gtk.ResponseType.OK:
            self.set_dirty()
            self.hotkeyEnabled = True
            key = self.hotkeyDialog.key
            modifiers = self.hotkeyDialog.get_active_modifiers()
            self.hotkeyLabel.set_text(self.currentItem.get_hotkey_string(key, modifiers))
            self.clearHotkeyButton.set_sensitive(True)

    def on_clearHotkeyButton_clicked(self, widget, data=None):
        self.set_dirty()
        self.hotkeyEnabled = False
        self.clearHotkeyButton.set_sensitive(False)
        self.hotkeyLabel.set_text(_("(None configured)"))
        self.hotkeyDialog.reset()

    def on_setFilterButton_clicked(self, widget, data=None):
        self.filterDialog.reset_focus()
        self.filterDialog.show()

    def on_clearFilterButton_clicked(self, widget, data=None):
        self.set_dirty()
        self.filterEnabled = False
        self.clearFilterButton.set_sensitive(False)
        if self.currentItem.inherits_filter():
            text = self.currentItem.parent.get_child_filter()
        else:
            text = _("(None configured)")
        self.windowFilterLabel.set_text(text)
        self.filterDialog.reset()

    def on_filter_dialog_response(self, res):
        if res == Gtk.ResponseType.OK:
            self.set_dirty()
            filterText = self.filterDialog.get_filter_text()
            if filterText != "":
                self.filterEnabled = True
                self.clearFilterButton.set_sensitive(True)
                self.windowFilterLabel.set_text(filterText)
            else:
                self.filterEnabled = False
                self.clearFilterButton.set_sensitive(False)
                if self.currentItem.inherits_filter():
                    text = self.currentItem.parent.get_child_filter()
                else:
                    text = _("(None configured)")
                self.windowFilterLabel.set_text(text)

    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)


class BlankPage:

    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("blankpage.xml")
        self.ui = builder.get_object("blankpage")

    def load(self, theFolder):
        pass

    def save(self):
        pass

    def set_item_title(self, newTitle):
        pass

    def reset(self):
        pass

    def validate(self):
        return True

    def on_modified(self, widget, data=None):
        pass

    def set_dirty(self):
        self.parentWindow.set_dirty(True)


class FolderPage:

    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("folderpage.xml")
        self.ui = builder.get_object("folderpage")
        builder.connect_signals(self)

        self.showInTrayCheckbox = builder.get_object("showInTrayCheckbox")
        self.linkButton = builder.get_object("linkButton")
        self.jsonLinkButton = builder.get_object("jsonLinkButton")
        label = self.linkButton.get_child()
        label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

        label1 = self.jsonLinkButton.get_child()
        label1.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

        vbox = builder.get_object("settingsVbox")
        self.settingsWidget = SettingsWidget(parentWindow)
        vbox.pack_start(self.settingsWidget.ui, True, True, 0)

    def load(self, theFolder):
        self.currentFolder = theFolder
        self.showInTrayCheckbox.set_active(theFolder.show_in_tray_menu)
        self.settingsWidget.load(theFolder)

        if self.is_new_item():
            self.linkButton.set_sensitive(False)
            self.linkButton.set_label(_("(Unsaved)"))
            self.jsonLinkButton.set_sensitive(False)
            self.jsonLinkButton.set_label(_("(Unsaved)"))
        else:
            set_linkbutton(self.linkButton, self.currentFolder.path)
            set_linkbutton(self.jsonLinkButton, self.currentFolder.get_json_path(), True)

    def save(self):
        self.currentFolder.show_in_tray_menu = self.showInTrayCheckbox.get_active()
        self.settingsWidget.save()
        self.currentFolder.persist()
        set_linkbutton(self.linkButton, self.currentFolder.path)

        return not self.currentFolder.path.startswith(cm_constants.CONFIG_DEFAULT_FOLDER)

    def set_item_title(self, newTitle):
        self.currentFolder.title = newTitle

    def rebuild_item_path(self):
        self.currentFolder.rebuild_path()

    def is_new_item(self):
        return self.currentFolder.path is None

    def reset(self):
        self.load(self.currentFolder)

    def validate(self):
        # Check settings
        errors = self.settingsWidget.validate()

        if errors:
            msg = PROBLEM_MSG_SECONDARY % '\n'.join(errors)
            dlg = Gtk.MessageDialog(
                self.parentWindow.ui,
                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                PROBLEM_MSG_PRIMARY
            )
            dlg.format_secondary_text(msg)
            dlg.run()
            dlg.destroy()

        return len(errors) == 0

    def on_modified(self, widget, data=None):
        self.set_dirty()

    def set_dirty(self):
        self.parentWindow.set_dirty(True)


class ScriptPage:

    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("scriptpage.xml")
        self.ui = builder.get_object("scriptpage")
        builder.connect_signals(self)

        self.buffer = GtkSource.Buffer()
        self.buffer.connect("changed", self.on_modified)
        self.editor = GtkSource.View.new_with_buffer(self.buffer)
        scrolledWindow = builder.get_object("scrolledWindow")
        scrolledWindow.add(self.editor)

        # Editor font
        settings = Gio.Settings.new("org.gnome.desktop.interface")
        fontDesc = Pango.font_description_from_string(settings.get_string("monospace-font-name"))
        self.editor.modify_font(fontDesc)

        self.promptCheckbox = builder.get_object("promptCheckbox")
        self.showInTrayCheckbox = builder.get_object("showInTrayCheckbox")
        self.linkButton = builder.get_object("linkButton")
        self.jsonLinkButton = builder.get_object("jsonLinkButton")
        label = self.linkButton.get_child()
        label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

        label1 = self.jsonLinkButton.get_child()
        label1.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

        vbox = builder.get_object("settingsVbox")
        self.settingsWidget = SettingsWidget(parentWindow)
        vbox.pack_start(self.settingsWidget.ui, False, False, 0)

        # Configure script editor
        self.__m = GtkSource.LanguageManager()
        self.__sm = GtkSource.StyleSchemeManager()
        self.buffer.set_language(self.__m.get_language("python"))
        self.buffer.set_style_scheme(self.__sm.get_scheme(cm.ConfigManager.SETTINGS[cm_constants.GTK_THEME]))
        self.editor.set_auto_indent(True)
        self.editor.set_smart_home_end(True)
        self.editor.set_insert_spaces_instead_of_tabs(True)
        self.editor.set_tab_width(4)

        self.editor_completion = self.editor.get_completion()
        #self.editor_completion.add_provider(FileCompletionProvider("./autokey/gtkui/data/api.csv"))
        macros_file = os.path.join(os.path.dirname(__file__), 'data/api.csv')
        self.editor_completion.add_provider(FileCompletionProvider(macros_file, "<"))

        self.ui.show_all()

    def load(self, theScript):
        self.currentItem = theScript

        self.buffer.begin_not_undoable_action()
        self.buffer.set_text(theScript.code)
        # self.buffer.set_text(theScript.code.encode("utf-8"))
        self.buffer.end_not_undoable_action()
        self.buffer.place_cursor(self.buffer.get_start_iter())

        self.promptCheckbox.set_active(theScript.prompt)
        self.showInTrayCheckbox.set_active(theScript.show_in_tray_menu)
        self.settingsWidget.load(theScript)

        if self.is_new_item():
            self.linkButton.set_sensitive(False)
            self.linkButton.set_label(_("(Unsaved)"))
            self.jsonLinkButton.set_sensitive(False)
            self.jsonLinkButton.set_label(_("(Unsaved)"))
        else:
            set_linkbutton(self.linkButton, self.currentItem.path)
            set_linkbutton(self.jsonLinkButton, self.currentItem.get_json_path(), True)

    def save(self):
        self.currentItem.code = self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter(), False)

        self.currentItem.prompt = self.promptCheckbox.get_active()
        self.currentItem.show_in_tray_menu = self.showInTrayCheckbox.get_active()

        self.settingsWidget.save()
        self.currentItem.persist()
        set_linkbutton(self.linkButton, self.currentItem.path)

        return False

    def set_item_title(self, newTitle):
        self.currentItem.description = newTitle

    def rebuild_item_path(self):
        self.currentItem.rebuild_path()

    def is_new_item(self):
        return self.currentItem.path is None

    def reset(self):
        self.load(self.currentItem)
        self.parentWindow.set_undo_available(False)
        self.parentWindow.set_redo_available(False)

    def validate(self):
        errors = []

        # Check script code        
        text = self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter(), False)
        if dialogs.EMPTY_FIELD_REGEX.match(text):
            errors.append(_("The script code can't be empty"))

        # Check settings
        errors += self.settingsWidget.validate()

        if errors:
            msg = PROBLEM_MSG_SECONDARY % '\n'.join(errors)
            dlg = Gtk.MessageDialog(
                self.parentWindow.ui,
                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                PROBLEM_MSG_PRIMARY
            )
            dlg.format_secondary_text(msg)
            dlg.run()
            dlg.destroy()

        return len(errors) == 0

    def record_keystrokes(self, isActive):
        if isActive:
            self.recorder = autokey.iomediator.keygrabber.Recorder(self)
            dlg = dialogs.RecordDialog(self.parentWindow.ui, self.on_rec_response)
            dlg.run()
        else:
            self.recorder.stop()

    def on_rec_response(self, response, recKb, recMouse, delay):
        if response == Gtk.ResponseType.OK:
            self.recorder.set_record_keyboard(recKb)
            self.recorder.set_record_mouse(recMouse)
            self.recorder.start(delay)
        elif response == Gtk.ResponseType.CANCEL:
            self.parentWindow.record_stopped()

    def cancel_record(self):
        self.recorder.stop()

    def start_record(self):
        self.buffer.insert(self.buffer.get_end_iter(), "\n")

    def start_key_sequence(self):
        self.buffer.insert(self.buffer.get_end_iter(), "keyboard.send_keys(\"")

    def end_key_sequence(self):
        self.buffer.insert(self.buffer.get_end_iter(), "\")\n")

    def append_key(self, key):
        #line, pos = self.buffer.getCursorPosition()
        self.buffer.insert(self.buffer.get_end_iter(), key)
        #self.scriptCodeEditor.setCursorPosition(line, pos + len(key))

    def append_hotkey(self, key, modifiers):
        #line, pos = self.scriptCodeEditor.getCursorPosition()
        keyString = self.currentItem.get_hotkey_string(key, modifiers)
        self.buffer.insert(self.buffer.get_end_iter(), keyString)
        #self.scriptCodeEditor.setCursorPosition(line, pos + len(keyString))

    def append_mouseclick(self, xCoord, yCoord, button, windowTitle):
        self.buffer.insert(self.buffer.get_end_iter(), "mouse.click_relative(%d, %d, %d) # %s\n" % (xCoord, yCoord, int(button), windowTitle))

    def undo(self):
        self.buffer.undo()
        self.parentWindow.set_undo_available(self.buffer.can_undo())
        self.parentWindow.set_redo_available(self.buffer.can_redo())

    def redo(self):
        self.buffer.redo()
        self.parentWindow.set_undo_available(self.buffer.can_undo())
        self.parentWindow.set_redo_available(self.buffer.can_redo())

    def on_modified(self, widget, data=None):
        self.set_dirty()
        self.parentWindow.set_undo_available(self.buffer.can_undo())
        self.parentWindow.set_redo_available(self.buffer.can_redo())

    def set_dirty(self):
        self.parentWindow.set_dirty(True)


class PhrasePage(ScriptPage):

    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        builder = get_ui("phrasepage.xml")
        self.ui = builder.get_object("phrasepage")
        builder.connect_signals(self)

        self.buffer = GtkSource.Buffer()
        self.buffer.connect("changed", self.on_modified)
        self.editor = GtkSource.View.new_with_buffer(self.buffer)

        self.editor_completion = self.editor.get_completion()
        #self.editor_completion.add_provider(FileCompletionProvider("./autokey/gtkui/data/macros.csv", "<"))
        macros_file = os.path.join(os.path.dirname(__file__), 'data/macros.csv')
        self.editor_completion.add_provider(FileCompletionProvider(macros_file, "<"))

        scrolledWindow = builder.get_object("scrolledWindow")
        scrolledWindow.add(self.editor)
        self.promptCheckbox = builder.get_object("promptCheckbox")
        self.showInTrayCheckbox = builder.get_object("showInTrayCheckbox")
        self.sendModeCombo = Gtk.ComboBoxText.new()
        self.sendModeCombo.connect("changed", self.on_modified)
        sendModeHbox = builder.get_object("sendModeHbox")
        sendModeHbox.pack_start(self.sendModeCombo, False, False, 0)

        self.linkButton = builder.get_object("linkButton")
        self.jsonLinkButton = builder.get_object("jsonLinkButton")

        vbox = builder.get_object("settingsVbox")
        self.settingsWidget = SettingsWidget(parentWindow)
        vbox.pack_start(self.settingsWidget.ui, False, False, 0)

        # Populate combo
        l = list(autokey.model.phrase.SEND_MODES.keys())
        l.sort()
        for val in l:
            self.sendModeCombo.append_text(val)

        # Configure script editor
        #self.__m = GtkSource.LanguageManager()
        self.__sm = GtkSource.StyleSchemeManager()
        self.buffer.set_language(None)
        self.buffer.set_style_scheme(self.__sm.get_scheme(cm.ConfigManager.SETTINGS[cm_constants.GTK_THEME]))
        self.buffer.set_highlight_matching_brackets(False)
        self.editor.set_auto_indent(False)
        self.editor.set_smart_home_end(False)
        self.editor.set_insert_spaces_instead_of_tabs(True)
        self.editor.set_tab_width(4)

        self.ui.show_all()

    def insert_text(self, text):
        self.buffer.insert_at_cursor(text)
        # self.buffer.insert_at_cursor(text.encode("utf-8"))

    def load(self, thePhrase):
        self.currentItem = thePhrase

        self.buffer.begin_not_undoable_action()
        self.buffer.set_text(thePhrase.phrase)
        # self.buffer.set_text(thePhrase.phrase.encode("utf-8"))
        self.buffer.end_not_undoable_action()
        self.buffer.place_cursor(self.buffer.get_start_iter())

        self.promptCheckbox.set_active(thePhrase.prompt)
        self.showInTrayCheckbox.set_active(thePhrase.show_in_tray_menu)
        self.settingsWidget.load(thePhrase)

        if self.is_new_item():
            self.linkButton.set_sensitive(False)
            self.linkButton.set_label(_("(Unsaved)"))
            self.jsonLinkButton.set_sensitive(False)
            self.jsonLinkButton.set_label(_("(Unsaved)"))
        else:
            set_linkbutton(self.linkButton, self.currentItem.path)
            set_linkbutton(self.jsonLinkButton, self.currentItem.get_json_path(), True)

        l = list(autokey.model.phrase.SEND_MODES.keys())
        l.sort()
        for k, v in autokey.model.phrase.SEND_MODES.items():
            if v == thePhrase.sendMode:
                self.sendModeCombo.set_active(l.index(k))
                break


    def save(self):
        self.currentItem.phrase = self.buffer.get_text(self.buffer.get_start_iter(),
                                                        self.buffer.get_end_iter(), False)#.decode("utf-8")

        self.currentItem.prompt = self.promptCheckbox.get_active()
        self.currentItem.show_in_tray_menu = self.showInTrayCheckbox.get_active()
        self.currentItem.sendMode = autokey.model.phrase.SEND_MODES[self.sendModeCombo.get_active_text()]

        self.settingsWidget.save()
        self.currentItem.persist()
        set_linkbutton(self.linkButton, self.currentItem.path)
        return False

    def validate(self):
        errors = []

        # Check phrase content
        text = self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter(), False)#.decode("utf-8")
        if dialogs.EMPTY_FIELD_REGEX.match(text):
            errors.append(_("The phrase content can't be empty"))

        # Check settings
        errors += self.settingsWidget.validate()

        if errors:
            msg = PROBLEM_MSG_SECONDARY % '\n'.join(errors)
            dlg = Gtk.MessageDialog(self.parentWindow.ui, Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR,
                                     Gtk.ButtonsType.OK, PROBLEM_MSG_PRIMARY)
            dlg.format_secondary_text(msg)
            dlg.run()
            dlg.destroy()

        return len(errors) == 0

    def record_keystrokes(self, isActive):
        if isActive:
            msg = _("AutoKey will now take exclusive use of the keyboard.\n\nClick the mouse anywhere to release the keyboard when you are done.")
            dlg = Gtk.MessageDialog(self.parentWindow.ui, Gtk.DialogFlags.MODAL, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, msg)
            dlg.set_title(_("Record Keystrokes"))
            dlg.run()
            dlg.destroy()
            self.editor.set_sensitive(False)
            self.recorder = autokey.iomediator.keygrabber.Recorder(self)
            self.recorder.set_record_keyboard(True)
            self.recorder.set_record_mouse(True)
            self.recorder.start_withgrab()
        else:
            self.recorder.stop()
            self.editor.set_sensitive(True)

    def start_record(self):
        pass

    def start_key_sequence(self):
        pass

    def end_key_sequence(self):
        pass

    def append_key(self, key):
        #line, pos = self.buffer.getCursorPosition()
        self.buffer.insert(self.buffer.get_end_iter(), key)
        #self.scriptCodeEditor.setCursorPosition(line, pos + len(key))

    def append_hotkey(self, key, modifiers):
        #line, pos = self.scriptCodeEditor.getCursorPosition()
        keyString = self.currentItem.get_hotkey_string(key, modifiers)
        self.buffer.insert(self.buffer.get_end_iter(), keyString)
        #self.scriptCodeEditor.setCursorPosition(line, pos + len(keyString))

    def append_mouseclick(self, xCoord, yCoord, button, windowTitle):
        self.cancel_record()
        self.parentWindow.record_stopped()

    def cancel_record(self):
        self.recorder.stop_withgrab()
        self.editor.set_sensitive(True)


class ConfigWindow:

    def __init__(self, app):
        self.app = app
        self.cutCopiedItems = []
        self.__warnedOfChanges = False

        builder = get_ui("mainwindow.xml")
        self.ui = builder.get_object("mainwindow")
        self.ui.set_title(CONFIG_WINDOW_TITLE)

        # Menus and Actions
        self.uiManager = Gtk.UIManager()
        self.add_accel_group(self.uiManager.get_accel_group())

        # Menu Bar
        actionGroup = Gtk.ActionGroup("menu")
        actions = [
            ("File", None, _("_File")),
            ("create", None, _("New")),
            ("new-top-folder", "folder-new", _("_Folder"), "", _("Create a new top-level folder"), self.on_new_topfolder),
            ("new-folder", "folder-new", _("Subf_older"), "", _("Create a new folder in the current folder"), self.on_new_folder),
            ("new-phrase", "text-x-generic", _("_Phrase"), "<control>n", _("Create a new phrase in the current folder"), self.on_new_phrase),
            ("new-script", "text-x-python", _("Scrip_t"), "<control><shift>n", _("Create a new script in the current folder"), self.on_new_script),
            ("save", Gtk.STOCK_SAVE, _("_Save"), None, _("Save changes to current item"), self.on_save),
            ("revert", Gtk.STOCK_REVERT_TO_SAVED, _("_Revert"), None, _("Drop all unsaved changes to current item"), self.on_revert),
            ("close-window", Gtk.STOCK_CLOSE, _("_Close window"), None, _("Close the configuration window"), self.on_close),
            ("quit", Gtk.STOCK_QUIT, _("_Quit"), None, _("Completely exit AutoKey"), self.on_quit),
            ("Edit", None, _("_Edit")),
            ("cut-item", Gtk.STOCK_CUT, _("Cu_t Item"), "", _("Cut the selected item"), self.on_cut_item),
            ("copy-item", Gtk.STOCK_COPY, _("_Copy Item"), "", _("Copy the selected item"), self.on_copy_item),
            ("paste-item", Gtk.STOCK_PASTE, _("_Paste Item"), "", _("Paste the last cut/copied item"), self.on_paste_item),
            ("clone-item", Gtk.STOCK_COPY, _("C_lone Item"), "<control><shift>c", _("Clone the selected item"), self.on_clone_item),
            ("delete-item", Gtk.STOCK_DELETE, _("_Delete Item"), "<control>d", _("Delete the selected item"), self.on_delete_item),
            ("rename", None, _("_Rename"), "F2", _("Rename the selected item"), self.on_rename),
            ("undo", Gtk.STOCK_UNDO, _("_Undo"), "<control>z", _("Undo the last edit"), self.on_undo),
            ("redo", Gtk.STOCK_REDO, _("_Redo"), "<control><shift>z", _("Redo the last undone edit"), self.on_redo),
            ("insert-macro", None, _("_Insert Macro"), None, _("Insert a phrase macro"), None),
            ("preferences", Gtk.STOCK_PREFERENCES, _("_Preferences"), "", _("Additional options"), self.on_advanced_settings),
            ("Tools", None, _("_Tools")),
            ("script-error", Gtk.STOCK_DIALOG_ERROR, _("Vie_w script error"), None, _("View script error information"), self.on_show_error),
            ("run", Gtk.STOCK_MEDIA_PLAY, _("_Run current script"), "F5", _("Run the currently selected script"), self.on_run_script),
            ("Help", None, _("_Help")),
            ("faq", None, _("_F.A.Q."), None, _("Display Frequently Asked Questions"), self.on_show_faq),
            ("help", Gtk.STOCK_HELP, _("Online _Help"), None, _("Display Online Help"), self.on_show_help),
            ("api", None, _("_Scripting Help"), None, _("Display Scripting API"), self.on_show_api),
            ("report-bug", None, _("Report a Bug"), "", _("Report a Bug"), self.on_report_bug),
            ("about", Gtk.STOCK_ABOUT, _("About AutoKey"), None, _("Show program information"), self.on_show_about),
        ]
        actionGroup.add_actions(actions)

        toggleActions = [
            ("toolbar", None, _("_Show Toolbar"), None, _("Show/hide the toolbar"), self.on_toggle_toolbar),
            ("record", Gtk.STOCK_MEDIA_RECORD, _("R_ecord keyboard/mouse"), None, _("Record keyboard/mouse actions"), self.on_record_keystrokes),
        ]
        actionGroup.add_toggle_actions(toggleActions)

        self.uiManager.insert_action_group(actionGroup, 0)
        self.uiManager.add_ui_from_file(UI_DESCRIPTION_FILE)
        self.vbox = builder.get_object("vbox")
        self.vbox.pack_end(self.uiManager.get_widget("/MenuBar"), False, False, 0)

        # Macro menu
        menu = self.app.service.phraseRunner.macroManager.get_menu(self.on_insert_macro)
        self.uiManager.get_widget("/MenuBar/Edit/insert-macro").set_submenu(menu)

        # Toolbar 'create' button 
        create = Gtk.MenuToolButton.new_from_stock(Gtk.STOCK_NEW)
        create.show()
        create.set_is_important(True)
        create.connect("clicked", self.on_new_clicked)
        menu = self.uiManager.get_widget('/NewDropdown')
        create.set_menu(menu)
        toolbar = self.uiManager.get_widget('/Toolbar')
        toolbar.insert(create, 0)
        self.uiManager.get_action("/MenuBar/Tools/toolbar").set_active(cm.ConfigManager.SETTINGS[cm_constants.SHOW_TOOLBAR])
        toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

        self.expanded_rows = cm.ConfigManager.SETTINGS[cm_constants.GTK_TREE_VIEW_EXPANDED_ROWS]
        self.last_open = cm.ConfigManager.SETTINGS[cm_constants.PATH_LAST_OPEN]

        self.treeView = builder.get_object("treeWidget")
        self.__initTreeWidget()

        self.stack = builder.get_object("stack")
        self.__initStack()

        self.hpaned = builder.get_object("hpaned")

        self.uiManager.get_widget("/Toolbar/save").set_is_important(True)
        self.uiManager.get_widget("/Toolbar/undo").set_is_important(True)

        builder.connect_signals(self)

        rootIter = self.treeView.get_model().get_iter_first()
        if rootIter is not None:
            self.treeView.get_selection().select_path(self.last_open)

        self.on_tree_selection_changed(self.treeView)

        self.treeView.columns_autosize()

        width, height = cm.ConfigManager.SETTINGS[cm_constants.WINDOW_DEFAULT_SIZE]
        self.set_default_size(width, height)
        self.hpaned.set_position(cm.ConfigManager.SETTINGS[cm_constants.HPANE_POSITION])

    def __addToolbar(self):
        toolbar = self.uiManager.get_widget('/Toolbar')
        self.vbox.pack_end(toolbar, False, False, 0)
        self.vbox.reorder_child(toolbar, 1)

    def record_stopped(self):
        self.uiManager.get_widget("/MenuBar/Tools/record").set_active(False)

    def cancel_record(self):
        if self.uiManager.get_widget("/MenuBar/Tools/record").get_active():
            self.record_stopped()
            self.__getCurrentPage().cancel_record()

    def save_completed(self, persistGlobal):
        self.uiManager.get_action("/MenuBar/File/save").set_sensitive(False)
        self.app.config_altered(persistGlobal)

    def set_dirty(self, dirty):
        self.dirty = dirty
        self.uiManager.get_action("/MenuBar/File/save").set_sensitive(dirty)
        self.uiManager.get_action("/MenuBar/File/revert").set_sensitive(dirty)

    def config_modified(self):
        logger.info("Modifications detected to open files. Reloading...")
        #save tree view selection
        selection = self.treeView.get_selection()
        selection.get_selected_rows()
        self.rebuild_tree()
        #get selection for new treeview
        selection = self.treeView.get_selection()
        path = Gtk.TreePath()
        for row in self.expanded_rows:
            self.treeView.expand_to_path(path.new_from_string(row))
        selection.select_path(path.new_from_string(self.last_open))
        self.on_tree_selection_changed(self.treeView)

    def update_actions(self, items, changed):
        if len(items) == 0:
            canCreate = False
            canCopy = False
            canRecord = False
            canMacro = False
            canPlay = False
            enableAny = False
            hasError = False
        else:
            canCreate = isinstance(items[0], autokey.model.folder.Folder) and len(items) == 1
            canCopy = True
            canRecord = (not isinstance(items[0], autokey.model.folder.Folder)) and len(items) == 1
            canMacro = isinstance(items[0], autokey.model.phrase.Phrase) and len(items) == 1
            canPlay = isinstance(items[0], autokey.model.script.Script) and len(items) == 1
            enableAny = True
            hasError = self.app.service.scriptRunner.error_records
                
            for item in items:
                if isinstance(item, autokey.model.folder.Folder):
                    canCopy = False
                    break

        self.uiManager.get_action("/MenuBar/Edit/copy-item").set_sensitive(canCopy)
        self.uiManager.get_action("/MenuBar/Edit/cut-item").set_sensitive(enableAny)
        self.uiManager.get_action("/MenuBar/Edit/clone-item").set_sensitive(canCopy)
        self.uiManager.get_action("/MenuBar/Edit/paste-item").set_sensitive(len(self.cutCopiedItems) > 0)
        self.uiManager.get_action("/MenuBar/Edit/delete-item").set_sensitive(enableAny)
        self.uiManager.get_action("/MenuBar/Edit/rename").set_sensitive(enableAny)
        self.uiManager.get_action("/MenuBar/Edit/insert-macro").set_sensitive(canMacro)
        self.uiManager.get_action("/MenuBar/Tools/record").set_sensitive(canRecord)
        self.uiManager.get_action("/MenuBar/Tools/run").set_sensitive(canPlay)
        self.uiManager.get_action("/MenuBar/Tools/script-error").set_sensitive(hasError)

        if changed:
            self.uiManager.get_action("/MenuBar/File/save").set_sensitive(False)
            self.uiManager.get_action("/MenuBar/Edit/undo").set_sensitive(False)
            self.uiManager.get_action("/MenuBar/Edit/redo").set_sensitive(False)

    def set_has_errors(self, state):
        self.uiManager.get_action("/MenuBar/Tools/script-error").set_sensitive(state)

    def set_undo_available(self, state):
        self.uiManager.get_action("/MenuBar/Edit/undo").set_sensitive(state)

    def set_redo_available(self, state):
        self.uiManager.get_action("/MenuBar/Edit/redo").set_sensitive(state)

    def rebuild_tree(self):
        self.treeView.set_model(AkTreeModel(self.app.configManager.folders))


    def refresh_tree(self):
        model, selectedPaths = self.treeView.get_selection().get_selected_rows()
        for path in selectedPaths:
            model.update_item(model[path].iter, self.__getTreeSelection())

    # ---- Signal handlers ----

    def on_new_clicked(self, widget, data=None):
        widget.get_menu().popup(None, None, None, None, 1, Gtk.get_current_event_time())

    def on_save(self, widget, data=None):
        if self.__getCurrentPage().validate():
            self.app.monitor.suspend()
            persistGlobal = self.__getCurrentPage().save()
            self.save_completed(persistGlobal)
            self.set_dirty(False)

            self.refresh_tree()
            self.app.monitor.unsuspend()
            return False

        return True

    def on_revert(self, widget, data=None):
        self.__getCurrentPage().reset()
        self.set_dirty(False)
        self.cancel_record()

    def queryClose(self):
        if self.dirty:
            return self.promptToSave()

        return False

    def on_close(self, widget, data=None):
        cm.ConfigManager.SETTINGS[cm_constants.WINDOW_DEFAULT_SIZE] = self.get_size()
        cm.ConfigManager.SETTINGS[cm_constants.HPANE_POSITION] = self.hpaned.get_position()
        cm.ConfigManager.SETTINGS[cm_constants.GTK_TREE_VIEW_EXPANDED_ROWS] = self.expanded_rows
        cm.ConfigManager.SETTINGS[cm_constants.PATH_LAST_OPEN] = self.last_open
        self.cancel_record()
        if self.queryClose():
            return True
        else:
            self.hide()
            self.destroy()
            self.app.configWindow = None
            self.app.config_altered(True)

    def on_quit(self, widget, data=None):
        #if not self.queryClose():
        cm.ConfigManager.SETTINGS[cm_constants.WINDOW_DEFAULT_SIZE] = self.get_size()
        cm.ConfigManager.SETTINGS[cm_constants.HPANE_POSITION] = self.hpaned.get_position()
        cm.ConfigManager.SETTINGS[cm_constants.GTK_TREE_VIEW_EXPANDED_ROWS] = self.expanded_rows
        cm.ConfigManager.SETTINGS[cm_constants.PATH_LAST_OPEN] = self.last_open
        self.app.shutdown()

    # File Menu

    def on_new_topfolder(self, widget, data=None):
        dlg = Gtk.FileChooserDialog(_("Create New Folder"), self.ui)
        dlg.set_action(Gtk.FileChooserAction.CREATE_FOLDER)
        dlg.set_local_only(True)
        dlg.add_buttons(_("Use Default"), Gtk.ResponseType.NONE, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        response = dlg.run()
        if response == Gtk.ResponseType.OK:
            path = dlg.get_filename()
            self.__createFolder(os.path.basename(path), None, path)
            self.app.monitor.add_watch(path)
            dlg.destroy()
            self.app.config_altered(True)
        elif response == Gtk.ResponseType.NONE:
            dlg.destroy()
            name = self.__getNewItemName("Folder")
            self.__createFolder(name, None)
            self.app.config_altered(True)
        else:
            dlg.destroy()

    def __getRealParent(self, parentIter):
        theModel = self.treeView.get_model()
        parentModelItem = theModel.get_value(parentIter, AkTreeModel.OBJECT_COLUMN)
        if not isinstance(parentModelItem, autokey.model.folder.Folder):
            return theModel.iter_parent(parentIter)

        return parentIter

    def on_new_folder(self, widget, data=None):
        name = self.__getNewItemName("Folder")
        if name is not None:
            theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
            parentIter = self.__getRealParent(theModel[selectedPaths[0]].iter)
            self.__createFolder(name, parentIter)
            self.app.config_altered(False)

    def __createFolder(self, title, parentIter, path=None):
        self.app.monitor.suspend()
        newFolder = autokey.model.folder.Folder(title, path=path)
        theModel = self.treeView.get_model()
        newIter = theModel.append_item(newFolder, parentIter)
        newFolder.persist()
        self.__expand_and_select_new_item(newIter, theModel)

    def __expand_and_select_new_item(self, item, theModel):
        self.app.monitor.unsuspend()
        self.treeView.expand_to_path(theModel.get_path(item))
        self.__change_selected_item(item)

    def __change_selected_item(self, item):
        self.treeView.get_selection().unselect_all()
        self.treeView.get_selection().select_iter(item)
        self.on_tree_selection_changed(self.treeView)

    def __getNewItemName(self, itemType):
        dlg = RenameDialog(self.ui, "New %s" % itemType, True, _("Create New %s") % itemType)
        dlg.set_image(Gtk.STOCK_NEW)

        if dlg.run() == 1:
            newText = dlg.get_name()
            if dialogs.validate(not dialogs.EMPTY_FIELD_REGEX.match(newText), _("The name can't be empty"),
                             None, self.ui):
                dlg.destroy()
                return newText
            else:
                dlg.destroy()
                return None

        dlg.destroy()
        return None

    def on_new_phrase(self, widget, data=None):
        name = self.__getNewItemName("Phrase")
        if name is not None:
            newIter = self.__add_new_scriptphrase(name, isScriptNotPhrase=False)
            self.__expand_and_select_new_iter(newIter)

    def on_new_script(self, widget, data=None):
        name = self.__getNewItemName("Script")
        if name is not None:
            newIter = self.__add_new_scriptphrase(name, isScriptNotPhrase=True)
            self.__expand_and_select_new_iter(newIter)

    def __add_new_scriptphrase(self, name, isScriptNotPhrase=True):
        self.app.monitor.suspend()
        if isScriptNotPhrase:
            scriptphrase = autokey.model.script.Script(name, "# Enter script code")
        else:
            scriptphrase = autokey.model.phrase.Phrase(name, "Enter phrase contents")
        theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
        parentIter = self.__getRealParent(theModel[selectedPaths[0]].iter)
        newIter = theModel.append_item(scriptphrase, parentIter)
        scriptphrase.persist()
        return newIter


    # Edit Menu

    def on_cut_item(self, widget, data=None):
        self.cutCopiedItems = self.__getTreeSelection()
        selection = self.treeView.get_selection()
        theModel, selectedPaths = selection.get_selected_rows()
        refs = []
        for path in selectedPaths:
            refs.append(Gtk.TreeRowReference(theModel, path))

        for ref in refs:
            if ref.valid():
                self.__removeItem(theModel, theModel[ref.get_path()].iter)

        if len(selectedPaths) > 1:
            self.__change_selected_item(theModel.get_iter_first())

        self.app.config_altered(True)

    def on_copy_item(self, widget, data=None):
        sourceObjects = self.__getTreeSelection()

        for source in sourceObjects:
            if isinstance(source, autokey.model.phrase.Phrase):
                newObj = autokey.model.phrase.Phrase('', '')
            else:
                newObj = autokey.model.script.Script('', '')
            newObj.copy(source)
            self.cutCopiedItems.append(newObj)

    def on_paste_item(self, widget, data=None):
        theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
        parentIter = self.__getRealParent(theModel[selectedPaths[0]].iter)
        self.app.monitor.suspend()

        newIters = []
        for item in self.cutCopiedItems:
            newIter = theModel.append_item(item, parentIter)
            if isinstance(item, autokey.model.folder.Folder):
                theModel.populate_store(newIter, item)
            newIters.append(newIter)
            item.path = None
            item.persist()

        self.app.monitor.unsuspend()

        self.treeView.expand_to_path(theModel.get_path(newIters[-1]))
        self.treeView.get_selection().unselect_all()
        self.treeView.get_selection().select_iter(newIters[0])
        self.cutCopiedItems = []
        self.on_tree_selection_changed(self.treeView)
        for iterator in newIters:
            self.treeView.get_selection().select_iter(iterator)
        self.app.config_altered(True)

    def on_clone_item(self, widget, data=None):
        source = self.__getTreeSelection()[0]
        theModel, selectedPaths = self.treeView.get_selection().get_selected_rows()
        sourceIter = theModel[selectedPaths[0]].iter
        parentIter = theModel.iter_parent(sourceIter)
        self.app.monitor.suspend()

        if isinstance(source, autokey.model.phrase.Phrase):
            newObj = autokey.model.phrase.Phrase('', '')
        else:
            newObj = autokey.model.script.Script('', '')
        newObj.copy(source)
        newObj.persist()

        self.app.monitor.unsuspend()
        newIter = theModel.append_item(newObj, parentIter)
        self.treeView.get_selection().unselect_all()
        self.treeView.get_selection().select_iter(newIter)
        self.on_tree_selection_changed(self.treeView)
        self.app.config_altered(False)

    def on_delete_item(self, widget, data=None):
        selection = self.treeView.get_selection()
        theModel, selectedPaths = selection.get_selected_rows()
        refs = []
        for path in selectedPaths:
            refs.append(Gtk.TreeRowReference.new(theModel, path))

        modified = False

        if len(refs) == 1:
            item = theModel[refs[0].get_path()].iter
            modelItem = theModel.get_value(item, AkTreeModel.OBJECT_COLUMN)
            if isinstance(modelItem, autokey.model.folder.Folder):
                msg = _("Are you sure you want to delete the %s and all the items in it?") % str(modelItem)
            else:
                msg = _("Are you sure you want to delete the %s?") % str(modelItem)
        else:
            msg = _("Are you sure you want to delete the %d selected items?") % len(refs)

        dlg = Gtk.MessageDialog(self.ui, Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, msg)
        dlg.set_title(_("Delete"))
        if dlg.run() == Gtk.ResponseType.YES:
            self.app.monitor.suspend()
            for ref in refs:
                if ref.valid():
                    item = theModel[ref.get_path()].iter
                    modelItem = theModel.get_value(item, AkTreeModel.OBJECT_COLUMN)
                    self.__removeItem(theModel, item)
                    modified = True
            self.app.monitor.unsuspend()

        dlg.destroy()

        if modified:
            if len(selectedPaths) > 1:
                self.__change_selected_item(theModel.get_iter_first())

            self.app.config_altered(True)

    def __removeItem(self, model, item):
        #selection = self.treeView.get_selection()
        #model, selectedPaths = selection.get_selected_rows()
        #parentIter = model.iter_parent(model[selectedPaths[0]].iter)
        parentIter = model.iter_parent(item)
        nextIter = model.iter_next(item)

        data = model.get_value(item, AkTreeModel.OBJECT_COLUMN)
        self.__deleteHotkeys(data)

        model.remove_item(item)

        if nextIter is not None:
            self.treeView.get_selection().select_iter(nextIter)
        elif parentIter is not None:
            self.treeView.get_selection().select_iter(parentIter)
        elif model.iter_n_children(None) > 0:
            selectIter = model.iter_nth_child(None, model.iter_n_children(None) - 1)
            self.treeView.get_selection().select_iter(selectIter)

        self.on_tree_selection_changed(self.treeView)

    def __deleteHotkeys(self, theItem):
        self.app.configManager.delete_hotkeys(theItem)

    def on_undo(self, widget, data=None):
        self.__getCurrentPage().undo()

    def on_redo(self, widget, data=None):
        self.__getCurrentPage().redo()

    def on_insert_macro(self, widget, macro):
        token = macro.get_token()
        self.phrasePage.insert_text(token)

    def on_advanced_settings(self, widget, data=None):
        s = SettingsDialog(self.ui, self.app.configManager)
        s.show()

    def on_record_keystrokes(self, widget, data=None):
        self.__getCurrentPage().record_keystrokes(widget.get_active())

    # Tools Menu

    def on_toggle_toolbar(self, widget, data=None):
        if widget.get_active():
            self.__addToolbar()
        else:
            self.vbox.remove(self.uiManager.get_widget('/Toolbar'))

        cm.ConfigManager.SETTINGS[cm_constants.SHOW_TOOLBAR] = widget.get_active()

    def on_show_error(self, widget, data=None):
        self.app.show_script_error(self.ui)

    def on_run_script(self, widget, data=None):
        t = threading.Thread(target=self.__runScript)
        t.start()

    def __runScript(self):
        script = self.__getTreeSelection()[0]
        time.sleep(2)
        self.app.service.scriptRunner.execute_script(script)

    # Help Menu

    def on_show_faq(self, widget, data=None):
        webbrowser.open(common.FAQ_URL, False, True)

    def on_show_help(self, widget, data=None):
        webbrowser.open(common.HELP_URL, False, True)

    def on_show_api(self, widget, data=None):
        webbrowser.open(common.API_URL, False, True)

    def on_report_bug(self, widget, data=None):
        webbrowser.open(common.BUG_URL, False, True)

    def on_show_about(self, widget, data=None):
        dlg = Gtk.AboutDialog()
        dlg.set_name("AutoKey")
        dlg.set_comments(_("A desktop automation utility for Linux, Wayland and X11."))
        dlg.set_version(common.VERSION)
        p = Gtk.IconTheme.get_default().load_icon(common.ICON_FILE, 100, 0)
        dlg.set_logo(p)
        dlg.set_website(common.HOMEPAGE)
        authors_list = []
        for author in common.author_data:
            authors_list.append(f"{author.name} ({author.role}) <{author.email}>")
        dlg.set_authors(authors_list)
        dlg.set_transient_for(self.ui)
        dlg.run()
        dlg.destroy()

    # Tree widget

    def on_rename(self, widget, data=None):
        selection = self.treeView.get_selection()
        theModel, selectedPaths = selection.get_selected_rows()
        selection.unselect_all()
        self.treeView.set_cursor(selectedPaths[0], self.treeView.get_column(0), False)
        selectedObject = self.__getTreeSelection()[0]
        if isinstance(selectedObject, autokey.model.folder.Folder):
            oldName = selectedObject.title
        else:

            oldName = selectedObject.description

        dlg = RenameDialog(self.ui, oldName, False)
        dlg.set_image(Gtk.STOCK_EDIT)

        if dlg.run() == 1:
            newText = dlg.get_name()
            if dialogs.validate(not dialogs.EMPTY_FIELD_REGEX.match(newText), _("The name can't be empty"),
                             None, self.ui):
                self.__getCurrentPage().set_item_title(newText)

                self.app.monitor.suspend()

                if dlg.get_update_fs():
                    self.__getCurrentPage().rebuild_item_path()

                persistGlobal = self.__getCurrentPage().save()
                self.refresh_tree()
                self.app.monitor.unsuspend()
                self.app.config_altered(persistGlobal)

        dlg.destroy()

    def on_treeWidget_row_activated(self, widget, path, viewColumn, data=None):
        """This function is called when a row is double clicked"""
        if widget.row_expanded(path):
            widget.collapse_row(path)
        else:
            widget.expand_row(path, False)

    def on_treeWidget_row_collapsed(self, widget, tIter, path, data=None):
        widget.columns_autosize()
        p = path.to_string()
        if len(p) == 1: #closing one of the base dirs
            self.__hide_row_with_path_up_to(p, 1)
            return
        self.__hide_row_with_path_up_to(p, len(p))

    def __hide_row_with_path_up_to(self, pathStr, up_to):
        to_remove = []
        for row in self.expanded_rows:
            if row[:up_to] == pathStr:
                # print("Removing ", row)
                to_remove.append(row)
        # print(self.expanded_rows)
        for row in to_remove:
            self.expanded_rows.remove(row)

    def on_treeWidget_row_expanded(self, widget, tIter, path, data=None):
        pathS = path.to_string()
        for row in self.expanded_rows:
            if row == pathS: #don't add already existing
                return
        self.expanded_rows.append(pathS)

    def on_treeview_buttonpress(self, widget, event, data=None):
        return self.dirty

    def on_treeview_buttonrelease(self, widget, event, data=None):
        if self.promptToSave():
            # True result indicates user selected Cancel. Stop event propagation
            return True
        else:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = widget.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                currentPath, currentCol = widget.get_cursor()
                if currentPath != path:
                    widget.set_cursor(path, col, 0)
                if event.button == 3:
                    self.__popupMenu(event)
            return False

    def on_drag_begin(self, *args):
        selection = self.treeView.get_selection()
        theModel, self.__sourceRows = selection.get_selected_rows()
        self.__sourceObjects = self.__getTreeSelection()

    def on_tree_selection_changed(self, widget, data=None):
        selectedObjects = self.__getTreeSelection()

        if len(selectedObjects) == 0:
            self.stack.set_current_page(0)
            self.set_dirty(False)
            self.cancel_record()
            self.update_actions(selectedObjects, True)
            self.selectedObject = None

        elif len(selectedObjects) == 1:
            selectedObject = selectedObjects[0]
            self.last_open = self.treeView.get_selection().get_selected_rows()[1][0].to_string()

            if isinstance(selectedObject, autokey.model.folder.Folder):
                self.stack.set_current_page(1)
                self.folderPage.load(selectedObject)
            elif isinstance(selectedObject, autokey.model.phrase.Phrase):
                self.stack.set_current_page(2)
                self.phrasePage.load(selectedObject)
            else:
                self.stack.set_current_page(3)
                self.scriptPage.load(selectedObject)

            self.set_dirty(False)
            self.cancel_record()
            self.update_actions(selectedObjects, True)
            self.selectedObject = selectedObject

        else:
            self.update_actions(selectedObjects, False)

    def on_drag_data_received(self, treeview, context, x, y, selection, info, etime):
        selection = self.treeView.get_selection()
        theModel, sourcePaths = selection.get_selected_rows()
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            targetIter = theModel.get_iter(path)
        else:
            targetIter = None

        #targetModelItem = theModel.get_value(targetIter, AkTreeModel.OBJECT_COLUMN)
        self.app.monitor.suspend()

        for path in self.__sourceRows:
            self.__removeItem(theModel, theModel[path].iter)

        newIters = []
        for item in self.__sourceObjects:
            newIter = theModel.append_item(item, targetIter)
            if isinstance(item, autokey.model.folder.Folder):
                theModel.populate_store(newIter, item)
                self.__dropRecurseUpdate(item)
            else:
                item.path = None
                item.persist()
            newIters.append(newIter)

        self.app.monitor.unsuspend()
        self.treeView.expand_to_path(theModel.get_path(newIters[-1]))
        selection.unselect_all()
        for iterator in newIters:
            selection.select_iter(iterator)
        self.on_tree_selection_changed(self.treeView)
        self.app.config_altered(True)

    def __dropRecurseUpdate(self, folder):
        folder.path = None
        folder.persist()

        for subfolder in folder.folders:
            self.__dropRecurseUpdate(subfolder)

        for child in folder.items:
            child.path = None
            child.persist()

    def on_drag_drop(self, widget, drag_context, x, y, timestamp):
        drop_info = widget.get_dest_row_at_pos(x, y)
        if drop_info:
            selection = widget.get_selection()
            theModel, sourcePaths = selection.get_selected_rows()
            path, position = drop_info

            if position not in (Gtk.TreeViewDropPosition.INTO_OR_BEFORE, Gtk.TreeViewDropPosition.INTO_OR_AFTER):
                return True

            targetIter = theModel.get_iter(path)
            targetModelItem = theModel.get_value(targetIter, AkTreeModel.OBJECT_COLUMN)

            if isinstance(targetModelItem, autokey.model.folder.Folder):
                # prevent dropping a folder onto itself
                return path in self.__sourceRows
            elif targetModelItem is None:
                # Target is top level
                for item in self.__sourceObjects:
                    if not isinstance(item, autokey.model.folder.Folder):
                        # drop not permitted for top level because not folder
                        return True

                # prevent dropping a folder onto itself
                return path in self.__sourceRows

        else:
            # target is top level with no drop info
            for item in self.__sourceObjects:
                if not isinstance(item, autokey.model.folder.Folder):
                    # drop not permitted for no drop info because not folder
                    return True

            # drop permitted for no drop info which is a folder
            return False

        # drop not permitted
        return True

    def __initTreeWidget(self):
        self.treeView.set_model(AkTreeModel(self.app.configManager.folders))
        self.treeView.set_headers_visible(True)
        self.treeView.set_reorderable(False)
        self.treeView.set_rubber_banding(True)
        self.treeView.set_search_column(1)
        self.treeView.set_enable_search(True)
        targets = []
        self.treeView.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, targets, Gdk.DragAction.DEFAULT|Gdk.DragAction.MOVE)
        self.treeView.enable_model_drag_dest(targets, Gdk.DragAction.DEFAULT)
        self.treeView.drag_source_add_text_targets()
        self.treeView.drag_dest_add_text_targets()
        self.treeView.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        # Treeview columns
        column1 = Gtk.TreeViewColumn(_("Name"))
        iconRenderer = Gtk.CellRendererPixbuf()
        textRenderer = Gtk.CellRendererText()
        column1.pack_start(iconRenderer, False)
        column1.pack_end(textRenderer, True)
        column1.add_attribute(iconRenderer, "icon-name", 0)
        column1.add_attribute(textRenderer, "text", 1)
        column1.set_expand(True)
        column1.set_min_width(150)
        column1.set_sort_column_id(1)
        self.treeView.append_column(column1)

        column2 = Gtk.TreeViewColumn(_("Abbr."))
        textRenderer = Gtk.CellRendererText()
        textRenderer.set_property("editable", False)
        column2.pack_start(textRenderer, True)
        column2.add_attribute(textRenderer, "text", 2)
        column2.set_expand(False)
        column2.set_min_width(50)
        self.treeView.append_column(column2)

        column3 = Gtk.TreeViewColumn(_("Hotkey"))
        textRenderer = Gtk.CellRendererText()
        textRenderer.set_property("editable", False)
        column3.pack_start(textRenderer, True)
        column3.add_attribute(textRenderer, "text", 3)
        column3.set_expand(False)
        column3.set_min_width(100)
        self.treeView.append_column(column3)

        path = Gtk.TreePath()
        for row in self.expanded_rows:
            p = path.new_from_string(row)
            if not p is None:
                self.treeView.expand_to_path(p)

    def __popupMenu(self, event):
        menu = self.uiManager.get_widget("/Context")
        menu.popup(None, None, None, None, event.button, event.time)

    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)

    def __getTreeSelection(self):
        selection = self.treeView.get_selection()
        if selection is None: return []

        model, items = selection.get_selected_rows()
        ret = []

        if items:
            for item in items:
                value = model.get_value(model[item].iter, AkTreeModel.OBJECT_COLUMN)
                if value.parent not in ret: # Filter out any child objects that belong to a parent already in the list
                    ret.append(value)

        return ret

    def __initStack(self):
        self.blankPage = BlankPage(self)
        self.folderPage = FolderPage(self)
        self.phrasePage = PhrasePage(self)
        self.scriptPage = ScriptPage(self)
        self.stack.append_page(self.blankPage.ui, None)
        self.stack.append_page(self.folderPage.ui, None)
        self.stack.append_page(self.phrasePage.ui, None)
        self.stack.append_page(self.scriptPage.ui, None)

    def promptToSave(self):
        selectedObject = self.__getTreeSelection()
        current = self.__getCurrentPage()

        result = False

        if self.dirty:
            if cm.ConfigManager.SETTINGS[cm_constants.PROMPT_TO_SAVE]:
                dlg = Gtk.MessageDialog(
                    self.ui, Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO,
                    _("There are unsaved changes. Would you like to save them?")
                )
                dlg.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
                response = dlg.run()

                if response == Gtk.ResponseType.YES:
                    self.on_save(None)

                elif response == Gtk.ResponseType.CANCEL:
                    result = True

                dlg.destroy()
            else:
                result = self.on_save(None)

        return result

    def __getCurrentPage(self):
        #selectedObject = self.__getTreeSelection()

        if isinstance(self.selectedObject, autokey.model.folder.Folder):
            return self.folderPage
        elif isinstance(self.selectedObject, autokey.model.phrase.Phrase):
            return self.phrasePage
        elif isinstance(self.selectedObject, autokey.model.script.Script):
            return self.scriptPage
        else:
            return None


class AkTreeModel(Gtk.TreeStore):

    OBJECT_COLUMN = 4

    def __init__(self, folders):
        Gtk.TreeStore.__init__(self, str, str, str, str, object)

        for folder in folders:
            iterator = self.append(None, folder.get_tuple())
            self.populate_store(iterator, folder)

        self.folders = folders
        self.set_sort_func(1, self.compare)
        self.set_sort_column_id(1, Gtk.SortType.ASCENDING)

    def populate_store(self, parent, parentFolder):
        for folder in parentFolder.folders:
            iterator = self.append(parent, folder.get_tuple())
            self.populate_store(iterator, folder)

        for item in parentFolder.items:
            self.append(parent, item.get_tuple())

    def append_item(self, item, parentIter):
        if parentIter is None:
            self.folders.append(item)
            item.parent = None
            return self.append(None, item.get_tuple())
        else:
            parentFolder = self.get_value(parentIter, self.OBJECT_COLUMN)
            if isinstance(item, autokey.model.folder.Folder):
                parentFolder.add_folder(item)
            else:
                parentFolder.add_item(item)

            return self.append(parentIter, item.get_tuple())

    def remove_item(self, iterator):
        item = self.get_value(iterator, self.OBJECT_COLUMN)
        item.remove_data()
        if item.parent is None:
            self.folders.remove(item)
        else:
            if isinstance(item, autokey.model.folder.Folder):
                item.parent.remove_folder(item)
            else:
                item.parent.remove_item(item)

        self.remove(iterator)

    def update_item(self, targetIter, items):
        for item in items:
            itemTuple = item.get_tuple()
            updateList = []
            for n in range(len(itemTuple)):
                updateList.append(n)
                updateList.append(itemTuple[n])
            self.set(targetIter, *updateList)

    def compare(self, theModel, iter1, iter2, data=None):
        item1 = theModel.get_value(iter1, AkTreeModel.OBJECT_COLUMN)
        item2 = theModel.get_value(iter2, AkTreeModel.OBJECT_COLUMN)

        if isinstance(item1, autokey.model.folder.Folder) and (isinstance(item2, autokey.model.phrase.Phrase) or isinstance(item2,
                                                                                                                            autokey.model.script.Script)):
            return -1
        elif isinstance(item2, autokey.model.folder.Folder) and (isinstance(item1, autokey.model.phrase.Phrase) or isinstance(item1,
                                                                                                                              autokey.model.script.Script)):
            return 1
        else:
            # return cmp(str(item1), str(item2))
            a, b = str(item1), str(item2)
            return (a > b) - (a < b)
