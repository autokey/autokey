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

from gi.repository import Gtk

from autokey.configmanager import *
import configwindow


class AbbrSelectorDialog:
    
    def __init__(self, app):
        builder = configwindow.get_ui("abbrselector.xml")
        self.ui = builder.get_object("abbrselector")
        builder.connect_signals(self)
        self.entry = builder.get_object("entry")
        
        self.service = app.service
        self.app = app
        self.abbreviations = self.service.configManager.abbreviations
        
        self.completion = Gtk.EntryCompletion()
        self.entry.set_completion(self.completion)
        model = AbbreviationModel(self.abbreviations)
        self.completion.set_model(model)
        self.completion.set_text_column(0)
        
        descriptionCell = Gtk.CellRendererText()
        self.completion.pack_start(descriptionCell, True, True, 0)
        self.completion.add_attribute(descriptionCell, "text", 1)
        self.completion.set_inline_completion(True)
        self.completion.set_inline_selection(True)
        self.completion.connect("match-selected", self.on_match_selected)
        
        self.set_keep_above(True)
        
        
    def on_match_selected(self, completion, model, iter, data=None):
        theItem = model.get_value(iter, AbbreviationModel.OBJECT_COLUMN)
        self.service.item_selected(theItem)
        self.hide()
        
    def on_entry_activated(self, widget, data=None):
        entered = self.entry.get_text()
        for thePhrase in self.abbreviations:
            if theItem.abbreviation == entered:
                self.service.phrase_selected(None, theItem)
        self.hide()
    
    def on_close(self, widget, data=None):
        self.destroy()
        self.app.abbrPopup = None

    def __getattr__(self, attr):
        # Magic fudge to allow us to pretend to be the ui class we encapsulate
        return getattr(self.ui, attr)
    
    
class AbbreviationModel(Gtk.ListStore):
    
    OBJECT_COLUMN = 2
        
    def __init__(self, abbreviations):
        GObject.GObject.__init__(self, str, str, object)
        
        for item in abbreviations:
            self.append((item.abbreviation, item.description, item))
            
    def match(self, completion, keyString, iter, data=None):
        abbreviation = self.get_value(iter, 0)
        description = self.get_value(iter, 1)
        if abbreviation.startswith(keyString):
            return True
        elif len(keyString) > 1:
            if keyString in description:
                return True

        return False
