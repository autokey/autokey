# Copyright (C) 2019 Thomas Hess <thomas.hess@udo.edu>

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
These tests are designed to catch errors in every possible codepath in app
initialisation and running.
They do not assert correct running, they only help with catching errors.
"""

import typing
import pathlib
import sys

from unittest.mock import Mock, MagicMock, patch

import pytest
from hamcrest import *

from autokey.configmanager.configmanager import ConfigManager
from autokey.service import PhraseRunner
import autokey.model
import autokey.service
from autokey.scripting import Engine
from autokey.baseapp import BaseApp

def nothing():
    # Silence error
    # with raises(SystemExit):
    #     sys.exit()
    return

@patch.object(autokey.service.Service, "start")
@patch.object(autokey.monitor.FileMonitor, "start")
def init_app(mock1, mock2):
    # Because testing arguments aren't valid arguments for the app.
    with patch("autokey.argument_parser.parse_args"):
        app = BaseApp(MagicMock)
        app.UI.show_error_dialog = MagicMock
        app.UI.show_configure_async = MagicMock
        # Close the app, end tests. Happens at end of BaseApp.initialise().
        app.UI.initialise = nothing
        app.UI.show_configure = nothing
        app.UI.notifier = Mock()
        # app.UI.notifier.rebuild_menu = nothing
        app.service = MagicMock
        app.service.mediator = Mock()
        app.service.mediator.interface = Mock()
        with patch("dbus.mainloop.glib.DBusGMainLoop") and patch("autokey.common.AppService"):
            app.initialise(True)
            app.service.mediator = Mock()
            app.service.mediator.interface = Mock()
    return app

def test_init():
    # Check for errors during init process.
    app = init_app()
    # app.initialise(True)
    # assert_that( calling(init_app),
    #         not_(raises(Exception)),
    #         "Initialising baseapp raises exception")
    false = lambda x: False
    with patch("os.path.exists", side_effect=false) and patch("os.mkdir"):
        init_app()


def test_default_dirs():
    with patch("os.makedirs"):
        app = init_app()
        assert_that( calling(app.create_default_dirs),
                not_(raises(Exception)),
                "Creating default dirs raises exception")
        false = lambda x: False
        with patch("os.path.exists", side_effect=false):
            assert_that( calling(app.create_default_dirs),
                    not_(raises(Exception)),
                    "Creating default dirs raises exception")

def test_verifyNotRunning():
    app = init_app()
    app._BaseApp__verifyNotRunning()
    false = lambda x: False
    with patch("os.path.exists", side_effect=false) and patch("os.mkdir"):
        app._BaseApp__verifyNotRunning()
    pipe = lambda : ["autokey".encode()]
    with patch("subprocess.Popen.communicate", side_effect=pipe):
        with pytest.raises(SystemExit):
            app._BaseApp__verifyNotRunning()

def test_createLockFile():
    false = lambda x: False
    with patch("os.path.exists", side_effect=false) and patch("os.mkdir"):
        app = init_app()
        app._BaseApp__createLockFile()

def test_service():
    app = init_app()
    app.pause_service()
    app.unpause_service()
    app.toggle_service()

def test_hotkey():
    app = init_app()
    app.init_global_hotkeys(app.configManager)
    with patch("autokey.interface.XInterfaceBase.grab_hotkey"):
        app.hotkey_created(Mock())
        app.hotkey_removed(Mock())

def test_config():
    app = init_app()
    app.config_altered(True)

def test_path():
    app = init_app()
    path = "/trashpath"
    app.path_created_or_modified(path)
    app.path_removed(path)
