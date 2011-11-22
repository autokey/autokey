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

import os.path
CONFIG_DIR = os.path.expanduser("~/.config/autokey")
LOCK_FILE = CONFIG_DIR + "/autokey.pid"
LOG_FILE = CONFIG_DIR + "/autokey.log"
MAX_LOG_SIZE = 5 * 1024 * 1024 # 5 megabytes
MAX_LOG_COUNT = 3
LOG_FORMAT = "%(asctime)s %(levelname)s - %(name)s - %(message)s"

APP_NAME = "AutoKey"
CATALOG = ""
VERSION = "0.80.4"
HOMEPAGE  = "http://autokey.googlecode.com/"
BUG_EMAIL = "cdekter@gmail.com"

FAQ_URL = "http://code.google.com/p/autokey/wiki/FAQ"
HELP_URL = "http://code.google.com/p/autokey/w/list"
DONATE_URL = "https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=L333CPRZ6J8JC"
BUG_URL = "http://code.google.com/p/autokey/issues/entry"

ICON_FILE = "autokey"
ICON_FILE_NOTIFICATION = "autokey-status"
ICON_FILE_NOTIFICATION_DARK = "autokey-status-dark"
ICON_FILE_NOTIFICATION_ERROR = "autokey-status-error"

# Misc
DOMAIN_SOCKET_PATH = "/var/run/autokey-daemon"
PACKET_SIZE = 32


