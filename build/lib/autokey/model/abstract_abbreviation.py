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

import re
import typing

from autokey.model.helpers import DEFAULT_WORDCHAR_REGEX, TriggerMode


class AbstractAbbreviation:
    """
    Abstract class encapsulating the common functionality of an abbreviation list
    """

    def __init__(self):
        self.abbreviations = []  # type: typing.List[str]
        self.backspace = True
        self.ignoreCase = False
        self.immediate = False
        self.triggerInside = False
        self.set_word_chars(DEFAULT_WORDCHAR_REGEX)

    def get_serializable(self):
        d = {
            "abbreviations": self.abbreviations,
            "backspace": self.backspace,
            "ignoreCase": self.ignoreCase,
            "immediate": self.immediate,
            "triggerInside": self.triggerInside,
            "wordChars": self.get_word_chars()
            }
        return d

    def load_from_serialized(self, data: dict):
        if "abbreviations" not in data: # check for pre v0.80.4
            self.abbreviations = [data["abbreviation"]]  # type: typing.List[str]
        else:
            self.abbreviations = data["abbreviations"]  # type: typing.List[str]

        self.backspace = data["backspace"]
        self.ignoreCase = data["ignoreCase"]
        self.immediate = data["immediate"]
        self.triggerInside = data["triggerInside"]
        self.set_word_chars(data["wordChars"])

    def copy_abbreviation(self, abbr):
        self.abbreviations = abbr.abbreviations
        self.backspace = abbr.backspace
        self.ignoreCase = abbr.ignoreCase
        self.immediate = abbr.immediate
        self.triggerInside = abbr.triggerInside
        self.set_word_chars(abbr.get_word_chars())

    def set_word_chars(self, regex):
        self.wordChars = re.compile(regex, re.UNICODE)

    def get_word_chars(self):
        return self.wordChars.pattern

    def add_abbreviation(self, abbr):
        if not isinstance(abbr, str):
            raise ValueError("Abbreviations must be strings. Cannot add abbreviation '{}', having type {}.".format(
                abbr, type(abbr)
            ))
        self.abbreviations.append(abbr)
        if TriggerMode.ABBREVIATION not in self.modes:
            self.modes.append(TriggerMode.ABBREVIATION)

    def add_abbreviations(self, abbreviation_list: typing.Iterable[str]):
        if not isinstance(abbreviation_list, list):
            abbreviation_list = list(abbreviation_list)
        if not all(isinstance(abbr, str) for abbr in abbreviation_list):
            raise ValueError("All added Abbreviations must be strings.")
        self.abbreviations += abbreviation_list
        if TriggerMode.ABBREVIATION not in self.modes:
            self.modes.append(TriggerMode.ABBREVIATION)

    def clear_abbreviations(self):
        self.abbreviations = []

    def get_abbreviations(self):
        if TriggerMode.ABBREVIATION not in self.modes:
            return ""
        elif len(self.abbreviations) == 1:
            return self.abbreviations[0]
        else:
            return "[" + ",".join(self.abbreviations) + "]"

    def _should_trigger_abbreviation(self, buffer):
        """
        Checks whether, based on the settings for the abbreviation and the given input,
        the abbreviation should trigger.

        @param buffer Input buffer to be checked (as string)
        """
        return any(self.__checkInput(buffer, abbr) for abbr in self.abbreviations)

    def _get_trigger_abbreviation(self, buffer):
        for abbr in self.abbreviations:
            if self.__checkInput(buffer, abbr):
                return abbr

        return None

    def __checkInput(self, buffer, abbr):
        stringBefore, typedAbbr, stringAfter = self._partition_input(buffer, abbr)
        if len(typedAbbr) > 0:
            # Check trigger character condition
            if not self.immediate:
                # If not immediate expansion, check last character
                if len(stringAfter) == 1:
                    # Have a character after abbr
                    if self.wordChars.match(stringAfter):
                        # last character(s) is a word char, can't send expansion
                        return False
                    elif len(stringAfter) > 1:
                        # Abbr not at/near end of buffer any more, can't send
                        return False
                else:
                    # Nothing after abbr yet, can't expand yet
                    return False

            else:
                # immediate option enabled, check abbr is at end of buffer
                if len(stringAfter) > 0:
                    return False

            # Check chars ahead of abbr
            # length of stringBefore should always be > 0
            if len(stringBefore) > 0 and not re.match('(^\s)', stringBefore[-1]) and not self.triggerInside:
                # check if last char before the typed abbreviation is a word char
                # if triggerInside is not set, can't trigger when inside a word
                return False

            return True

        return False

    def _partition_input(self, current_string: str, abbr: typing.Optional[str]) -> typing.Tuple[str, str, str]:
        """
        Partition the input into text before, typed abbreviation (if it exists), and text after
        """
        if abbr:
            if self.ignoreCase:
                string_before, typed_abbreviation, string_after = self._case_insensitive_rpartition(
                    current_string, abbr
                )
                abbr_start_index = len(string_before)
                abbr_end_index = abbr_start_index + len(typed_abbreviation)
                typed_abbreviation = current_string[abbr_start_index:abbr_end_index]
            else:
                string_before, typed_abbreviation, string_after = current_string.rpartition(abbr)

            return string_before, typed_abbreviation, string_after
        else:
            # abbr is None. This happens if the phrase was typed/pasted using a hotkey and is about to be un-done.
            # In this case, there is no trigger character (thus empty before and after text). The complete string
            # should be undone.
            return "", current_string, ""

    @staticmethod
    def _case_insensitive_rpartition(input_string: str, separator: str) -> typing.Tuple[str, str, str]:
        """Same as str.rpartition(), except that the partitioning is done case insensitive."""
        lowered_input_string = input_string.lower()
        lowered_separator = separator.lower()
        try:
            split_index = lowered_input_string.rindex(lowered_separator)
        except ValueError:
            # Did not find the separator in the input_string.
            # Follow https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str
            # str.rpartition documentation and return the tuple ("", "", unmodified_input) in this case
            return "", "", input_string
        else:
            split_index_2 = split_index+len(separator)
            return input_string[:split_index], input_string[split_index: split_index_2], input_string[split_index_2:]
