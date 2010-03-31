#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2008 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import os.path
CONFIG_DIR = os.path.expanduser("~/.config/autokey")
LOCK_FILE = CONFIG_DIR + "/autokey.pid"
LOG_FILE = CONFIG_DIR + "/autokey.log"
MAX_LOG_SIZE = 5 * 1024 * 1024 # 5 megabytes
MAX_LOG_COUNT = 3
LOG_FORMAT = "%(levelname)s - %(name)s - %(message)s"

APP_NAME = "AutoKey"
CATALOG = ""
VERSION = "0.61.7"
HOMEPAGE  = "http://autokey.sourceforge.net/"
BUG_EMAIL = "cdekter@gmail.com"

FAQ_URL = "http://code.google.com/p/autokey/wiki/FAQ"
HELP_URL = "http://code.google.com/p/autokey/w/list"
DONATE_URL = "https://sourceforge.net/donate/index.php?group_id=216191"

CONFIG_WINDOW_TITLE = "Configuration"

ICON_FILE = "/usr/share/pixmaps/akicon.png"

USING_QT = True

# Misc
DOMAIN_SOCKET_PATH = "/var/run/autokey-daemon"
PACKET_SIZE = 32


