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
import re
import typing

from gi.repository import Gtk, Gdk, Pango, Gio

import autokey.model.folder
import autokey.model.helpers
import autokey.model.triggermode
import autokey.model.constants
import autokey.model.phrase
from autokey.model.key import MAPPED_UNIVERSAL_MODIFIERS
from autokey.model.triggermode import TriggerMode
import autokey.iomediator.keygrabber
import autokey.iomediator.windowgrabber

GETTEXT_DOMAIN = 'autokey'

locale.setlocale(locale.LC_ALL, '')


__all__ = ["validate", "EMPTY_FIELD_REGEX", "AbbrSettingsDialog", "HotkeySettingsDialog", "WindowFilterSettingsDialog", "RecordDialog"]

from autokey import model
from autokey import UI_common_functions as UI_common
from autokey.model.key import Key
from .shared import get_ui

logger = __import__("autokey.logger").logger.get_logger(__name__)

WORD_CHAR_OPTIONS = {
                     "All non-word": autokey.model.constants.DEFAULT_WORDCHAR_REGEX,
                     "Space and Enter": r"[^ \n]",
                     "Tab": r"[^\t]"
                     }
WORD_CHAR_OPTIONS_ORDERED = ["All non-word", "Space and Enter", "Tab"]

EMPTY_FIELD_REGEX = re.compile(r"^ *$", re.UNICODE)


def validate(expression, message, widget, parent):
    if not expression:
        dlg = Gtk.MessageDialog(
            parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.WARNING,
            Gtk.ButtonsType.OK,
            message
        )
        dlg.run()
        dlg.destroy()
        if widget is not None:
            widget.grab_focus()
    return expression


class DialogBase:

    def __init__(self):
        self.connect("close", self.on_close)
        self.connect("delete_event", self.on_close)

    def on_close(self, widget, data=None):
        self.hide()
        return True

    def on_cancel(self, widget, data=None):
        self.load(self.targetItem)
        self.ui.response(Gtk.ResponseType.CANCEL)
        self.hide()

    def on_ok(self, widget, data=None):
        if self.valid():
            self.response(Gtk.ResponseType.OK)
            self.hide()

    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)

    def on_response(self, widget, responseId):
        self.closure(responseId)
        if responseId < 0:
            self.hide()
            self.emit_stop_by_name('response')


class ShowScriptErrorsDialog(DialogBase):

    def __init__(self, app):
        builder = get_ui("show_script_errors_dialog.xml")

        self.ui = builder.get_object("show_script_errors_dialog")
        self.show_first_error_button = builder.get_object("first_error_button")
        self.show_previous_error_button = builder.get_object("previous_error_button")
        self.show_next_error_button = builder.get_object("next_error_button")
        self.show_last_error_button = builder.get_object("last_error_button")
        self.current_error_label = builder.get_object("current_error_label")
        self.total_error_count_label = builder.get_object("total_error_count_label")
        self.script_name_field = builder.get_object("script_name_field")
        self.script_start_time_field = builder.get_object("script_start_time_field")
        self.script_crash_time_field = builder.get_object("script_crash_time_field")
        self.script_triggered_by_field = builder.get_object("script_triggered_by_field")
        self.crash_stack_trace_field = builder.get_object("crash_stack_trace_field")
        # TODO: When setting the compatibility to GTK >= 3.16, remove the next three code lines and replace them with:
        # self.crash_stack_trace_field.set_monospace(True)
        settings = Gio.Settings.new("org.gnome.desktop.interface")
        monospace_font_description = Pango.font_description_from_string(settings.get_string("monospace-font-name"))
        self.crash_stack_trace_field.modify_font(monospace_font_description)

        builder.connect_signals(self)

        self.set_default_size(800, 600)
        self.script_runner = app.service.scriptRunner
        self.error_list = self.script_runner.error_records  # type: typing.List[model.ScriptErrorRecord]
        self.currently_shown_error_index = 0
        self.parent = app.configWindow
        if self.parent is not None:
            self.ui.set_transient_for(self.parent.ui)
        self.show_error_at_current_index()
        super(ShowScriptErrorsDialog, self).__init__()

    def show_first_error(self, button):
        self.currently_shown_error_index = 0
        self.show_error_at_current_index()

    def show_previous_error(self, button):
        self.currently_shown_error_index -= 1
        self.show_error_at_current_index()

    def show_next_error(self, button):
        self.currently_shown_error_index += 1
        self.show_error_at_current_index()

    def show_last_error(self, button):
        self.currently_shown_error_index = self.get_error_count() - 1
        self.show_error_at_current_index()

    def clear_all_errors(self, button):
        self.error_list.clear()
        self.parent.set_has_errors(False)
        self.on_close(button)

    def delete_currently_shown_error(self, button):
        if self.get_error_count() == 1:
            self.clear_all_errors(button)
        else:
            del self.error_list[self.currently_shown_error_index]
            if self.currently_shown_error_index == self.get_error_count():
                # Go to previous error if at the end of the error list. Else shows the next error in the list.
                self.currently_shown_error_index -= 1
            self.show_error_at_current_index()

    def get_error_count(self) -> int:
        return len(self.error_list)

    def _update_navigation_gui_states(self):
        self._update_total_error_count()
        self._update_navigation_button_states()

    def _update_total_error_count(self):
        current_error_str = str(self.currently_shown_error_index + 1)
        error_count_str = str(self.get_error_count())
        self.current_error_label.set_text(current_error_str)
        self.total_error_count_label.set_text(error_count_str)

    def _update_navigation_button_states(self):
        self.show_first_error_button.set_sensitive(True)
        self.show_previous_error_button.set_sensitive(True)
        self.show_next_error_button.set_sensitive(True)
        self.show_last_error_button.set_sensitive(True)
        if self.currently_shown_error_index == 0:
            self.show_first_error_button.set_sensitive(False)
            self.show_previous_error_button.set_sensitive(False)
        if self.currently_shown_error_index == self.get_error_count() - 1:
            self.show_next_error_button.set_sensitive(False)
            self.show_last_error_button.set_sensitive(False)

    def show_error_at_current_index(self):
        self._update_navigation_gui_states()
        print(f"About to show error at index {self.currently_shown_error_index}")
        error = self.error_list[self.currently_shown_error_index]
        self.script_name_field.get_buffer().set_text(error.script_name)
        self.script_start_time_field.get_buffer().set_text(str(error.start_time))
        self.script_crash_time_field.get_buffer().set_text(str(error.error_time))
        self.crash_stack_trace_field.get_buffer().set_text(error.error_traceback)


class AbbrSettingsDialog(DialogBase):

    def __init__(self, parent, configManager, closure):
        builder = get_ui("abbrsettings.xml")
        self.ui = builder.get_object("abbrsettings")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        self.configManager = configManager
        self.closure = closure

        self.abbrList = builder.get_object("abbrList")
        self.addButton = builder.get_object("addButton")
        self.removeButton = builder.get_object("removeButton")

        self.wordCharCombo = builder.get_object("wordCharCombo")
        self.removeTypedCheckbox = builder.get_object("removeTypedCheckbox")
        self.omitTriggerCheckbox = builder.get_object("omitTriggerCheckbox")
        self.matchCaseCheckbox = builder.get_object("matchCaseCheckbox")
        self.ignoreCaseCheckbox = builder.get_object("ignoreCaseCheckbox")
        self.triggerInsideCheckbox = builder.get_object("triggerInsideCheckbox")
        self.immediateCheckbox = builder.get_object("immediateCheckbox")

        DialogBase.__init__(self)

        # set up list view
        store = Gtk.ListStore(str)
        self.abbrList.set_model(store)

        column1 = Gtk.TreeViewColumn(_("Abbreviations"))
        textRenderer = Gtk.CellRendererText()
        textRenderer.set_property("editable", True)
        textRenderer.connect("edited", self.on_cell_modified)
        textRenderer.connect("editing-canceled", self.on_cell_editing_cancelled)
        column1.pack_end(textRenderer, True)
        column1.add_attribute(textRenderer, "text", 0)
        column1.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.abbrList.append_column(column1)

        for item in WORD_CHAR_OPTIONS_ORDERED:
            self.wordCharCombo.append_text(item)

    def load(self, item):
        self.targetItem = item
        self.abbrList.get_model().clear()

        if TriggerMode.ABBREVIATION in item.modes:
            for abbr in item.abbreviations:
                self.abbrList.get_model().append((abbr,))
            self.removeButton.set_sensitive(True)
            firstIter = self.abbrList.get_model().get_iter_first()
            self.abbrList.get_selection().select_iter(firstIter)
        else:
            self.removeButton.set_sensitive(False)

        self.removeTypedCheckbox.set_active(item.backspace)

        self.__resetWordCharCombo()

        wordCharRegex = item.get_word_chars()
        if wordCharRegex in list(WORD_CHAR_OPTIONS.values()):
            # Default wordchar regex used
            for desc, regex in WORD_CHAR_OPTIONS.items():
                if item.get_word_chars() == regex:
                    self.wordCharCombo.set_active(WORD_CHAR_OPTIONS_ORDERED.index(desc))
                    break
        else:
            # Custom wordchar regex used
            self.wordCharCombo.append_text(autokey.model.helpers.extract_wordchars(wordCharRegex))
            self.wordCharCombo.set_active(len(WORD_CHAR_OPTIONS))

        if isinstance(item, autokey.model.folder.Folder):
            self.omitTriggerCheckbox.hide()
        else:
            self.omitTriggerCheckbox.show()
            self.omitTriggerCheckbox.set_active(item.omitTrigger)

        if isinstance(item, autokey.model.phrase.Phrase):
            self.matchCaseCheckbox.show()
            self.matchCaseCheckbox.set_active(item.matchCase)
        else:
            self.matchCaseCheckbox.hide()

        self.ignoreCaseCheckbox.set_active(item.ignoreCase)
        self.triggerInsideCheckbox.set_active(item.triggerInside)
        self.immediateCheckbox.set_active(item.immediate)

    def save(self, item):
        item.modes.append(TriggerMode.ABBREVIATION)
        item.clear_abbreviations()
        item.abbreviations = self.get_abbrs()

        item.backspace = self.removeTypedCheckbox.get_active()

        option = self.wordCharCombo.get_active_text()
        if option in WORD_CHAR_OPTIONS:
            item.set_word_chars(WORD_CHAR_OPTIONS[option])
        else:
            item.set_word_chars(autokey.model.helpers.make_wordchar_re(option))

        if not isinstance(item, autokey.model.folder.Folder):
            item.omitTrigger = self.omitTriggerCheckbox.get_active()

        if isinstance(item, autokey.model.phrase.Phrase):
            item.matchCase = self.matchCaseCheckbox.get_active()

        item.ignoreCase = self.ignoreCaseCheckbox.get_active()
        item.triggerInside = self.triggerInsideCheckbox.get_active()
        item.immediate = self.immediateCheckbox.get_active()

    def reset(self):
        self.abbrList.get_model().clear()
        self.__resetWordCharCombo()
        self.removeButton.set_sensitive(False)
        self.wordCharCombo.set_active(0)
        self.omitTriggerCheckbox.set_active(False)
        self.removeTypedCheckbox.set_active(True)
        self.matchCaseCheckbox.set_active(False)
        self.ignoreCaseCheckbox.set_active(False)
        self.triggerInsideCheckbox.set_active(False)
        self.immediateCheckbox.set_active(False)

    def __resetWordCharCombo(self):
        self.wordCharCombo.remove_all()
        for item in WORD_CHAR_OPTIONS_ORDERED:
            self.wordCharCombo.append_text(item)
        self.wordCharCombo.set_active(0)

    def get_abbrs(self):
        ret = []
        model = self.abbrList.get_model()
        i = iter(model)
        # TODO: list comprehension or for loop, instead of manual loop
        try:
            while True:
                # Fix issue 646
                #text = model.get_value(i.next().iter, 0)
                text = model.get_value(next(i).iter, 0)
                ret.append(text)
                # ret.append(text.decode("utf-8"))
        except StopIteration:
            pass

        return list(set(ret))

    def get_abbrs_readable(self):
        abbrs = self.get_abbrs()
        if len(abbrs) == 1:
            return abbrs[0]
        else:
            return "[" + ",".join(abbrs) + "]"

    def valid(self):
        if not validate(
                len(self.get_abbrs()) > 0,
                _("You must specify at least one abbreviation"),
                self.addButton,
                self.ui):
            return False

        return True

    def reset_focus(self):
        self.addButton.grab_focus()

    # Signal handlers

    def on_cell_editing_cancelled(self, renderer, data=None):
        model, curIter = self.abbrList.get_selection().get_selected()
        oldText = model.get_value(curIter, 0) or ""
        self.on_cell_modified(renderer, None, oldText)

    def on_cell_modified(self, renderer, path, newText, data=None):
        model, curIter = self.abbrList.get_selection().get_selected()
        oldText = model.get_value(curIter, 0) or ""
        if EMPTY_FIELD_REGEX.match(newText) and EMPTY_FIELD_REGEX.match(oldText):
            self.on_removeButton_clicked(renderer)
        else:
            model.set(curIter, 0, newText)

    def on_addButton_clicked(self, widget, data=None):
        model = self.abbrList.get_model()
        newIter = model.append()
        self.abbrList.set_cursor(model.get_path(newIter), self.abbrList.get_column(0), True)
        self.removeButton.set_sensitive(True)

    def on_removeButton_clicked(self, widget, data=None):
        model, curIter = self.abbrList.get_selection().get_selected()
        model.remove(curIter)
        if model.get_iter_first() is None:
            self.removeButton.set_sensitive(False)
        else:
            self.abbrList.get_selection().select_iter(model.get_iter_first())

    def on_abbrList_cursorchanged(self, widget, data=None):
        pass

    def on_immediateCheckbox_stateChanged(self, widget, data=None):
        if self.immediateCheckbox.get_active():
            self.omitTriggerCheckbox.set_active(False)
            self.omitTriggerCheckbox.set_sensitive(False)
            self.wordCharCombo.set_sensitive(False)
        else:
            self.omitTriggerCheckbox.set_sensitive(True)
            self.wordCharCombo.set_sensitive(True)


class HotkeySettingsDialog(DialogBase):

    KEY_MAP = {
               ' ': "<space>",
               }

    REVERSE_KEY_MAP = {}
    for key, value in KEY_MAP.items():
        REVERSE_KEY_MAP[value] = key

    def __init__(self, parent, configManager, closure):
        builder = get_ui("hotkeysettings.xml")
        self.ui = builder.get_object("hotkeysettings")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        self.configManager = configManager
        self.closure = closure
        self.key = None

        self.universalControl = builder.get_object("universalControl")
        self.universalAlt = builder.get_object("universalAlt")
        self.universalShift = builder.get_object("universalShift")
        self.universalSuper = builder.get_object("universalSuper")
        self.universalHyper = builder.get_object("universalHyper")
        self.universalMeta = builder.get_object("universalMeta")

        self.rcontrolButton = builder.get_object("rcontrolButton")
        self.raltButton = builder.get_object("raltButton")
        self.rshiftButton = builder.get_object("rshiftButton")
        self.rsuperButton = builder.get_object("rsuperButton")
        self.rhyperButton = builder.get_object("rhyperButton")
        self.rmetaButton = builder.get_object("rmetaButton")

        self.lcontrolButton = builder.get_object("lcontrolButton")
        self.laltButton = builder.get_object("laltButton")
        self.lshiftButton = builder.get_object("lshiftButton")
        self.lsuperButton = builder.get_object("lsuperButton")
        self.lhyperButton = builder.get_object("lhyperButton")
        self.lmetaButton = builder.get_object("lmetaButton")

        self.altgrButton = builder.get_object("altgrButton")
        self.setButton = builder.get_object("setButton")
        self.keyLabel = builder.get_object("keyLabel")
        self.MODIFIER_BUTTONS = {
            self.lcontrolButton: Key.LEFTCONTROL,
            self.rcontrolButton: Key.RIGHTCONTROL,

            self.laltButton: Key.LEFTALT,
            self.raltButton: Key.RIGHTALT,

            self.altgrButton: Key.ALT_GR,

            self.lshiftButton: Key.LEFTSHIFT,
            self.rshiftButton: Key.RIGHTSHIFT,

            self.lsuperButton: Key.LEFTSUPER,
            self.rsuperButton: Key.RIGHTSUPER,

            self.lhyperButton: Key.LEFTHYPER,
            self.rhyperButton: Key.RIGHTHYPER,

            self.lmetaButton: Key.LEFTMETA,
            self.rmetaButton: Key.RIGHTMETA,

        }

        self.MODIFIER_SWITCHES ={
            self.universalControl: Key.CONTROL,
            self.universalAlt: Key.ALT,
            self.universalShift: Key.SHIFT,
            self.universalSuper: Key.SUPER,
            self.universalHyper: Key.HYPER,
            self.universalMeta: Key.META,
        }

        DialogBase.__init__(self)

    def load(self, item):
        self.setButton.set_sensitive(True)
        self.targetItem = item
        UI_common.load_hotkey_settings_dialog(self, item)

    def populate_hotkey_details(self, item):
        self.activate_modifier_buttons(item.modifiers)
        key = item.hotKey
        keyText = UI_common.get_hotkey_text(self, key)
        self._setKeyLabel(keyText)
        self.key = keyText
        logger.debug("Loaded item {}, key: {}, modifiers: {}".format(item, keyText, item.modifiers))

    def activate_modifier_buttons(self, modifiers):
        for button, key in self.MODIFIER_BUTTONS.items():
            button.set_active(key in modifiers)

        for button, key in self.MODIFIER_SWITCHES.items():
            button.set_active(key in modifiers)

    def save(self, item):
        UI_common.save_hotkey_settings_dialog(self, item)

    def reset(self):
        for button in self.MODIFIER_BUTTONS:
            button.set_active(False)

        for button in self.MODIFIER_SWITCHES:
            button.set_active(False)

        self._setKeyLabel(_("(None)"))
        self.key = None
        self.setButton.set_sensitive(True)

    def set_key(self, key, modifiers: list=None):
        if modifiers is None:
            modifiers = []
        Gdk.threads_enter()
        if key in self.KEY_MAP:
            key = self.KEY_MAP[key]
        self._setKeyLabel(key)
        self.key = key
        self.activate_modifier_buttons(modifiers)

        self.setButton.set_sensitive(True)
        Gdk.threads_leave()

    def cancel_grab(self):
        Gdk.threads_enter()
        self.setButton.set_sensitive(True)
        self._setKeyLabel(self.key)
        Gdk.threads_leave()

    def get_active_modifiers(self):
        modifiers = []
        for button, key in self.MODIFIER_BUTTONS.items():
            if button.get_active():
                modifiers.append(key)
        for button, key in self.MODIFIER_SWITCHES.items():
            if button.get_active():
                for item in MAPPED_UNIVERSAL_MODIFIERS[key]: # remove the left/right modifier versions if the switch is active
                    if item in modifiers:
                        modifiers.remove(item)
                modifiers.append(key)
        modifiers.sort()
        return modifiers

    def _setKeyLabel(self, key):
        self.keyLabel.set_text(_("Key: ") + key)

    def valid(self):
        if not self.check_nonempty_key():
            return False

        return True

    def check_nonempty_key(self):
        return validate(
            self.key is not None,
            _("You must specify a key for the hotkey."),
            None,
            self.ui)

    def on_setButton_pressed(self, widget, data=None):
        self.setButton.set_sensitive(False)
        self.keyLabel.set_text(_("Press a key..."))
        self.grabber = autokey.iomediator.keygrabber.KeyGrabber(self)
        self.grabber.start()

    def on_switch_activate(self, widget, data=None):
        # print(widget, widget.get_name())
        name = widget.get_name()
        if name == "<ctrl>":
            self.lcontrolButton.set_active(False)
            self.rcontrolButton.set_active(False)
        elif name == "<alt>":
            self.laltButton.set_active(False)
            self.raltButton.set_active(False)
        elif name == "<shift>":
            self.lshiftButton.set_active(False)
            self.rshiftButton.set_active(False)
        elif name == "<super>":
            self.lsuperButton.set_active(False)
            self.rsuperButton.set_active(False)
        elif name == "<meta>":
            self.lmetaButton.set_active(False)
            self.rmetaButton.set_active(False)
        elif name == "<hyper>":
            self.lhyperButton.set_active(False)
            self.rhyperButton.set_active(False)


class GlobalHotkeyDialog(HotkeySettingsDialog):

    def load(self, item):
        self.targetItem = item
        UI_common.load_global_hotkey_dialog(self,
                                            item)


    def save(self, item):
        UI_common.save_hotkey_settings_dialog(self, item)

    def valid(self):
        configManager = self.configManager
        modifiers = self.get_active_modifiers()
        regex = self.targetItem.get_applicable_regex()
        pattern = None
        if regex is not None:
            pattern = regex.pattern

        unique, conflicting = configManager.check_hotkey_unique(modifiers, self.key, pattern, self.targetItem)
        if not validate(unique,
                        _("The hotkey is already in use for %s.") % conflicting,
                        None,
                        self.ui):
            return False

        if not self.check_nonempty_key():
            return False

        return True


class WindowFilterSettingsDialog(DialogBase):

    def __init__(self, parent, closure):
        builder = get_ui("windowfiltersettings.xml")
        self.ui = builder.get_object("windowfiltersettings")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)
        self.closure = closure

        self.triggerRegexEntry = builder.get_object("triggerRegexEntry")
        self.recursiveButton = builder.get_object("recursiveButton")
        self.detectButton = builder.get_object("detectButton")

        DialogBase.__init__(self)

    def load(self, item):
        self.targetItem = item

        if not isinstance(item, autokey.model.folder.Folder):
            self.recursiveButton.hide()
        else:
            self.recursiveButton.show()

        if not item.has_filter():
            self.reset()
        else:
            self.triggerRegexEntry.set_text(item.get_filter_regex())
            self.recursiveButton.set_active(item.isRecursive)

    def save(self, item):
        UI_common.save_item_filter(self, item)

    def reset(self):
        self.triggerRegexEntry.set_text("")
        self.recursiveButton.set_active(False)

    def get_filter_text(self):
        return self.triggerRegexEntry.get_text()

    def get_is_recursive(self):
        return self.recursiveButton.get_active()

    def valid(self):
        return True

    def reset_focus(self):
        self.triggerRegexEntry.grab_focus()

    def on_response(self, widget, responseId):
        self.closure(responseId)

    def receive_window_info(self, info):
        Gdk.threads_enter()
        dlg = DetectDialog(self.ui)
        dlg.populate(info)
        response = dlg.run()

        if response == Gtk.ResponseType.OK:
            self.triggerRegexEntry.set_text(dlg.get_choice())

        self.detectButton.set_sensitive(True)
        Gdk.threads_leave()

    def on_detectButton_pressed(self, widget, data=None):
        #self.__dlg =
        widget.set_sensitive(False)
        self.grabber = autokey.iomediator.windowgrabber.WindowGrabber(self)
        self.grabber.start()


class DetectDialog(DialogBase):

    def __init__(self, parent):
        builder = get_ui("detectdialog.xml")
        self.ui = builder.get_object("detectdialog")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)

        self.classLabel = builder.get_object("classLabel")
        self.titleLabel = builder.get_object("titleLabel")
        self.classRadioButton = builder.get_object("classRadioButton")
        self.titleRadioButton = builder.get_object("titleRadioButton")

        DialogBase.__init__(self)

    def populate(self, windowInfo):
        self.titleLabel.set_text(_("Window title: %s") % windowInfo.wm_title)
        self.classLabel.set_text(_("Window class: %s") % windowInfo.wm_class)
        self.windowInfo = windowInfo

    def get_choice(self):
        if self.classRadioButton.get_active():
            return self.windowInfo.wm_class
        else:
            return self.windowInfo.wm_title

    def on_cancel(self, widget, data=None):
        self.ui.response(Gtk.ResponseType.CANCEL)
        self.hide()

    def on_ok(self, widget, data=None):
        self.response(Gtk.ResponseType.OK)
        self.hide()


class RecordDialog(DialogBase):

    def __init__(self, parent, closure):
        self.closure = closure
        builder = get_ui("recorddialog.xml")
        self.ui = builder.get_object("recorddialog")
        builder.connect_signals(self)
        self.ui.set_transient_for(parent)

        self.keyboardButton = builder.get_object("keyboardButton")
        self.mouseButton = builder.get_object("mouseButton")
        self.spinButton = builder.get_object("spinButton")

        DialogBase.__init__(self)

    def get_record_keyboard(self):
        return self.keyboardButton.get_active()

    def get_record_mouse(self):
        return self.mouseButton.get_active()

    def get_delay(self):
        return self.spinButton.get_value_as_int()

    def on_response(self, widget, responseId):
        self.closure(responseId, self.get_record_keyboard(), self.get_record_mouse(), self.get_delay())

    def on_cancel(self, widget, data=None):
        self.ui.response(Gtk.ResponseType.CANCEL)
        self.hide()

    def valid(self):
        return True
