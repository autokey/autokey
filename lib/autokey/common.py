#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
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

import os
from typing import NamedTuple, Iterable

XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
# Runtime dir falls back to cache dir, as a fallback is suggested by the spec
XDG_CACHE_HOME = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
XDG_DATA_HOME = os.environ.get('XDG_DATA_HOME', os.path.expanduser("~/.local/share"))
SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE")
DESKTOP = os.environ.get('XDG_CURRENT_DESKTOP')
if DESKTOP and DESKTOP.lower() in ('kde', 'plasma'):
    DESKTOP = 'KDE'

CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "autokey")
RUN_DIR = os.path.join(os.environ.get('XDG_RUNTIME_DIR', XDG_CACHE_HOME), "autokey")
DATA_DIR = os.path.join(XDG_DATA_HOME, "autokey")
# The desktop file to start autokey during login is placed here
AUTOSTART_DIR = os.path.join(XDG_CONFIG_HOME, "autostart")

LOCK_FILE = os.path.join(RUN_DIR, "autokey.pid")

APP_NAME = "autokey"
CATALOG = ""
VERSION = "0.97.4"
HOMEPAGE = "https://github.com/dlk3/autokey-wayland"
AUTHOR = 'Chris Dekter'
AUTHOR_EMAIL = 'cdekter@gmail.com'
MAINTAINER = 'dlk3'
MAINTAINER_EMAIL = 'dave@daveking.com'
BUG_EMAIL = "autokey-wayland@fire.fundersclub.com"
COPYRIGHT = """
(c) 2008 Sam Peterson
(c) 2009-2012 Chris Dekter
(c) 2014 GuoCi
(c) 2017-2018 Thomas Hess
(c) 2020-2021 Silico Biomancer
(c) 2024 Sam Sebastian
(c) 2026 David King
"""

AuthorData = NamedTuple("AuthorData", (("name", str), ("role", str), ("email", str)))
AboutData = NamedTuple("AboutData", (
    ("program_name", str),
    ("version", str),
    ("program_description", str),
    ("license_text", str),
    ("copyright_notice", str),
    ("homepage_url", str),
    ("bug_report_email", str),
    ("author_list", Iterable[AuthorData])
))
author_data = (
    AuthorData("Sam Peterson", "Original developer", "peabodyenator@gmail.com"),
    AuthorData("Chris Dekter", "Developer", "cdekter@gmail.com"),
    AuthorData("GuoCi", "Python 3 port maintainer", "guociz@gmail.com"),
    AuthorData("Thomas Hess", "PyKDE4 to PyQt5 port", "thomas.hess@udo.edu"),
    AuthorData("Silico Biomancer", "Developer", ""),
    AuthorData("Sam Sebastian", "Wayland port", "sebastiansam55@gmail.com"),
    AuthorData("David King", "Wayland enhancements", "dave@daveking.com")
)
about_data = AboutData(
   program_name="AutoKey for Wayland",
   version=VERSION,
   program_description="Desktop automation utility",
   license_text="""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
""",
   copyright_notice=COPYRIGHT,
   homepage_url=HOMEPAGE,
   bug_report_email=BUG_EMAIL,
   author_list=author_data
)

FAQ_URL = 'https://autokey-wayland.readthedocs.io/en/latest/'
HELP_URL = 'https://autokey-wayland.readthedocs.io/en/latest/'
API_URL = HELP_URL + "/api.html"
BUG_URL = "https://github.com/dlk3/autokey-wayland/issues"

ICON_FILE = "autokey"
ICON_FILE_NOTIFICATION = "autokey-status"
ICON_FILE_NOTIFICATION_DARK = "autokey-status-dark"
ICON_FILE_NOTIFICATION_ERROR = "autokey-status-error"

# Set at the top of each entrypoint app
USED_UI_TYPE = "headless"

# Share parsed command line arguments between modules, Namespace object content
# set by argument_parser.py
ARGS = None

# A list of text strings that are the names of the keyboard and mouse devices
# that we want to recognize automatically during system startup under Wayland.
# There is no need to add names that include the words "keyboard" or "mouse" to
# these lists.  AutoKey will recognize those without them being here.
WAYLAND_KEYBOARD_DEVICE_LIST = (
    'Logitech K270',
    'Logitech K400'
)
WAYLAND_MOUSE_DEVICE_LIST = (
    'Logitech MX Ergo'
)
