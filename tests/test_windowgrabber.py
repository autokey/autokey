# Copyright (C) 2026
#
# Tests for WindowGrabber click capture / timeout (issue #1189).

import sys
import time
import types
from unittest.mock import MagicMock

import pytest

# IoMediator / UInput pull in desktop-specific D-Bus stacks. Stub the heavy
# optional deps so these unit tests run without a Wayland desktop or system
# packages installed (this CI/box environment has no dbus/gi/evdev by default).
def _ensure_stub(name, **attrs):
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


_ensure_stub("dbus")
_ensure_stub("dbus.mainloop")
_ensure_stub("dbus.mainloop.glib", DBusGMainLoop=MagicMock())
_ensure_stub("dbus.exceptions", DBusException=type("DBusException", (Exception,), {}))
gi = _ensure_stub("gi")
gi.require_version = MagicMock()
_ensure_stub("gi.repository")
_ensure_stub("gi.repository.GLib", MainLoop=MagicMock())
_ensure_stub("pydbus", SessionBus=MagicMock())
evdev_mod = _ensure_stub("evdev")
evdev_mod.ecodes = MagicMock()
evdev_mod.UInput = MagicMock()
evdev_mod.categorize = MagicMock()
evdev_mod.KeyEvent = type("KeyEvent", (), {})
evdev_mod.RelEvent = type("RelEvent", (), {})
_ensure_stub("evdev.ecodes")
_ensure_stub("pyudev")
_ensure_stub("magic")
_ensure_stub(
    "pyinotify",
    WatchManager=MagicMock,
    Notifier=MagicMock,
    EventsCodes=MagicMock(),
    ProcessEvent=object,
)

from autokey.iomediator.iomediator import IoMediator
from autokey.iomediator.windowgrabber import WindowGrabber
from autokey.model.button import Button
from autokey.sys_interface.abstract_interface import WindowInfo


@pytest.fixture(autouse=True)
def clean_listeners():
    """WindowGrabber mutates the process-global IoMediator.listeners list."""
    original = list(IoMediator.listeners)
    IoMediator.listeners = []
    yield
    IoMediator.listeners = original


def test_windowgrabber_delivers_window_info_on_click():
    dialog = MagicMock()
    grabber = WindowGrabber(dialog, timeout_seconds=None)
    grabber.start()

    assert grabber in IoMediator.listeners

    info = WindowInfo(wm_title="Terminal", wm_class="gnome-terminal-server.Gnome-terminal")
    grabber.handle_mouseclick(10, 20, 1, 2, Button.LEFT, info)

    dialog.receive_window_info.assert_called_once_with(info)
    assert grabber not in IoMediator.listeners


def test_windowgrabber_timeout_notifies_dialog():
    dialog = MagicMock()
    grabber = WindowGrabber(dialog, timeout_seconds=0.05)
    grabber.start()

    deadline = time.time() + 2.0
    while grabber in IoMediator.listeners and time.time() < deadline:
        time.sleep(0.01)

    assert grabber not in IoMediator.listeners
    dialog.receive_window_detect_timeout.assert_called_once()
    (timeout_arg,) = dialog.receive_window_detect_timeout.call_args[0]
    assert timeout_arg == pytest.approx(0.05)
    dialog.receive_window_info.assert_not_called()


def test_windowgrabber_click_cancels_pending_timeout():
    dialog = MagicMock()
    grabber = WindowGrabber(dialog, timeout_seconds=1.0)
    grabber.start()

    info = WindowInfo(wm_title="Firefox", wm_class="firefox.Firefox")
    grabber.handle_mouseclick(0, 0, 0, 0, Button.LEFT, info)

    time.sleep(0.05)
    dialog.receive_window_info.assert_called_once_with(info)
    dialog.receive_window_detect_timeout.assert_not_called()


def test_windowgrabber_double_completion_is_idempotent():
    dialog = MagicMock()
    grabber = WindowGrabber(dialog, timeout_seconds=None)
    grabber.start()

    info = WindowInfo(wm_title="A", wm_class="a.A")
    grabber.handle_mouseclick(0, 0, 0, 0, Button.LEFT, info)
    grabber.handle_mouseclick(0, 0, 0, 0, Button.LEFT, info)

    dialog.receive_window_info.assert_called_once()


def _import_uinput_interface():
    # uinput_interface imports AutokeyApplication only for typing/comments;
    # stub it to avoid pulling the full app stack in unit tests.
    if "autokey.autokey_app" not in sys.modules or not hasattr(sys.modules.get("autokey.autokey_app", None), "AutokeyApplication"):
        app_mod = types.ModuleType("autokey.autokey_app")
        app_mod.AutokeyApplication = type("AutokeyApplication", (), {})
        sys.modules["autokey.autokey_app"] = app_mod
    # Fresh import may already be cached from a failed attempt; drop cache.
    sys.modules.pop("autokey.uinput_interface", None)
    from autokey.uinput_interface import UInputInterface
    return UInputInterface


def test_uinput_button_from_keyevent_helpers():
    UInputInterface = _import_uinput_interface()

    helper = object.__new__(UInputInterface)
    event = MagicMock()
    event.keycode = "BTN_LEFT"
    assert helper._button_from_keyevent(event) == Button.LEFT

    event.keycode = ["BTN_RIGHT", "BTN_MOUSE"]
    assert helper._button_from_keyevent(event) == Button.RIGHT

    event.keycode = "KEY_A"
    assert helper._button_from_keyevent(event) is None


def test_uinput_handle_mouseclick_forwards_to_mediator():
    import queue as queue_mod
    UInputInterface = _import_uinput_interface()

    ui = object.__new__(UInputInterface)
    ui.mediator = MagicMock()
    info = WindowInfo(wm_title="Code", wm_class="code.Code")
    ui.mediator.windowInterface.get_window_info.return_value = info
    ui.mouse_location = MagicMock(return_value=[100, 200])
    ui.relative_mouse_location = MagicMock(return_value=(5, 6))

    while True:
        try:
            UInputInterface.queue.get_nowait()
        except queue_mod.Empty:
            break

    ui.handle_mouseclick(Button.LEFT, None, None)
    method, args = UInputInterface.queue.get_nowait()
    method(*args)

    ui.mediator.handle_mouse_click.assert_called_once_with(
        100, 200, 5, 6, Button.LEFT, info
    )
