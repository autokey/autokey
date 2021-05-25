# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2019-2020 Thomas Hess <thomas.hess@udo.edu>
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

import datetime
import json
import os
import typing
from pathlib import Path

import autokey.model.common as model_common
from autokey.model.store import Store
from autokey.model.triggermode import TriggerMode
from autokey.model.abstract_abbreviation import AbstractAbbreviation
from autokey.model.abstract_window_filter import AbstractWindowFilter
from autokey.model.abstract_hotkey import AbstractHotkey

logger = __import__("autokey.logger").logger.get_logger(__name__)


class Script(AbstractAbbreviation, AbstractHotkey, AbstractWindowFilter):
    """
    Encapsulates all data and behaviour for a script.
    """

    def __init__(self, description: str, source_code: str, path=None):
        AbstractAbbreviation.__init__(self)
        AbstractHotkey.__init__(self)
        AbstractWindowFilter.__init__(self)
        self.description = description
        self.code = source_code
        self.store = Store()
        self.modes = []  # type: typing.List[TriggerMode]
        self.usageCount = 0
        self.prompt = False
        self.omitTrigger = False
        self.parent = None
        self.show_in_tray_menu = False
        self.path = path

    def build_path(self, base_name=None):
        return model_common.build_path(self, ".py", base_name)

    def get_json_path(self):
        return model_common.get_json_path(self.path)

    def persist(self):
        if self.path is None:
            self.build_path()

        self._persist_metadata()

        with open(self.path, "w") as out_file:
            out_file.write(self.code)

    def get_serializable(self):
        d = model_common.get_serializable_scriptphrase(self)
        d2 = {
            "type": "script",
            "store": self.store,
        }
        d.update(d2)
        return d

    def _persist_metadata(self):
        """
        Write all script meta-data, including the persistent script Store.
        The Store instance might contain arbitrary user data, like function objects, OpenCL contexts, or whatever other
        non-serializable objects, both as keys or values.
        Try to serialize the data, and if it fails, fall back to checking the store and removing all non-serializable
        data.
        """
        serializable_data = self.get_serializable()
        try:
            self._try_persist_metadata(serializable_data)
        except TypeError:
            # The user added non-serializable data to the store, so skip all non-serializable keys or values.
            cleaned_data = Script._remove_non_serializable_store_entries(serializable_data["store"])
            self._try_persist_metadata(cleaned_data)

    def _try_persist_metadata(self, serializable_data: dict):
        with open(self.get_json_path(), "w") as json_file:
                json.dump(serializable_data, json_file, indent=4)

    @staticmethod
    def _remove_non_serializable_store_entries(store: Store) -> dict:
        """
        Copy all serializable data into a new dict, and skip the rest.
        This makes sure to keep the items during runtime, even if the user edits and saves the script.
        """
        cleaned_store_data = {}
        for key, value in store.items():
            if Script._is_serializable(key) and Script._is_serializable(value):
                cleaned_store_data[key] = value
            else:
                logger.info("Skip non-serializable item in the local script store. Key: '{}', Value: '{}'. "
                             "This item cannot be saved and therefore will be lost when autokey quits.".format(
                                key, value
                ))
        return cleaned_store_data

    @staticmethod
    def _is_serializable(data):
        try:
            json.dumps(data)
        except (TypeError, ValueError):
            # TypeError occurs with non-serializable types (type, function, etc.)
            # ValueError occurs when circular references are found. Example: `l=[]; l.append(l)`
            return False
        else:
            return True

    def load(self, parent):
        model_common.load(self, parent)

    def load_from_serialized(self, **kwargs):
        model_common.load_from_serialized(self)

    def inject_json_data(self, data: dict):
        model_common.inject_json_data_scriptphrase(self, data)
        self.store = Store(data["store"])

    def rebuild_path(self):
        model_common.rebuild_path(self)

    def remove_data(self):
        model_common.remove_data(self)

    def copy(self, source_script):
        model_common.copy_scriptphrase(self, source_script)
        self.code = source_script.code
        self.omitTrigger = source_script.omitTrigger

    def get_tuple(self):
        return "text-x-python", self.description, self.get_abbreviations(), self.get_hotkey_string(), self

    def set_modes(self, modes: typing.List[TriggerMode]):
        self.modes = modes

    def check_input(self, buffer, window_info):
        if TriggerMode.ABBREVIATION in self.modes:
            return self._should_trigger_abbreviation(buffer) and self._should_trigger_window_title(window_info)
        else:
            return False

    def process_buffer(self, buffer):
        self.usageCount += 1
        self.parent.increment_usage_count()
        trigger_found = False
        backspaces = 0
        string = ""

        if TriggerMode.ABBREVIATION in self.modes:
            if self._should_trigger_abbreviation(buffer):
                abbr = self._get_trigger_abbreviation(buffer)
                stringBefore, typedAbbr, stringAfter = self._partition_input(buffer, abbr)
                trigger_found = True
                if self.backspace:
                    # determine how many backspaces to send
                    backspaces = len(abbr) + len(stringAfter)
                else:
                    backspaces = len(stringAfter)

                if not self.omitTrigger:
                    string += stringAfter

        if not trigger_found:
            # Phrase could have been triggered from menu - check parents for backspace count
            backspaces = self.parent.get_backspace_count(buffer)

        return backspaces, string

    def should_prompt(self, buffer):
        return self.prompt

    def get_description(self, buffer):
        return self.description

    def __str__(self):
        return "script '{}'".format(self.description)

    def __repr__(self):
        return "Script('" + self.description + "')"


class ScriptErrorRecord:
    """
    This class holds a record of an error that caused a user Script to abort and additional meta-data .
    """
    def __init__(self, script: typing.Union[Script, Path], error_traceback: str,
                 start_time: datetime.time, error_time: datetime.time):
        self.script_name = script.description if isinstance(script, Script) else str(script)
        self.error_traceback = error_traceback
        self.start_time = start_time
        self.error_time = error_time
