"""


"""

import re
from gi import require_version

require_version('Gtk', '3.0')
require_version('GtkSource', '3.0')

from gi.repository import Gtk, GtkSource, GObject

class CompletionProvider(GObject.GObject, GtkSource.CompletionProvider):

    def do_get_name(self):
        return self.name

    def do_match(self, context):
        return True

    def do_populate(self, context):
        proposals = []
        keywords = ["keyboard", "clipboard", "engine", "dialog", "mouse", "system", "window", "store"]

        end_iter = context.get_iter()
        if not isinstance(end_iter, Gtk.TextIter):
            _, end_iter = context.get_iter()

        if end_iter:
            for i in keywords:
                buffer = end_iter.get_buffer()
                mov_iter = end_iter.copy()
                keyword = i
                if mov_iter.backward_search(keyword, Gtk.TextSearchFlags.VISIBLE_ONLY):
                    mov_iter, _ = mov_iter.backward_search(keyword, Gtk.TextSearchFlags.VISIBLE_ONLY)
                    left_text = buffer.get_text(mov_iter,end_iter,True)
                else:
                    left_text = ''
                if re.match(r'keyboard\.$', left_text):
                    self.name = "Keyboard"
                    proposals.append(GtkSource.CompletionItem(label="Fake Keypress", text="fake_keypress("))
                    proposals.append(GtkSource.CompletionItem(label="Press Key", text="press_key("))
                    proposals.append(GtkSource.CompletionItem(label="Release Key", text="release_key("))
                    proposals.append(GtkSource.CompletionItem(label="Send Key", text="send_key("))
                    proposals.append(GtkSource.CompletionItem(label="Send Keys", text="send_keys("))
                    proposals.append(GtkSource.CompletionItem(label="Wait for Keypress", text="wait_for_keypress("))
                elif re.match(r'clipboard\.$', left_text):
                    self.name = "Clipboard"
                    proposals.append(GtkSource.CompletionItem(label="Fill Clipboard", text="fill_clipboard("))
                    proposals.append(GtkSource.CompletionItem(label="Fill Selection", text="fill_selection("))
                    proposals.append(GtkSource.CompletionItem(label="Get Clipboard", text="get_clipboard("))
                    proposals.append(GtkSource.CompletionItem(label="Get Selection", text="get_selection("))
                elif re.match(r'engine\.$', left_text):
                    self.name = "Engine"
                    proposals.append(GtkSource.CompletionItem(label="Create Abbreviation", text="create_abbreviation("))
                    proposals.append(GtkSource.CompletionItem(label="Create Folder", text="create_folder("))
                    proposals.append(GtkSource.CompletionItem(label="Create Hotkey", text="create_hotkey("))
                    proposals.append(GtkSource.CompletionItem(label="Get Folder", text="get_folder("))
                elif re.match(r'dialog\.$', left_text):
                    self.name = "Dialog"
                    proposals.append(GtkSource.CompletionItem(label="Calendar Dialog", text="calendar_dialog("))
                    proposals.append(GtkSource.CompletionItem(label="Choose Colour", text="choose_colour("))
                    proposals.append(GtkSource.CompletionItem(label="Choose Directory", text="choose_directory("))
                    proposals.append(GtkSource.CompletionItem(label="Info Dialog", text="info_dialog("))
                    proposals.append(GtkSource.CompletionItem(label="Input Dialog", text="input_dialog("))
                    proposals.append(GtkSource.CompletionItem(label="List Menu", text="list_menu("))
                elif re.match(r'system\.$', left_text):
                    self.name = "System"
                    proposals.append(GtkSource.CompletionItem(label="Create File", text="create_file("))
                    proposals.append(GtkSource.CompletionItem(label="Exec Command", text="exec_command("))
                elif re.match(r'window\.$', left_text):
                    self.name = "Window"
                    proposals.append(GtkSource.CompletionItem(label="Activate", text="activate("))
                    proposals.append(GtkSource.CompletionItem(label="Close", text="close("))
                    proposals.append(GtkSource.CompletionItem(label="Get Active Class", text="get_active_class("))
                    proposals.append(GtkSource.CompletionItem(label="Get Active Geometry", text="get_active_geometry("))
                    proposals.append(GtkSource.CompletionItem(label="Get Active Title", text="get_active_title("))
                    proposals.append(GtkSource.CompletionItem(label="Move To Desktop", text="move_to_desktop("))
                    proposals.append(GtkSource.CompletionItem(label="Close", text="close("))
                    proposals.append(GtkSource.CompletionItem(label="Set Property", text="set_property("))
                    proposals.append(GtkSource.CompletionItem(label="Switch Desktop", text="switch_desktop("))
                    proposals.append(GtkSource.CompletionItem(label="Wait For Exist", text="wait_for_exist("))
                    proposals.append(GtkSource.CompletionItem(label="Wait For Focus", text="wait_for_focus("))
                elif re.match(r'mouse\.$', left_text):
                    self.name = "Mouse"
                    proposals.append(GtkSource.CompletionItem(label="Click Absolute", text="click_absolute("))
                    proposals.append(GtkSource.CompletionItem(label="Click Relative", text="click_relative("))
                    proposals.append(GtkSource.CompletionItem(label="Click Relative Self", text="click_relative_self("))
                    proposals.append(GtkSource.CompletionItem(label="Drag And Select", text="drag_and_select("))
                    proposals.append(GtkSource.CompletionItem(label="Mouse Button Down", text="mouse_button_down("))
                    proposals.append(GtkSource.CompletionItem(label="Mouse Button Down", text="mouse_button_down("))
                    proposals.append(GtkSource.CompletionItem(label="Move Cursor", text="move_cursor("))
                    proposals.append(GtkSource.CompletionItem(label="Wait For Click", text="wait_for_click("))
                elif re.match(r'store\.$', left_text):
                    self.name = "Store"
                    proposals.append(GtkSource.CompletionItem(label="Set Value", text="set_value("))
                    proposals.append(GtkSource.CompletionItem(label="Get Value", text="get_value("))
                    proposals.append(GtkSource.CompletionItem(label="Remove Value", text="remove_value("))
                    proposals.append(GtkSource.CompletionItem(label="Set Global Value", text="set_global_value("))
                    proposals.append(GtkSource.CompletionItem(label="Get Global Value", text="get_global_value("))
                    proposals.append(GtkSource.CompletionItem(label="Remove Global Value", text="remove_global_value("))
                    proposals.append(GtkSource.CompletionItem(label="Has Key", text="has_key("))



        context.add_proposals(self, proposals, True)
        return
