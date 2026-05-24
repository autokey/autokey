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
Wayland compositor detection and window interface factory.

This module detects the active Wayland compositor (GNOME, KDE/KWin, Sway,
Hyprland, or other) and provides the appropriate AbstractWindowInterface
implementation.  Non-GNOME compositors receive a ``FallbackWindowInterface``
that returns safe empty values so that AutoKey can still perform text expansion
and hotkey matching even when full window-title detection is unavailable.

Usage::

    compositor = detect_compositor()        # e.g. "gnome", "kde", "sway", …
    window_iface = create_window_interface() # ready-to-use AbstractWindowInterface
"""

import os
import subprocess

from autokey.sys_interface.abstract_interface import (
    AbstractWindowInterface,
    WindowInfo,
)

logger = __import__("autokey.logger").logger.get_logger(__name__)

# ---------------------------------------------------------------------------
# Compositor identifiers
# ---------------------------------------------------------------------------

COMPOSITOR_GNOME = "gnome"
COMPOSITOR_KDE = "kde"
COMPOSITOR_SWAY = "sway"
COMPOSITOR_HYPRLAND = "hyprland"
COMPOSITOR_UNKNOWN = "unknown"

# Compositors that have full window-interface support
SUPPORTED_COMPOSITORS = {COMPOSITOR_GNOME}

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_compositor() -> str:
    """
    Return a lowercase string identifying the active Wayland compositor.

    Detection strategy (first match wins):

    1. ``XDG_CURRENT_DESKTOP`` / ``DESKTOP_SESSION`` env-var keywords
    2. Compositor-specific environment variables (``SWAYSOCK``,
       ``HYPRLAND_INSTANCE_SIGNATURE``)
    3. Process inspection via ``pgrep``
    """
    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        or os.environ.get("DESKTOP_SESSION", "").lower()
    )
    session_desktop = os.environ.get("XDG_SESSION_DESKTOP", "").lower()

    # --- GNOME ---
    if (
        "gnome" in desktop
        or "gnome" in session_desktop
        or "GNOME_DESKTOP_SESSION_ID" in os.environ
    ):
        logger.debug("detect_compositor: identified GNOME")
        return COMPOSITOR_GNOME

    # --- KDE / KWin ---
    if "kde" in desktop or "plasma" in desktop or "kde" in session_desktop:
        logger.debug("detect_compositor: identified KDE")
        return COMPOSITOR_KDE

    # --- Sway ---
    if "sway" in desktop or "sway" in session_desktop or "SWAYSOCK" in os.environ:
        logger.debug("detect_compositor: identified Sway")
        return COMPOSITOR_SWAY

    # --- Hyprland ---
    if (
        "hyprland" in desktop
        or "hyprland" in session_desktop
        or "HYPRLAND_INSTANCE_SIGNATURE" in os.environ
    ):
        logger.debug("detect_compositor: identified Hyprland")
        return COMPOSITOR_HYPRLAND

    # --- Process inspection fallback ---
    compositor = _detect_via_pgrep()
    if compositor != COMPOSITOR_UNKNOWN:
        return compositor

    logger.warning(
        "detect_compositor: could not identify compositor; "
        "desktop='%s', session_desktop='%s'",
        desktop,
        session_desktop,
    )
    return COMPOSITOR_UNKNOWN


def _detect_via_pgrep(timeout: float = 2.0) -> str:
    """Try to identify the compositor by inspecting running processes."""
    candidates = [
        ("gnome-shell", COMPOSITOR_GNOME),
        ("kwin_wayland", COMPOSITOR_KDE),
        ("sway", COMPOSITOR_SWAY),
        ("Hyprland", COMPOSITOR_HYPRLAND),
    ]
    for process_name, compositor_id in candidates:
        try:
            result = subprocess.run(
                ["pgrep", "-x", process_name],
                capture_output=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                logger.debug(
                    "detect_compositor: identified %s via pgrep", compositor_id
                )
                return compositor_id
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return COMPOSITOR_UNKNOWN


def is_supported_compositor(compositor: str = None) -> bool:
    """Return True if the compositor has a full AutoKey window interface."""
    if compositor is None:
        compositor = detect_compositor()
    return compositor in SUPPORTED_COMPOSITORS


# ---------------------------------------------------------------------------
# FallbackWindowInterface — safe no-op implementation for unsupported compositors
# ---------------------------------------------------------------------------

class FallbackWindowInterface(AbstractWindowInterface):
    """
    A safe, no-op ``AbstractWindowInterface`` for Wayland compositors that do
    not yet have dedicated AutoKey support.

    All methods return empty/stub values so that the rest of AutoKey can
    continue to function (text expansion, hotkeys) without crashing, while
    window-title filtering is simply disabled.
    """

    _EMPTY_INFO = WindowInfo(wm_title="", wm_class="")

    def __init__(self, compositor: str = COMPOSITOR_UNKNOWN):
        self._compositor = compositor
        logger.warning(
            "FallbackWindowInterface active for compositor '%s'. "
            "Window title/class filtering will not work on this compositor.",
            compositor,
        )

    def get_window_info(self, window=None, traverse: bool = True) -> WindowInfo:
        return self._EMPTY_INFO

    def get_window_list(self):
        return []

    def get_window_title(self, window=None, traverse=True) -> str:
        return ""

    def get_window_class(self, window=None, traverse=True) -> str:
        return ""

    def get_active_window(self):
        return None

    def get_screen_size(self):
        return [0, 0]

    def activate_window(self, window_id):
        logger.debug(
            "FallbackWindowInterface.activate_window called "
            "(no-op on compositor '%s')",
            self._compositor,
        )

    def close_window(self, window_id):
        logger.debug(
            "FallbackWindowInterface.close_window called "
            "(no-op on compositor '%s')",
            self._compositor,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_window_interface(compositor: str = None) -> AbstractWindowInterface:
    """
    Return the appropriate ``AbstractWindowInterface`` for the active Wayland
    compositor.

    * **GNOME** → ``GnomeExtensionWindowInterface`` (full support via D-Bus
      GNOME Shell extension)
    * **Everything else** → ``FallbackWindowInterface`` (safe stub)

    :param compositor: Override the auto-detected compositor string.  Pass
        ``None`` (default) to auto-detect.
    :raises Exception: Re-raises any exception from the GNOME interface
        constructor so the caller can decide whether to fall back or abort.
    """
    if compositor is None:
        compositor = detect_compositor()

    logger.info("create_window_interface: compositor='%s'", compositor)

    if compositor == COMPOSITOR_GNOME:
        from autokey.gnome_interface import GnomeExtensionWindowInterface
        try:
            iface = GnomeExtensionWindowInterface()
            logger.info(
                "create_window_interface: using GnomeExtensionWindowInterface"
            )
            return iface
        except Exception as exc:
            logger.error(
                "create_window_interface: failed to connect to GNOME Shell "
                "extension (%s).  Falling back to FallbackWindowInterface.",
                exc,
            )
            return FallbackWindowInterface(compositor)

    if compositor == COMPOSITOR_KDE:
        logger.info(
            "create_window_interface: KDE/KWin Wayland detected. "
            "Full window interface not yet implemented; using fallback. "
            "Track progress at https://github.com/autokey/autokey/issues/1042"
        )
        return FallbackWindowInterface(compositor)

    if compositor == COMPOSITOR_SWAY:
        logger.info(
            "create_window_interface: Sway compositor detected. "
            "Full window interface not yet implemented; using fallback."
        )
        return FallbackWindowInterface(compositor)

    if compositor == COMPOSITOR_HYPRLAND:
        logger.info(
            "create_window_interface: Hyprland compositor detected. "
            "Full window interface not yet implemented; using fallback."
        )
        return FallbackWindowInterface(compositor)

    logger.warning(
        "create_window_interface: unknown compositor '%s'; using fallback.",
        compositor,
    )
    return FallbackWindowInterface(compositor)


# ---------------------------------------------------------------------------
# Compositor-aware scripting Window class factory
# ---------------------------------------------------------------------------

def create_scripting_window(mediator):
    """
    Return the appropriate scripting ``Window`` object for the current session.

    * Wayland + GNOME → ``window_gnome.Window``
    * Wayland + other → ``window_wayland_fallback.Window`` (stub)
    * X11            → ``window.Window`` (classic wmctrl-based)
    """
    from autokey import common

    if common.SESSION_TYPE != "wayland":
        from autokey.scripting.window import Window
        return Window(mediator)

    compositor = detect_compositor()

    if compositor == COMPOSITOR_GNOME:
        try:
            from autokey.scripting.window_gnome import Window
            return Window(mediator)
        except Exception as exc:
            logger.error(
                "create_scripting_window: failed to load window_gnome (%s); "
                "using fallback Window.",
                exc,
            )

    # Non-GNOME Wayland: return a safe stub Window
    from autokey.scripting.window_wayland_fallback import Window
    return Window(mediator)
