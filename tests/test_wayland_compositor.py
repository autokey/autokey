"""
Tests for autokey.wayland_compositor module.

Covers:
 - detect_compositor() environment-variable detection
 - detect_compositor() process-inspection fallback
 - is_supported_compositor()
 - FallbackWindowInterface safe default behaviour
 - create_window_interface() factory routing
"""

import types
import unittest.mock

import pytest

import autokey.wayland_compositor as wc
from autokey.wayland_compositor import (
    COMPOSITOR_GNOME,
    COMPOSITOR_KDE,
    COMPOSITOR_SWAY,
    COMPOSITOR_HYPRLAND,
    COMPOSITOR_UNKNOWN,
    FallbackWindowInterface,
    detect_compositor,
    is_supported_compositor,
    create_window_interface,
)
from autokey.sys_interface.abstract_interface import WindowInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_compositor_env(monkeypatch):
    for var in (
        "XDG_CURRENT_DESKTOP", "DESKTOP_SESSION", "XDG_SESSION_DESKTOP",
        "GNOME_DESKTOP_SESSION_ID", "SWAYSOCK", "HYPRLAND_INSTANCE_SIGNATURE",
    ):
        monkeypatch.delenv(var, raising=False)
    # Prevent process-inspection fallback from matching anything
    monkeypatch.setattr(
        wc.subprocess, "run",
        lambda *a, **kw: types.SimpleNamespace(returncode=1, stdout=b""),
    )


# ---------------------------------------------------------------------------
# detect_compositor() — environment variables
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("env_var,env_val,expected", [
    ("XDG_CURRENT_DESKTOP",        "GNOME",              COMPOSITOR_GNOME),
    ("XDG_SESSION_DESKTOP",        "gnome",              COMPOSITOR_GNOME),
    ("GNOME_DESKTOP_SESSION_ID",   "this-is-deprecated", COMPOSITOR_GNOME),
    ("XDG_CURRENT_DESKTOP",        "KDE",                COMPOSITOR_KDE),
    ("XDG_CURRENT_DESKTOP",        "plasma",             COMPOSITOR_KDE),
    ("XDG_CURRENT_DESKTOP",        "sway",               COMPOSITOR_SWAY),
    ("SWAYSOCK",                   "/run/sway.sock",     COMPOSITOR_SWAY),
    ("XDG_SESSION_DESKTOP",        "hyprland",           COMPOSITOR_HYPRLAND),
    ("HYPRLAND_INSTANCE_SIGNATURE","abc123",             COMPOSITOR_HYPRLAND),
])
def test_detect_compositor_env_vars(monkeypatch, env_var, env_val, expected):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv(env_var, env_val)
    assert detect_compositor() == expected


def test_detect_compositor_unknown_when_no_env(monkeypatch):
    _clear_compositor_env(monkeypatch)
    assert detect_compositor() == COMPOSITOR_UNKNOWN


# ---------------------------------------------------------------------------
# detect_compositor() — process-inspection fallback
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("proc_name,expected", [
    ("gnome-shell",  COMPOSITOR_GNOME),
    ("kwin_wayland", COMPOSITOR_KDE),
    ("sway",         COMPOSITOR_SWAY),
    ("Hyprland",     COMPOSITOR_HYPRLAND),
])
def test_detect_compositor_via_pgrep(monkeypatch, proc_name, expected):
    _clear_compositor_env(monkeypatch)

    def fake_pgrep(args, *a, **kw):
        # pgrep -x <proc_name>
        if args[0] == "pgrep" and args[2] == proc_name:
            return types.SimpleNamespace(returncode=0, stdout=b"1234")
        return types.SimpleNamespace(returncode=1, stdout=b"")

    monkeypatch.setattr(wc.subprocess, "run", fake_pgrep)
    assert detect_compositor() == expected


def test_detect_compositor_pgrep_timeout(monkeypatch):
    """If pgrep times out, detection should still return UNKNOWN gracefully."""
    _clear_compositor_env(monkeypatch)
    import subprocess as sp

    def raise_timeout(*a, **kw):
        raise sp.TimeoutExpired("pgrep", 2)

    monkeypatch.setattr(wc.subprocess, "run", raise_timeout)
    assert detect_compositor() == COMPOSITOR_UNKNOWN


def test_detect_compositor_pgrep_not_found(monkeypatch):
    """If pgrep binary is missing, detection should still return UNKNOWN."""
    _clear_compositor_env(monkeypatch)

    def raise_fnf(*a, **kw):
        raise FileNotFoundError("pgrep")

    monkeypatch.setattr(wc.subprocess, "run", raise_fnf)
    assert detect_compositor() == COMPOSITOR_UNKNOWN


# ---------------------------------------------------------------------------
# is_supported_compositor()
# ---------------------------------------------------------------------------

def test_gnome_is_supported():
    assert is_supported_compositor(COMPOSITOR_GNOME) is True


@pytest.mark.parametrize("compositor", [
    COMPOSITOR_KDE, COMPOSITOR_SWAY, COMPOSITOR_HYPRLAND, COMPOSITOR_UNKNOWN,
])
def test_non_gnome_not_supported(compositor):
    assert is_supported_compositor(compositor) is False


# ---------------------------------------------------------------------------
# FallbackWindowInterface — safe return values
# ---------------------------------------------------------------------------

def test_fallback_get_window_info():
    iface = FallbackWindowInterface(COMPOSITOR_KDE)
    info = iface.get_window_info()
    assert isinstance(info, WindowInfo)
    assert info.wm_title == ""
    assert info.wm_class == ""


def test_fallback_get_window_list():
    iface = FallbackWindowInterface(COMPOSITOR_SWAY)
    assert iface.get_window_list() == []


def test_fallback_get_window_title():
    iface = FallbackWindowInterface(COMPOSITOR_HYPRLAND)
    assert iface.get_window_title() == ""


def test_fallback_get_window_class():
    iface = FallbackWindowInterface(COMPOSITOR_UNKNOWN)
    assert iface.get_window_class() == ""


def test_fallback_get_active_window():
    iface = FallbackWindowInterface(COMPOSITOR_KDE)
    assert iface.get_active_window() is None


def test_fallback_get_screen_size():
    iface = FallbackWindowInterface(COMPOSITOR_SWAY)
    assert iface.get_screen_size() == [0, 0]


def test_fallback_activate_window_no_exception():
    iface = FallbackWindowInterface(COMPOSITOR_KDE)
    iface.activate_window("0xdeadbeef")  # Must not raise


def test_fallback_close_window_no_exception():
    iface = FallbackWindowInterface(COMPOSITOR_KDE)
    iface.close_window("0xdeadbeef")  # Must not raise


# ---------------------------------------------------------------------------
# create_window_interface() — factory routing
# ---------------------------------------------------------------------------

def test_factory_returns_fallback_for_kde():
    iface = create_window_interface(COMPOSITOR_KDE)
    assert isinstance(iface, FallbackWindowInterface)


def test_factory_returns_fallback_for_sway():
    iface = create_window_interface(COMPOSITOR_SWAY)
    assert isinstance(iface, FallbackWindowInterface)


def test_factory_returns_fallback_for_hyprland():
    iface = create_window_interface(COMPOSITOR_HYPRLAND)
    assert isinstance(iface, FallbackWindowInterface)


def test_factory_returns_fallback_for_unknown():
    iface = create_window_interface(COMPOSITOR_UNKNOWN)
    assert isinstance(iface, FallbackWindowInterface)


def test_factory_gnome_falls_back_on_dbus_error(monkeypatch):
    """If the GNOME extension is unavailable, factory falls back gracefully."""
    from autokey import gnome_interface

    def bad_init(self):
        raise Exception("D-Bus not available")

    monkeypatch.setattr(
        gnome_interface.DBusInterface, "__init__", bad_init
    )
    iface = create_window_interface(COMPOSITOR_GNOME)
    assert isinstance(iface, FallbackWindowInterface)


def test_factory_gnome_success(monkeypatch):
    """When the GNOME extension is available, factory returns GnomeExtensionWindowInterface."""
    from autokey import gnome_interface
    from autokey.gnome_interface import GnomeExtensionWindowInterface

    # Stub out the D-Bus constructor
    def stub_init(self):
        self.dbus_interface = unittest.mock.MagicMock()

    monkeypatch.setattr(gnome_interface.DBusInterface, "__init__", stub_init)
    iface = create_window_interface(COMPOSITOR_GNOME)
    assert isinstance(iface, GnomeExtensionWindowInterface)


# ---------------------------------------------------------------------------
# create_scripting_window() — session-aware factory
# ---------------------------------------------------------------------------

def test_create_scripting_window_x11(monkeypatch):
    import autokey.common as common
    from autokey.wayland_compositor import create_scripting_window
    from autokey.scripting.window import Window

    monkeypatch.setattr(common, "SESSION_TYPE", "x11")
    mediator = unittest.mock.MagicMock()
    win = create_scripting_window(mediator)
    assert isinstance(win, Window)


def test_create_scripting_window_wayland_fallback(monkeypatch):
    import autokey.common as common
    from autokey.wayland_compositor import create_scripting_window
    from autokey.scripting.window_wayland_fallback import Window as FallbackWindow

    monkeypatch.setattr(common, "SESSION_TYPE", "wayland")
    monkeypatch.setattr(wc, "detect_compositor", lambda: COMPOSITOR_KDE)
    mediator = unittest.mock.MagicMock()
    win = create_scripting_window(mediator)
    assert isinstance(win, FallbackWindow)
