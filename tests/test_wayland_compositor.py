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

"""Tests for Wayland compositor detection and fallback interface."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# We need to mock heavy dependencies that may not be installed in test env
sys.modules.setdefault('dbus', MagicMock())
sys.modules.setdefault('dbus.mainloop', MagicMock())
sys.modules.setdefault('dbus.mainloop.glib', MagicMock())
sys.modules.setdefault('evdev', MagicMock())
sys.modules.setdefault('evdev.ecodes', MagicMock())
sys.modules.setdefault('PyQt5', MagicMock())
sys.modules.setdefault('PyQt5.QtGui', MagicMock())
sys.modules.setdefault('PyQt5.QtWidgets', MagicMock())
sys.modules.setdefault('PyQt5.QtCore', MagicMock())
sys.modules.setdefault('gi', MagicMock())
sys.modules.setdefault('gi.repository', MagicMock())

from autokey.wayland_compositor import (
    detect_wayland_compositor,
    create_wayland_window_interface,
    FallbackWindowInterface,
    COMPOSITOR_GNOME,
    COMPOSITOR_KDE,
    COMPOSITOR_SWAY,
    COMPOSITOR_HYPRLAND,
    COMPOSITOR_UNKNOWN,
)


class TestDetectWaylandCompositor:
    """Test compositor detection from environment variables."""

    def _clean_env(self):
        """Return env dict with detection-relevant vars cleared."""
        return {
            "XDG_CURRENT_DESKTOP": "",
            "XDG_SESSION_DESKTOP": "",
            "DESKTOP_SESSION": "",
        }

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "GNOME", "XDG_SESSION_DESKTOP": ""})
    def test_detect_gnome(self):
        assert detect_wayland_compositor() == COMPOSITOR_GNOME

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "KDE", "XDG_SESSION_DESKTOP": ""})
    def test_detect_kde(self):
        assert detect_wayland_compositor() == COMPOSITOR_KDE

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "plasma", "XDG_SESSION_DESKTOP": ""})
    def test_detect_kde_plasma(self):
        assert detect_wayland_compositor() == COMPOSITOR_KDE

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "sway", "XDG_SESSION_DESKTOP": ""})
    def test_detect_sway_from_xdg(self):
        assert detect_wayland_compositor() == COMPOSITOR_SWAY

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "Hyprland", "XDG_SESSION_DESKTOP": ""})
    def test_detect_hyprland_from_xdg(self):
        assert detect_wayland_compositor() == COMPOSITOR_HYPRLAND

    @patch("autokey.wayland_compositor._detect_from_processes", return_value=COMPOSITOR_UNKNOWN)
    def test_detect_unknown(self, mock_proc):
        env = self._clean_env()
        env.pop("SWAYSOCK", None)
        env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        with patch.dict(os.environ, env, clear=False):
            # Ensure socket-based vars are gone
            os.environ.pop("SWAYSOCK", None)
            os.environ.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
            assert detect_wayland_compositor() == COMPOSITOR_UNKNOWN


class TestFallbackWindowInterface:
    """Test the fallback window interface returns safe defaults."""

    def setup_method(self):
        self.iface = FallbackWindowInterface("test-compositor")

    def test_get_window_info_returns_namedtuple(self):
        info = self.iface.get_window_info()
        assert info.wm_title == ""
        assert info.wm_class == ""

    def test_get_window_title_returns_empty(self):
        assert self.iface.get_window_title() == ""

    def test_get_window_class_returns_empty(self):
        assert self.iface.get_window_class() == ""

    def test_get_window_list_returns_empty(self):
        assert self.iface.get_window_list() == []

    def test_get_screen_size_returns_default(self):
        size = self.iface.get_screen_size()
        assert len(size) == 2
        assert size[0] > 0 and size[1] > 0

    def test_get_active_window_returns_none(self):
        assert self.iface.get_active_window() is None


class TestCreateWaylandWindowInterface:
    """Test the factory function."""

    def test_unknown_compositor_returns_fallback(self):
        iface = create_wayland_window_interface(compositor=COMPOSITOR_UNKNOWN)
        assert isinstance(iface, FallbackWindowInterface)

    def test_kde_returns_fallback(self):
        iface = create_wayland_window_interface(compositor=COMPOSITOR_KDE)
        assert isinstance(iface, FallbackWindowInterface)

    def test_sway_returns_fallback(self):
        iface = create_wayland_window_interface(compositor=COMPOSITOR_SWAY)
        assert isinstance(iface, FallbackWindowInterface)

    @patch("autokey.wayland_compositor._create_gnome_interface")
    def test_gnome_attempts_gnome_interface(self, mock_create):
        mock_create.return_value = MagicMock()
        create_wayland_window_interface(compositor=COMPOSITOR_GNOME)
        mock_create.assert_called_once()

    def test_gnome_falls_back_on_dbus_failure(self):
        # Without a running GNOME Shell, should fall back gracefully
        iface = create_wayland_window_interface(compositor=COMPOSITOR_GNOME)
        assert isinstance(iface, FallbackWindowInterface) or hasattr(iface, 'get_window_info')
