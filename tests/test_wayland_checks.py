"""
Tests for autokey.wayland_checks module.

These tests cover:
 - X11 / no-session passthrough (always True)
 - GNOME/Wayland full prerequisite checks
 - Partial-support compositors (KDE, Sway, Hyprland)
 - Unknown compositor best-effort handling
 - _detect_compositor() helper
 - _check_uinput_prerequisites() helper
"""

import types
import pytest

import autokey.wayland_checks as wayland_checks


# ---------------------------------------------------------------------------
# Non-Wayland sessions – always pass
# ---------------------------------------------------------------------------

def test_wayland_checks_passes_without_session_type(monkeypatch):
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    assert wayland_checks.waylandChecks() is True


def test_wayland_checks_passes_on_x11(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert wayland_checks.waylandChecks() is True


# ---------------------------------------------------------------------------
# _detect_compositor() — environment-variable-based detection
# ---------------------------------------------------------------------------

def _clear_compositor_env(monkeypatch):
    for var in (
        "XDG_CURRENT_DESKTOP", "DESKTOP_SESSION", "XDG_SESSION_DESKTOP",
        "GNOME_DESKTOP_SESSION_ID", "SWAYSOCK", "HYPRLAND_INSTANCE_SIGNATURE",
    ):
        monkeypatch.delenv(var, raising=False)
    # Make pgrep always fail so process-inspection fallback doesn't interfere
    monkeypatch.setattr(
        wayland_checks.subprocess, "run",
        lambda *a, **kw: types.SimpleNamespace(returncode=1, stdout=b""),
    )


def test_detect_compositor_gnome_via_xdg_current_desktop(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    assert wayland_checks._detect_compositor() == "gnome"


def test_detect_compositor_gnome_via_session_desktop(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "gnome")
    assert wayland_checks._detect_compositor() == "gnome"


def test_detect_compositor_gnome_via_env_var(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("GNOME_DESKTOP_SESSION_ID", "this-is-deprecated")
    assert wayland_checks._detect_compositor() == "gnome"


def test_detect_compositor_kde(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    assert wayland_checks._detect_compositor() == "kde"


def test_detect_compositor_kde_plasma(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "plasma")
    assert wayland_checks._detect_compositor() == "kde"


def test_detect_compositor_sway_via_xdg(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "sway")
    assert wayland_checks._detect_compositor() == "sway"


def test_detect_compositor_sway_via_socket(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("SWAYSOCK", "/run/sway-ipc.sock")
    assert wayland_checks._detect_compositor() == "sway"


def test_detect_compositor_hyprland_via_xdg(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "hyprland")
    assert wayland_checks._detect_compositor() == "hyprland"


def test_detect_compositor_hyprland_via_sig(monkeypatch):
    _clear_compositor_env(monkeypatch)
    monkeypatch.setenv("HYPRLAND_INSTANCE_SIGNATURE", "abc123")
    assert wayland_checks._detect_compositor() == "hyprland"


def test_detect_compositor_unknown(monkeypatch):
    _clear_compositor_env(monkeypatch)
    assert wayland_checks._detect_compositor() == "unknown"


# ---------------------------------------------------------------------------
# _check_uinput_prerequisites()
# ---------------------------------------------------------------------------

class _FakeGroup:
    def __init__(self, members):
        self.gr_mem = members


def test_uinput_ok(monkeypatch):
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "alice")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)
    ok, msg = wayland_checks._check_uinput_prerequisites()
    assert ok is True
    assert msg == ""


def test_uinput_user_not_in_group(monkeypatch):
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "bob")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)
    ok, msg = wayland_checks._check_uinput_prerequisites()
    assert ok is False
    assert "bob" in msg


def test_uinput_group_missing(monkeypatch):
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "alice")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: (_ for _ in ()).throw(KeyError(g)))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)
    ok, msg = wayland_checks._check_uinput_prerequisites()
    assert ok is False
    assert "input" in msg


def test_uinput_no_write_access(monkeypatch):
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "alice")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: False)
    ok, msg = wayland_checks._check_uinput_prerequisites()
    assert ok is False
    assert "uinput" in msg


def test_uinput_root_bypasses_group(monkeypatch):
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "root")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup([]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 0)  # root
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)
    ok, msg = wayland_checks._check_uinput_prerequisites()
    assert ok is True


# ---------------------------------------------------------------------------
# GNOME/Wayland full checks via waylandChecks()
# ---------------------------------------------------------------------------

def _good_gnome_env(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "gnome")
    monkeypatch.delenv("SWAYSOCK", raising=False)
    monkeypatch.delenv("HYPRLAND_INSTANCE_SIGNATURE", raising=False)


def test_gnome_wayland_all_ok(monkeypatch):
    _good_gnome_env(monkeypatch)

    def fake_run(cmd, *a, **kw):
        return types.SimpleNamespace(returncode=0, stdout=b"Enabled: Yes", stderr=b"")

    monkeypatch.setattr(wayland_checks.subprocess, "run", fake_run)
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "alice")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)

    assert wayland_checks.waylandChecks() is True


def test_gnome_wayland_missing_extension(monkeypatch):
    popups = []
    _good_gnome_env(monkeypatch)

    def fake_run(cmd, *a, **kw):
        if "gnome-extensions" in str(cmd):
            raise FileNotFoundError("gnome-extensions not found")
        return types.SimpleNamespace(returncode=1, stdout=b"", stderr=b"")

    monkeypatch.setattr(wayland_checks.subprocess, "run", fake_run)
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "alice")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)
    # Suppress actual popup
    import unittest.mock
    with unittest.mock.patch("autokey.wayland_checks._WaylandChecks__show_popup", lambda t, m: popups.append((t, m)), create=True):
        result = wayland_checks.waylandChecks()

    # Extension missing means GNOME checks fail -> should return False
    assert result is False


def test_gnome_wayland_user_not_in_input_group(monkeypatch):
    _good_gnome_env(monkeypatch)

    def fake_run(cmd, *a, **kw):
        return types.SimpleNamespace(returncode=0, stdout=b"Enabled: Yes", stderr=b"")

    monkeypatch.setattr(wayland_checks.subprocess, "run", fake_run)
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "bob")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)

    import unittest.mock
    with unittest.mock.patch(
        "autokey.wayland_checks.__show_popup", lambda t, m: None, create=True
    ):
        result = wayland_checks.waylandChecks()
    assert result is False


# ---------------------------------------------------------------------------
# Partial-support compositors (KDE, Sway, Hyprland) — should return True
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("compositor,env_var,env_val", [
    ("kde",      "XDG_CURRENT_DESKTOP",          "KDE"),
    ("sway",     "SWAYSOCK",                      "/run/sway.sock"),
    ("hyprland", "HYPRLAND_INSTANCE_SIGNATURE",   "abc123"),
])
def test_partial_compositor_returns_true_when_uinput_ok(
    monkeypatch, compositor, env_var, env_val
):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("XDG_SESSION_DESKTOP", raising=False)
    monkeypatch.delenv("GNOME_DESKTOP_SESSION_ID", raising=False)
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.delenv("SWAYSOCK", raising=False)
    monkeypatch.delenv("HYPRLAND_INSTANCE_SIGNATURE", raising=False)
    monkeypatch.setenv(env_var, env_val)

    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "alice")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)
    # Suppress pgrep calls
    monkeypatch.setattr(
        wayland_checks.subprocess, "run",
        lambda *a, **kw: types.SimpleNamespace(returncode=1, stdout=b""),
    )

    assert wayland_checks.waylandChecks() is True


@pytest.mark.parametrize("compositor,env_var,env_val", [
    ("kde",      "XDG_CURRENT_DESKTOP", "KDE"),
    ("sway",     "SWAYSOCK",            "/run/sway.sock"),
    ("hyprland", "HYPRLAND_INSTANCE_SIGNATURE", "abc123"),
])
def test_partial_compositor_returns_false_when_uinput_missing(
    monkeypatch, compositor, env_var, env_val
):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("XDG_SESSION_DESKTOP", raising=False)
    monkeypatch.delenv("GNOME_DESKTOP_SESSION_ID", raising=False)
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.delenv("SWAYSOCK", raising=False)
    monkeypatch.delenv("HYPRLAND_INSTANCE_SIGNATURE", raising=False)
    monkeypatch.setenv(env_var, env_val)

    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "bob")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: False)
    monkeypatch.setattr(
        wayland_checks.subprocess, "run",
        lambda *a, **kw: types.SimpleNamespace(returncode=1, stdout=b""),
    )

    import unittest.mock
    with unittest.mock.patch(
        "autokey.wayland_checks.__show_popup", lambda t, m: None, create=True
    ):
        result = wayland_checks.waylandChecks()
    assert result is False


# ---------------------------------------------------------------------------
# Unknown compositor — best-effort, always returns True
# ---------------------------------------------------------------------------

def test_unknown_compositor_returns_true(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("XDG_SESSION_DESKTOP", raising=False)
    monkeypatch.delenv("DESKTOP_SESSION", raising=False)
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.delenv("GNOME_DESKTOP_SESSION_ID", raising=False)
    monkeypatch.delenv("SWAYSOCK", raising=False)
    monkeypatch.delenv("HYPRLAND_INSTANCE_SIGNATURE", raising=False)
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "alice")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["alice"]))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)
    monkeypatch.setattr(
        wayland_checks.subprocess, "run",
        lambda *a, **kw: types.SimpleNamespace(returncode=1, stdout=b""),
    )

    assert wayland_checks.waylandChecks() is True


# ---------------------------------------------------------------------------
# Regression: non-interactive user lookup (getpass, not os.getlogin)
# ---------------------------------------------------------------------------

def test_wayland_checks_uses_noninteractive_user_lookup(monkeypatch):
    """getpass.getuser() should be used, not os.getlogin() (fails without a tty)."""
    _good_gnome_env(monkeypatch)

    def fake_run(cmd, *a, **kw):
        return types.SimpleNamespace(returncode=0, stdout=b"Enabled: Yes", stderr=b"")

    monkeypatch.setattr(wayland_checks.subprocess, "run", fake_run)
    monkeypatch.setattr(
        wayland_checks.os, "getlogin",
        lambda: (_ for _ in ()).throw(OSError("no tty")),
    )
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(wayland_checks.os, "access", lambda p, m: True)
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "autokey-user")
    monkeypatch.setattr(
        wayland_checks.grp, "getgrnam", lambda g: _FakeGroup(["autokey-user"])
    )

    assert wayland_checks.waylandChecks() is True
