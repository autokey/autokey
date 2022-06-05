# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>
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

"""
This package contains all user dialogs. All these dialogs subclass QDialog.
They perform various input tasks.
"""

__all__ = [
    "validate",
    "EMPTY_FIELD_REGEX",
    "AbbrSettingsDialog",
    "AboutAutokeyDialog",
    "HotkeySettingsDialog",
    "GlobalHotkeyDialog",
    "WindowFilterSettingsDialog",
    "RecordDialog",
    "ShowRecentScriptErrorsDialog"
]

from autokey.qtui.common import EMPTY_FIELD_REGEX, validate


from .abbrsettings import AbbrSettingsDialog
from .hotkeysettings import HotkeySettingsDialog, GlobalHotkeyDialog
from .windowfiltersettings import WindowFilterSettingsDialog
from .recorddialog import RecordDialog
from .about_autokey_dialog import AboutAutokeyDialog
from .show_recent_script_errors import ShowRecentScriptErrorsDialog
