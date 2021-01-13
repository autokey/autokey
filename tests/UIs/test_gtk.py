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

import unittest
from unittest.mock import patch
import pytest
skip = pytest.mark.skip
import hamcrest as hm

import autokey.gtkapp as gtkui

def ret_arg(arg):
    return arg

# def create_mock_app():
#     with patch(
#         'autokey.autokey_app.AutokeyApplication._AutokeyApplication__initialise'), \
#             patch('sys.argv', ['autokey-headless']):
#         return ak.AutokeyApplication()

def get_errors_in_log(caplog):
    errors = [record for record in caplog.get_records('call') if record.levelno >= logging.ERROR]
    return errors


@patch('sys.argv', ['autokey-app-testing'])
def test_application_runs_without_errors(caplog):
    app = gtkui.Application()
    app.show_configure()
    app._Application__completeShutdown()
    hm.assert_that(get_errors_in_log(caplog), hm.empty())
