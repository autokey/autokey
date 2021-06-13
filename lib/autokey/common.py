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
VERSION = "0.96.0-beta.5"
HOMEPAGE = "https://github.com/autokey/autokey"
AUTHOR = 'Chris Dekter'
AUTHOR_EMAIL = 'cdekter@gmail.com'
MAINTAINER = 'GuoCi'
MAINTAINER_EMAIL = 'guociz@gmail.com'
BUG_EMAIL = "guociz@gmail.com"

FAQ_URL = "https://github.com/autokey/autokey/wiki/FAQ"
API_URL = "https://autokey.github.io/"
HELP_URL = "https://github.com/autokey/autokey/wiki/Troubleshooting"
BUG_URL = HOMEPAGE + "/issues"

ICON_FILE = "autokey"
ICON_FILE_NOTIFICATION = "autokey-status"
ICON_FILE_NOTIFICATION_DARK = "autokey-status-dark"
ICON_FILE_NOTIFICATION_ERROR = "autokey-status-error"

USING_QT = False
