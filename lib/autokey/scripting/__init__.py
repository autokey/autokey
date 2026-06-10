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


# Platform abstraction; Allows code like `import scripting.Dialog`
if autokey.common.USED_UI_TYPE == "QT":
    from .clipboard_qt import QtClipboard as Clipboard
    from .dialog_qt import QtDialog as Dialog
elif autokey.common.USED_UI_TYPE == "GTK":
    from .clipboard_gtk import GtkClipboard as Clipboard
    from .dialog_gtk import GtkDialog as Dialog
elif autokey.common.USED_UI_TYPE == "headless":
    from .clipboard_tkinter import TkClipboard as Clipboard
    # Doesn't actually use anything gtk-specific.
    from .dialog_gtk import GtkDialog as Dialog

# Window scripting API: compositor-aware selection.
# create_scripting_window() is the preferred factory for runtime use;
# the Window class imported here is the default used at module import time
# (before a mediator is available).
if autokey.common.SESSION_TYPE == "wayland":
    from autokey.wayland_compositor import detect_compositor, COMPOSITOR_GNOME
    if detect_compositor() == COMPOSITOR_GNOME:
        try:
            from .window_gnome import Window
        except Exception:
            from .window_wayland_fallback import Window
    else:
        from .window_wayland_fallback import Window
else:
    from autokey.scripting.window import Window
