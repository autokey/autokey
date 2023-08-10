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

CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "autokey")
RUN_DIR = os.path.join(os.environ.get('XDG_RUNTIME_DIR', XDG_CACHE_HOME), "autokey")
DATA_DIR = os.path.join(XDG_DATA_HOME, "autokey")
# The desktop file to start autokey during login is placed here
AUTOSTART_DIR = os.path.join(XDG_CONFIG_HOME, "autostart")

LOCK_FILE = os.path.join(RUN_DIR, "autokey.pid")

APP_NAME = "autokey"
CATALOG = ""
VERSION = "0.96.0-beta.9"
HOMEPAGE = "https://github.com/autokey/autokey"
AUTHOR = 'Chris Dekter'
AUTHOR_EMAIL = 'cdekter@gmail.com'
MAINTAINER = 'GuoCi'
MAINTAINER_EMAIL = 'guociz@gmail.com'
BUG_EMAIL = "guociz@gmail.com"
COPYRIGHT = """
(c) 2009-2012 Chris Dekter
(c) 2014 GuoCi
(c) 2017, 2018 Thomas Hess
(c) 2020, 2021 BlueDrink9
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
    AuthorData("Thomas Hess", "PyKDE4 to PyQt5 port", "thomas.hess@udo.edu"),
    AuthorData("GuoCi", "Python 3 port maintainer", "guociz@gmail.com"),
    AuthorData("Chris Dekter", "Developer", "cdekter@gmail.com"),
    AuthorData("Sam Peterson", "Original developer", "peabodyenator@gmail.com")
)
about_data = AboutData(
   program_name="AutoKey",
   version=VERSION,
   program_description="Desktop automation utility",
   license_text="GPL v3",  # TODO: load actual license text from disk somewhere
   copyright_notice=COPYRIGHT,
   homepage_url=HOMEPAGE,
   bug_report_email=BUG_EMAIL,
   author_list=author_data
)


FAQ_URL = "https://github.com/autokey/autokey/wiki/FAQ"
API_URL = "https://autokey.github.io/"
HELP_URL = "https://github.com/autokey/autokey/wiki/Troubleshooting"
BUG_URL = HOMEPAGE + "/issues"

ICON_FILE = "autokey"
ICON_FILE_NOTIFICATION = "autokey-status"
ICON_FILE_NOTIFICATION_DARK = "autokey-status-dark"
ICON_FILE_NOTIFICATION_ERROR = "autokey-status-error"

# Set at the top of each entrypoint app
# headless, gtk or qt
USED_UI_TYPE = "headless"
# x11 or wayland
USED_DISPLAY_SERVER = "x11"

# "x11" or "gnomeext"
USED_WINDOW_INTERFACE = "x11"