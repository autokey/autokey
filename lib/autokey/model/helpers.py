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

import enum
import os
import re

DEFAULT_WORDCHAR_REGEX = '[\w]'
JSON_FILE_PATTERN = "{}/{}.json"
SPACES_RE = re.compile(r"^ | $")


def make_wordchar_re(word_chars: str):
    return "[^{word_chars}]".format(word_chars=word_chars)


def extract_wordchars(regex):
    return regex[2:-1]


def get_safe_path(base_path, name, ext=""):
    name = SPACES_RE.sub('_', name)
    safe_name = ''.join((char for char in name if char.isalnum() or char in "_ -."))

    if safe_name == '':
        path = base_path + '/1' + ext
        jsonPath = base_path + "/1.json"
        n = 2
    else:
        path = base_path + '/' + safe_name + ext
        jsonPath = base_path + '/' + safe_name + ".json"
        n = 1

    while os.path.exists(path) or os.path.exists(jsonPath):
        path = base_path + '/' + safe_name + str(n) + ext
        jsonPath = base_path + '/' + safe_name + str(n) + ".json"
        n += 1

    return path


@enum.unique
class TriggerMode(enum.Enum):
    """
    Enumeration class for phrase match modes.

    NONE: Don't trigger this phrase (phrase will only be shown in its folder).
    ABBREVIATION: Trigger this phrase using an abbreviation.
    PREDICTIVE: Trigger this phrase using predictive mode.
    """
    NONE = 0
    ABBREVIATION = 1
    PREDICTIVE = 2
    HOTKEY = 3
