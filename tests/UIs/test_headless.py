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
import sys
import subprocess

import unittest
from unittest.mock import patch
import pytest
skip = pytest.mark.skip
import hamcrest as hm

import autokey.headless_app as headless
import tests.helpers_for_tests as testhelpers

logger = __import__("autokey.logger").logger.get_logger(__name__)

def ret_arg(arg):
    return arg

def get_errors_in_log(caplog):
    errors = [record for record in caplog.get_records('call') if record.levelno >= logging.ERROR]
    return errors


@patch('autokey.dbus_service.AppService' , unittest.mock.MagicMock())
@patch('sys.argv', ['autokey-app-testing'])
def test_application_runs_without_errors(caplog, tmp_path):
    config = str(testhelpers.make_dummy_config(tmp_path))
    backup = str(tmp_path / "autokey.json~")
    confman_module_path = "autokey.configmanager.configmanager"
    with \
        patch(confman_module_path + ".CONFIG_DEFAULT_FOLDER", str(tmp_path)), \
        patch(confman_module_path + ".CONFIG_FILE", config), \
        patch(confman_module_path + ".CONFIG_FILE_BACKUP", backup):
            subprocess.call(["xhost", "+SI:localuser:{}".format(os.environ.get('USER'))])
            app = headless.Application()
            with pytest.raises(SystemExit):
                app.shutdown()
                hm.assert_that(get_errors_in_log(caplog), hm.empty())
