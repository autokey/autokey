# Copyright (C) 2026 Kai (Pave Technologies)
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
Wayland compositor detection and window interface factory.

Under Wayland, different compositors require different approaches for
window management (getting active window title/class, window list, etc.).
This module detects the running compositor and provides the appropriate
window interface.
"""

import os
import shutil
import subprocess

logger = __import__("autokey.logger").logger.get_logger(__name__)


# Compositor types
COMPOSITOR_GNOME = "gnome"
COMPOSITOR_KDE = "kde"
COMPOSITOR_SWAY = "sway"
COMPOSITOR_HYPRLAND = "hyprland"
COMPOSITOR_UNKNOWN = "unknown"


def detect_wayland_compositor():
    """
    Detect which Wayland compositor is running.

    Uses environment variables and process checks to determine the compositor.
    Returns one of the COMPOSITOR_* constants.
    """
    xdg_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    xdg_session_desktop = os.environ.get("XDG_SESSION_DESKTOP", "").lower()
    desktop_session = os.environ.get("DESKTOP_SESSION", "").lower()

    # Check for GNOME
    if "gnome" in xdg_desktop or "gnome" in xdg_session_desktop:
        logger.info("Detected GNOME Wayland compositor")
        return COMPOSITOR_GNOME

    # Check for KDE/KWin
    if "kde" in xdg_desktop or "plasma" in xdg_desktop or "kde" in xdg_session_desktop:
        logger.info("Detected KDE Wayland compositor")
        return COMPOSITOR_KDE

    # Check for Sway
    if os.environ.get("SWAYSOCK"):
        logger.info("Detected Sway Wayland compositor")
        return COMPOSITOR_SWAY

    if "sway" in xdg_desktop or "sway" in desktop_session:
        logger.info("Detected Sway Wayland compositor")
        return COMPOSITOR_SWAY

    # Check for Hyprland
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        logger.info("Detected Hyprland Wayland compositor")
        return COMPOSITOR_HYPRLAND

    if "hyprland" in xdg_desktop:
        logger.info("Detected Hyprland Wayland compositor")
        return COMPOSITOR_HYPRLAND

    # Fallback: check running processes
    compositor = _detect_from_processes()
    if compositor != COMPOSITOR_UNKNOWN:
        return compositor

    logger.warning(
        "Could not detect Wayland compositor. "
        "XDG_CURRENT_DESKTOP=%s, XDG_SESSION_DESKTOP=%s",
        os.environ.get("XDG_CURRENT_DESKTOP", ""),
        os.environ.get("XDG_SESSION_DESKTOP", ""),
    )
    return COMPOSITOR_UNKNOWN


def _detect_from_processes():
    """Fallback compositor detection via running process names."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "comm"],
            capture_output=True, text=True, timeout=5
        )
        processes = result.stdout.lower()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return COMPOSITOR_UNKNOWN

    if "gnome-shell" in processes:
        logger.info("Detected GNOME compositor via process list")
        return COMPOSITOR_GNOME
    if "kwin_wayland" in processes:
        logger.info("Detected KDE compositor via process list")
        return COMPOSITOR_KDE
    if "sway" in processes:
        logger.info("Detected Sway compositor via process list")
        return COMPOSITOR_SWAY
    if "hyprland" in processes.split():
        logger.info("Detected Hyprland compositor via process list")
        return COMPOSITOR_HYPRLAND

    return COMPOSITOR_UNKNOWN


def create_wayland_window_interface(compositor=None):
    """
    Factory function to create the appropriate Wayland window interface.

    :param compositor: Override compositor detection (for testing).
                       If None, auto-detects.
    :returns: An instance implementing AbstractWindowInterface.
    :raises RuntimeError: If no suitable window interface can be created.
    """
    if compositor is None:
        compositor = detect_wayland_compositor()

    if compositor == COMPOSITOR_GNOME:
        return _create_gnome_interface()

    # For compositors without a dedicated interface, use the fallback
    logger.warning(
        "No dedicated window interface for compositor %s. "
        "Using fallback interface with limited window detection.",
        compositor,
    )
    return FallbackWindowInterface(compositor)


def _create_gnome_interface():
    """Attempt to create the GNOME extension window interface with error handling."""
    try:
        from autokey.gnome_interface import GnomeExtensionWindowInterface
        return GnomeExtensionWindowInterface()
    except Exception as e:
        logger.error(
            "Failed to connect to GNOME Shell AutoKey extension: %s. "
            "Make sure the AutoKey GNOME extension is installed and enabled. "
            "Falling back to limited window detection.",
            e,
        )
        return FallbackWindowInterface(COMPOSITOR_GNOME)


class FallbackWindowInterface:
    """
    Minimal window interface for Wayland compositors without a dedicated implementation.

    Provides safe defaults so AutoKey can still function for basic hotkey/abbreviation
    expansion, even without full window title/class detection. Window-filter-dependent
    features will not work.
    """

    def __init__(self, compositor_name="unknown"):
        self._compositor = compositor_name
        self._warned = False
        logger.info(
            "FallbackWindowInterface active for compositor %s. "
            "Window title/class detection is unavailable — "
            "window filters will not work.",
            compositor_name,
        )

    def _warn_once(self):
        if not self._warned:
            logger.warning(
                "Window info requested but no compositor-specific interface is available. "
                "Install the appropriate extension or use a supported compositor "
                "(GNOME with AutoKey extension) for full functionality."
            )
            self._warned = True

    def get_window_info(self, window=None, traverse=True):
        from autokey.sys_interface.abstract_interface import WindowInfo
        self._warn_once()
        return WindowInfo(wm_title="", wm_class="")

    def get_window_title(self, window=None, traverse=True):
        self._warn_once()
        return ""

    def get_window_class(self, window=None, traverse=True):
        self._warn_once()
        return ""

    def get_window_list(self):
        self._warn_once()
        return []

    def get_screen_size(self):
        """Return a reasonable default screen size."""
        return [1920, 1080]

    def get_active_window(self):
        self._warn_once()
        return None
