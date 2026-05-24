# Copyright (C) 2024 AutoKey Contributors
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
Fallback scripting ``Window`` API for Wayland compositors that do not have a
dedicated AutoKey window interface (e.g., KDE/KWin, Sway, Hyprland).

All methods that require compositor-specific window management return safe
empty/stub values and emit a warning.  Methods that do not depend on the
compositor (e.g., ``wait_for_focus``) still work where possible.
"""

import time

logger = __import__("autokey.logger").logger.get_logger(__name__)

_WAYLAND_LIMITATION_MSG = (
    "Window management is not supported on this Wayland compositor. "
    "Only GNOME (via the AutoKey GNOME Shell extension) is currently supported. "
    "Phrase expansion and hotkeys still work normally."
)


class Window:
    """
    Scripting ``Window`` API stub for unsupported Wayland compositors.

    AutoKey scripts that call these methods on an unsupported Wayland
    compositor will receive empty strings / ``None`` / ``False`` instead of
    crashing with an unhandled exception.
    """

    def __init__(self, mediator):
        self.mediator = mediator
        logger.warning(_WAYLAND_LIMITATION_MSG)

    # ------------------------------------------------------------------
    # Title / class queries (use windowInterface if available)
    # ------------------------------------------------------------------

    def get_active_title(self) -> str:
        """
        Get the title of the active window.

        On unsupported Wayland compositors this always returns an empty string.
        """
        try:
            return self.mediator.windowInterface.get_window_title() or ""
        except Exception:
            return ""

    def get_active_class(self) -> str:
        """
        Get the WM class of the active window.

        On unsupported Wayland compositors this always returns an empty string.
        """
        try:
            return self.mediator.windowInterface.get_window_class() or ""
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Waiting helpers — still functional via polling
    # ------------------------------------------------------------------

    def wait_for_focus(self, title: str, timeOut: float = 5) -> bool:
        """
        Wait for a window with the given title to gain focus.

        On compositors without window-title support this will always return
        ``False`` after the timeout because the title cannot be read.

        :param title: title to match (as a regular expression)
        :param timeOut: seconds to wait before giving up
        :rtype: bool
        """
        import re
        regex = re.compile(title)
        waited = 0.0
        while waited <= timeOut:
            current = self.get_active_title()
            if regex.match(current):
                return True
            if timeOut == 0:
                break
            time.sleep(0.3)
            waited += 0.3
        return False

    def wait_for_exist(self, title: str, timeOut: float = 5, by_hex: bool = False) -> bool:
        """
        Wait for a window with the given title to be created.

        Always returns ``False`` on unsupported Wayland compositors because the
        window list cannot be retrieved.
        """
        logger.warning(
            "window.wait_for_exist() is not supported on this Wayland compositor."
        )
        return False

    # ------------------------------------------------------------------
    # Window management — unsupported stubs
    # ------------------------------------------------------------------

    def _unsupported(self, method_name: str):
        logger.warning(
            "window.%s() is not supported on this Wayland compositor.  %s",
            method_name,
            _WAYLAND_LIMITATION_MSG,
        )

    def activate(self, title, switchDesktop=False, matchClass=False, by_hex=False):
        """Activate the specified window (not supported on this compositor)."""
        self._unsupported("activate")

    def close(self, title, matchClass=False, by_hex=False):
        """Close the specified window (not supported on this compositor)."""
        self._unsupported("close")

    def resize_move(self, title, xOrigin=-1, yOrigin=-1, width=-1, height=-1,
                    matchClass=False, by_hex=False):
        """Resize/move the specified window (not supported on this compositor)."""
        self._unsupported("resize_move")

    def move_to_desktop(self, title, deskNum, matchClass=False, by_hex=False):
        """Move the window to a desktop (not supported on this compositor)."""
        self._unsupported("move_to_desktop")

    def switch_desktop(self, deskNum):
        """Switch to the specified desktop (not supported on this compositor)."""
        self._unsupported("switch_desktop")

    def set_property(self, title, action, prop, matchClass=False, by_hex=False):
        """Set a window property (not supported on this compositor)."""
        self._unsupported("set_property")

    def get_active_geometry(self):
        """Return the active window geometry (not supported on this compositor)."""
        self._unsupported("get_active_geometry")
        return None

    def get_window_geometry(self, title, by_hex=False):
        """Return the window geometry for the given title (not supported)."""
        self._unsupported("get_window_geometry")
        return None

    def get_window_list(self, filter_desktop=-1):
        """Return a list of windows (not supported on this compositor)."""
        self._unsupported("get_window_list")
        return []

    def get_window_hex(self, title):
        """Return the hex ID of a window (not supported on this compositor)."""
        self._unsupported("get_window_hex")
        return None

    def center_window(self, title=":ACTIVE:", win_width=None, win_height=None,
                      monitor=0, matchClass=False, by_hex=False):
        """Center the window (not supported on this compositor)."""
        self._unsupported("center_window")
