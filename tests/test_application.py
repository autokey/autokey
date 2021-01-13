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
from hamcrest import *

import autokey.autokey_app as ak
import autokey.headless_app as app

def ret_arg(arg):
    return arg

def create_mock_app():
    with patch(
        'autokey.autokey_app.AutokeyApplication._AutokeyApplication__initialise'), \
            patch('sys.argv', ['autokey-headless']):
        return ak.AutokeyApplication()

def test_application_runs():
    with patch('sys.argv', ['autokey-app-testing']):
        app = ak.AutokeyApplication()
        app.autokey_shutdown()

@skip
@patch('sys.argv', ['autokey-headless'])
def test_headless_runs():
    x = threading.Thread(target=app.main())
    x.daemon = True
    x.start()
    x.join()
    sleep(3)

@skip
def test_headless_runs_without_errors(caplog):
    pass


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
        assert_that(sys.path, has_item(mock_path))


def test_write_read_lock_file(tmpdir):
    app = create_mock_app()
    lockfile = tmpdir.join("lockfile")
    pid = str(os.getpid())
    with patch('common.LOCK_FILE', lockfile):
        ak.AutokeyApplication.create_lock_file()
        assert_that(
            app._AutokeyApplication__read_pid_from_lock_file(),
            equal_to(pid)
        )
