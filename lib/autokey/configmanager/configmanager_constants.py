# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

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

"""This file holds constants used in the configuration manager."""

import os.path

from autokey import common

# Configuration file location
CONFIG_FILE = os.path.join(common.CONFIG_DIR, "autokey.json")
CONFIG_DEFAULT_FOLDER = os.path.join(common.CONFIG_DIR, "data")
CONFIG_FILE_BACKUP = CONFIG_FILE + '~'

DEFAULT_ABBR_FOLDER = "Imported Abbreviations"
RECENT_ENTRIES_FOLDER = "Recently Typed"

# JSON Key names used in the configuration file
INTERFACE_TYPE = "interfaceType"
IS_FIRST_RUN = "isFirstRun"
SERVICE_RUNNING = "serviceRunning"
MENU_TAKES_FOCUS = "menuTakesFocus"
SHOW_TRAY_ICON = "showTrayIcon"
SORT_BY_USAGE_COUNT = "sortByUsageCount"
PROMPT_TO_SAVE = "promptToSave"
INPUT_SAVINGS = "inputSavings"
ENABLE_QT4_WORKAROUND = "enableQT4Workaround"
UNDO_USING_BACKSPACE = "undoUsingBackspace"
WINDOW_DEFAULT_SIZE = "windowDefaultSize"
HPANE_POSITION = "hPanePosition"
COLUMN_WIDTHS = "columnWidths"
SHOW_TOOLBAR = "showToolbar"
NOTIFICATION_ICON = "notificationIcon"
WORKAROUND_APP_REGEX = "workAroundApps"
DISABLED_MODIFIERS = "disabledModifiers"
TRIGGER_BY_INITIAL = "triggerItemByInitial"
SCRIPT_GLOBALS = "scriptGlobals"
GTK_THEME = "gtkTheme"
GTK_TREE_VIEW_EXPANDED_ROWS = "gtkExpandedRows"
PATH_LAST_OPEN = "pathLastOpen"
