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

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import *

from autokey.configmanager.configmanager import ConfigManager
from autokey.service import PhraseRunner
import autokey.model
import autokey.service
from autokey.scripting import Engine
from autokey.baseapp import BaseApp

def init_app():
    # Because testing arguments aren't valid arguments for the app.
    with patch("autokey.argument_parser.parse_args"):
        app = BaseApp(MagicMock)
    return app

def test_init():
    # Check for errors during init process.
    init_app()
    assert_that( calling(init_app),
            not_(raises(Exception)),
            "Initialising baseapp raises exception")

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

@pytest.mark.skip(reason="For some reason the function doesn't show up as an existing attribute.")
def test_verifyNotRunning():
    app = init_app()
    assert_that( calling(app.__verifyNotRunning),
            not_(raises(Exception)),
            "Creating default dirs raises exception")

# def test_verifyNotRunning():
#     app = init_app()
#     assert_that( calling(app.__verifyNotRunning),
#             not_(raises(Exception)),
#             "Creating default dirs raises exception")

# def test_verifyNotRunning():
#     app = init_app()
#     assert_that( calling(app.__verifyNotRunning),
#             not_(raises(Exception)),
#             "Creating default dirs raises exception")

