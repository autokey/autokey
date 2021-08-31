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
from time import sleep

import unittest
from unittest.mock import patch
import pytest
skip = pytest.mark.skip
import hamcrest as hm

import autokey
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

# Automatically patch config dirs wherever needed, so that tests don't
# overwrite or rely on user config.
# @pytest.fixture(scope="function", autouse=True)
# def create_file_patches(tmp_path, request):
#     patches = []
#     # Patching relies on namespaces. Since configmanager uses from
#     # ..constants import X, we have to use configmanager's namespace
#     # as well as of common.
#     patch_paths = {
#         'CONFIG_DIR': str(tmp_path),
#         'CONFIG_DEFAULT_FOLDER': str(tmp_path / "data"), 
#         'CONFIG_FILE': str(tmp_path / "autokey.json"),
#         'CONFIG_FILE_BACKUP': str(tmp_path / "autokey.json~"),
#         'LOCK_FILE': str(tmp_path / "autokey.pid"),
#     }
#     namespaces = ['autokey.common', 'autokey.configmanager.configmanager']

#     for name in namespaces:
#         for patched, path in patch_paths.items():
#             patches.append(
#                 patch(name + '.' + patched, path)
#             )
#     for p in patches.copy():
#         try:
#             p.__enter__()
#         except AttributeError:
#             patches.remove(p)
#             continue

#     def unpatch():
#         for p in patches:
#             p.__exit__()
#     request.addfinalizer(unpatch)



@skip(reason="Not currently parallel enough to run and shut down simultaneously. Creating gtkui.Application is blocking")
@patch('sys.argv', ['autokey-app-testing'])
def test_gtk_application_runs_without_errors(caplog):
    app = gtkui.Application()
    # app.show_configure()
    app._Application__completeShutdown()
    hm.assert_that(get_errors_in_log(caplog), hm.empty())

# @patch('sys.argv', ['autokey-app-testing'])
# def test_clear_hotkey_button():
#     app = gtkui.Application()

#     app.show_configure()
#     while app.configWindow is None:
#         sleep(0.1)
#     app.configWindow.treeView.get_selection().settingsWidget.on_clearHotkeyButton_clicked()

#     app._Application__completeShutdown()

