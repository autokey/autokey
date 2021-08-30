# Copyright (C) 2021 BlueDrink9

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
from datetime import datetime

import unittest
from unittest.mock import patch
import pytest
skip = pytest.mark.skip
import hamcrest as hm

import autokey
import autokey.scripting.clipboard_tkinter as cb

logger = __import__("autokey.logger").logger.get_logger(__name__)

def get_errors_in_log(caplog):
    errors = [record for record in caplog.get_records('call') if record.levelno >= logging.ERROR]
    return errors


@skip(reason="selection clipboard not implemented")
def  test_tkinter_selection_clipboard():
    # Note: this test does not test that the *system* clipboard is actually
    # filled, it just tests that the tk object clipboard is.
    #
    # Add current time to ensure fresh test string
    now = datetime.now()
    test_string = "this is the new clipboard contents {}".format(now)
    b = cb.TkClipboard()
    b.fill_selection(test_string)
    hm.assert_that(
        b.get_selection(),
        hm.equal_to(test_string),
        "Selection clipboard is not the same as what it was filled with!"
    )

def  test_tkinter_clipboard():
    # Note: this test does not test that the *system* clipboard is actually
    # filled, it just tests that the tk object clipboard is.
    #
    # Add current time to ensure fresh test string
    now = datetime.now()
    test_string = "this is the new clipboard contents {}".format(now)
    b = cb.TkClipboard()
    b.fill_clipboard(test_string)
    hm.assert_that(
        b.get_clipboard(),
        hm.equal_to(test_string),
        "Clipboard is not the same as what it was filled with!"
    )
