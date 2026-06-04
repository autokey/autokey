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

"""
This module creates and loads the pre-defined scripts and phrases users find after the first application start.
Script content is stored as Python files inside the predefined_user_scripts directory.
This eases maintenance of predefined user scripts, because those are not stored inside string variables any more.
"""

from typing import NamedTuple, List, Optional
import pathlib

from autokey.model.folder import Folder
from autokey.model.script import Script
from autokey.model.phrase import Phrase
from autokey.model.triggermode import TriggerMode

logger = __import__("autokey.logger").logger.get_logger(__name__)
# A Hotkey is defined by a list of modifier keys and a printable key.
HotkeyData = NamedTuple("HotkeyData", [("modifiers", List[str]), ("key", str)])
# ItemData holds everything needed to define a standalone Script or Phrase. For Scripts, content contains the file name
# pointing to the actual data (without the .pyi extension).
ItemData = NamedTuple(
    "ItemData", [
        ("name", str),
        ("hotkey", Optional[HotkeyData]),
        ("abbreviations", List[str]),
        ("trigger_modes", Optional[List[TriggerMode]]),
        ("window_filter", Optional[str]),
        ("show_in_tray_menu", bool),
        ("content", str)]
)

adress_phrases_data = [
    ItemData(
        name="Home Address",
        hotkey=None,
        abbreviations=["adr"],
        trigger_modes=[TriggerMode.ABBREVIATION],
        window_filter=None,
        show_in_tray_menu=False,
        content="22 Avenue Street\nBrisbane\nQLD\n4000")
]

my_phrases_data = [
    ItemData(
        name="First phrase",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=".* - gedit",
        show_in_tray_menu=False,
        content="Test phrase number one!"),
    ItemData(
        name="Second phrase",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=False,
        content="Test phrase number two!"),
    ItemData(
        name="Third phrase",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=False,
        content="Test phrase number three!")

]

sample_scripts_data = [
    ItemData(
        name="Insert Date",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=False,
        content="insert_date"),
    ItemData(
        name="List Menu",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=False,
        content="list_menu"),
    ItemData(
        name="Selection Test",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=False,
        content="selection_test"),
    ItemData(
        name="Abbreviation from selection",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=False,
        content="new_abbreviation_from_selection"),
    ItemData(
        name="Phrase from selection",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=False,
        content="create_phrase_from_selection"),        
    ItemData(
        name="Display window info",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=True,
        content="display_window_info"),
    ItemData(
        name="Unicode Strings In Scripts",
        hotkey=None,
        abbreviations=[],
        trigger_modes=[],
        window_filter=None,
        show_in_tray_menu=True,
        content="unicode_strings_in_scripts")
]


def _create_script(data: ItemData, parent: Folder) -> Script:
    """
    Create a script from data, reading the actual content from a python file in the predefined_user_scripts directory.
    Place the script into the parent folder.
    """
    content_path = pathlib.Path(__file__).parent / "predefined_user_scripts" / (data.content + ".pyi")

    logger.debug("Creating Script: name={}, path_to_content={}".format(data.name, content_path))

    with open(str(content_path), "r", encoding="utf-8") as source_file:
        source_code = source_file.read()
    item = Script(data.name, source_code)
    if data.hotkey:
        item.set_hotkey(*data.hotkey)
    for abbreviation in data.abbreviations:
        item.add_abbreviation(abbreviation)
    item.set_modes(data.trigger_modes)
    if data.window_filter:
        item.set_window_titles(data.window_filter)
    item.show_in_tray_menu = data.show_in_tray_menu
    parent.add_item(item)
    item.persist()
    return item


def _create_phrase(data: ItemData, parent: Folder) -> Phrase:
    """Create a Phrase from data. Place it into the parent folder."""
    logger.debug("Creating Phrase: name={}".format(data.name))
    item = Phrase(data.name, data.content)
    if data.hotkey:
        item.set_hotkey(*data.hotkey)
    for abbreviation in data.abbreviations:
        item.add_abbreviation(abbreviation)
    item.set_modes(data.trigger_modes)
    if data.window_filter:
        item.set_window_titles(data.window_filter)
    item.show_in_tray_menu = data.show_in_tray_menu
    parent.add_item(item)
    item.persist()
    return item


def _create_folder(name: str, parent: Folder=None) -> Folder:
    """Creates a folder with the given name. If parent is given, create it inside parent."""
    logger.debug("About to create folder '{}'".format(name))
    folder = Folder(name)
    if parent is not None:
        parent.add_folder(folder)
    return folder


def _create_addresses_folder(parent: Folder) -> Folder:
    """Creates the "Adresses" folder inside the "My Phrases" folder."""
    addresses = _create_folder("Addresses", parent)
    addresses.persist()
    for item_data in adress_phrases_data:
        _create_phrase(item_data, addresses)
    return addresses


def create_my_phrases_folder() -> Folder:
    """Creates the "My Phrases" folder. It will contain some simple test phrases"""
    my_phrases = _create_folder("My Phrases")
    my_phrases.set_hotkey(["<ctrl>"], "<f7>")
    my_phrases.set_modes([TriggerMode.HOTKEY])
    my_phrases.persist()
    _create_addresses_folder(my_phrases)
    for item_data in my_phrases_data:
        _create_phrase(item_data, my_phrases)
    return my_phrases


def create_sample_scripts_folder():
    """
    Creates the "Sample Scripts" folder. It contains a bunch of pre-defined example scripts.
    The exact script content is read from the predefined_user_scripts directory inside this Python package.
    """
    sample_scripts = _create_folder("Sample Scripts")
    sample_scripts.persist()
    for item_data in sample_scripts_data:
        _create_script(item_data, sample_scripts)
    return sample_scripts
