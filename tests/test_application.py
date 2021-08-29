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
import os
import signal
import sys
import threading
from time import sleep
import typing

import unittest
from unittest.mock import patch
import pytest
skip = pytest.mark.skip
import hamcrest as hm

import autokey
import autokey.autokey_app as ak

def ret_arg(arg):
    return arg

def create_mock_app():
    with patch(
        'autokey.autokey_app.AutokeyApplication._AutokeyApplication__initialise'), \
            patch('sys.argv', ['autokey-headless']):
        return ak.AutokeyApplication()

def get_errors_in_log(caplog):
    errors = [record for record in caplog.get_records('call') if record.levelno >= logging.ERROR]
    return errors

@skip
@patch('sys.argv', ['autokey-app-testing'])
def test_application_runs_without_errors(caplog):
    autokey.common.USED_UI_TYPE = "headless"
    app = ak.AutokeyApplication()
    app.autokey_shutdown()
    hm.assert_that(get_errors_in_log(caplog), hm.empty())


def test_write_read_lock_file(tmpdir):
    app = create_mock_app()
    lockfile = tmpdir.join("lockfile")
    pid = str(os.getpid())
    with patch('autokey.common.LOCK_FILE', lockfile):
        ak.AutokeyApplication.create_lock_file()
        hm.assert_that(
            ak.AutokeyApplication.read_pid_from_lock_file(),
            hm.equal_to(pid),
            "PID written then read from lock file is not the same"
        )


@skip
def test_autokey_application_creates_lock():
    pass


@skip
def test_autokey_already_running():
    pass


@skip
def test_add_user_code_dir_to_path():
    app = create_mock_app()
    mock_path = 'test/dummy/path'
    with patch(app.configManager.userCodeDir, mock_path):
        app.__add_user_code_dir_to_path()
        hm.assert_that(sys.path, hm.has_item(mock_path))
