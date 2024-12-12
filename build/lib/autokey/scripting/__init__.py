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

"""
This package contains the scripting API.

This file centralises the public API classes for easier importing.
"""

import autokey.common

from . import highlevel

from .common import ColourData, DialogData

from .engine import Engine
from .keyboard import Keyboard
from .mouse import Mouse
from autokey.model.store import Store
from .system import System
from .window import Window

# Platform abstraction
if autokey.common.USING_QT:
    from .clipboard_qt import QtClipboard as Clipboard
    from .dialog_qt import QtDialog as Dialog
else:
    from .clipboard_gtk import GtkClipboard as Clipboard
    from .dialog_gtk import GtkDialog as Dialog
