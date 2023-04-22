# -*- coding: utf-8 -*-

# Copyright (C) 2023 Sam Sebastian

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


from gi import require_version
import csv

require_version('Gtk', '3.0')
require_version('GtkSource', '3.0')

from gi.repository import Gtk, GtkSource, GObject

logger = __import__("autokey.logger").logger.get_logger(__name__)

class FileCompletionProvider(GObject.GObject, GtkSource.CompletionProvider):

    def __init__(self, filename, trigger="."):
        super().__init__()
        self.csv_items = []
        self.name = "GTKAutocomplete"
        self.trigger=trigger

        with open(filename, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                self.csv_items.append(row)


    def do_get_name(self):
        return self.name

    def do_match(self, context):
        return True

    def do_populate(self, context):
        proposals = []

        end_iter = context.get_iter()
        if not isinstance(end_iter, Gtk.TextIter):
            _, end_iter = context.get_iter()

        if end_iter:
            buffer = end_iter.get_buffer()
            line_number = end_iter.get_line()
            line_start = buffer.get_iter_at_line(line_number)
            line_end = line_start.copy()
            line_end.forward_to_line_end()
            full_line_text = buffer.get_text(line_start, line_end, False)
            line_text = full_line_text.strip()

            logger.debug(f"Current line: {line_number}, text: {line_text}")


            for row in self.csv_items:
                if self.trigger==".":
                    module_name = row[0].split(".")[0]
                    func_name = row[0].split(".")[1]
                    #print(module_name, func_name)

                if (self.trigger=="<" or (line_text in row[0] or module_name in line_text)) and len(line_text)>=1 and line_text[-1]==self.trigger:
                    if self.trigger=="<": module_name=""

                    completion_text = row[0][len(module_name)+1:]
                    label = " ".join([completion_text, row[1]])

                    item = GtkSource.CompletionItem(label=label, text=completion_text)
                    item.set_icon_name("gtk-jump-to")

                    
                    proposals.append({"func_name": func_name, "completion": item})

                    if self.trigger=="<":
                        self.name = "Insert Macro"
                    else:
                        self.name = row[0].split(".")[0]

        proposals.sort(key=lambda x: x["func_name"])
        sorted_proposals = [p["completion"] for p in proposals]
        context.add_proposals(self, sorted_proposals, True)
