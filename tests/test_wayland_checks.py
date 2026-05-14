import types

import autokey.wayland_checks as wayland_checks


def test_wayland_checks_passes_without_session_type(monkeypatch):
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)

    assert wayland_checks.waylandChecks() is True


def test_wayland_checks_passes_on_x11(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")

    assert wayland_checks.waylandChecks() is True


def test_wayland_checks_handles_missing_desktop_name(monkeypatch):
    messages = []
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("XDG_SESSION_DESKTOP", raising=False)
    monkeypatch.delenv("DESKTOP_SESSION", raising=False)
    monkeypatch.delenv("GNOME_DESKTOP_SESSION_ID", raising=False)
    monkeypatch.setattr(
        wayland_checks,
        "__show_popup",
        lambda title, message: messages.append((title, message)),
    )

    assert wayland_checks.waylandChecks() is False
    assert messages
    assert '"unknown"' in messages[0][1]


def test_wayland_checks_uses_noninteractive_user_lookup(monkeypatch):
    class InputGroup:
        gr_mem = ["autokey-user"]

    def run_gnome_extensions(*args, **kwargs):
        return types.SimpleNamespace(stdout=b"Enabled: Yes")

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "gnome")
    monkeypatch.setattr(wayland_checks.subprocess, "run", run_gnome_extensions)
    monkeypatch.setattr(wayland_checks.os, "getlogin", lambda: (_ for _ in ()).throw(OSError("no tty")))
    monkeypatch.setattr(wayland_checks.os, "geteuid", lambda: 1000, raising=False)
    monkeypatch.setattr(wayland_checks.os, "access", lambda path, mode: True)
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "autokey-user")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", lambda group: InputGroup())

    assert wayland_checks.waylandChecks() is True


def test_wayland_checks_reports_missing_input_group(monkeypatch):
    messages = []

    def run_gnome_extensions(*args, **kwargs):
        return types.SimpleNamespace(stdout=b"Enabled: Yes")

    def missing_group(group):
        raise KeyError(group)

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "gnome")
    monkeypatch.setattr(wayland_checks.subprocess, "run", run_gnome_extensions)
    monkeypatch.setattr(wayland_checks.os, "access", lambda path, mode: True)
    monkeypatch.setattr(wayland_checks.getpass, "getuser", lambda: "autokey-user")
    monkeypatch.setattr(wayland_checks.grp, "getgrnam", missing_group)
    monkeypatch.setattr(
        wayland_checks,
        "__show_popup",
        lambda title, message: messages.append((title, message)),
    )

    assert wayland_checks.waylandChecks() is False
    assert messages
    assert "input" in messages[0][1]
