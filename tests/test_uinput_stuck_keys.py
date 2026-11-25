"""
Regression tests for dlk3/autokey-wayland#39: after a hotkey such as
<left_alt>+<left_ctrl>+z, the compositor kept seeing Alt (or any other key)
as held until the user pressed and released it again.

The physical keyboards are grabbed exclusively, so the compositor only ever
sees AutoKey's own "autokey mouse and keyboard" uinput device. A key whose
press was forwarded before a script started sending, and whose release arrived
while it was sending, used to be dropped, so it stayed down on that device.

In real use the timing that decides this is the gap between the user releasing
the keys and the script's ``begin_send()`` being dequeued, which is why the
bug looks random. Here the order is fixed by hand.
"""

import itertools
import threading
from unittest.mock import MagicMock

import evdev
import pytest
from evdev import ecodes as e

from autokey import uinput_interface


class _KernelLikeUI:
    """
    Stands in for AutoKey's output uinput device and keeps the key state the
    kernel input core keeps for it: a press of a key that is already down, or
    a release of a key that is already up, is dropped and never reaches the
    compositor.  ``held`` is what KWin/Mutter believe is held on this device.
    """

    def __init__(self):
        self.held = set()

    def write(self, type_, code, value):
        if type_ != e.EV_KEY or value == 2:
            return
        if value and code not in self.held:
            self.held.add(code)
        elif not value and code in self.held:
            self.held.discard(code)

    def held_names(self):
        return sorted(e.KEY[code] for code in self.held)


class _FakeKeyboard:
    """A grabbed physical keyboard: events queue up until read(), active_keys() is the live kernel state."""

    _fds = itertools.count(100)

    def __init__(self, path):
        self.fd = next(self._fds)
        self.path = str(path)
        self.name = "Fake keyboard"
        self._pending = []
        self._down = set()

    def _emit(self, code, value):
        self._pending += [
            evdev.InputEvent(0, 0, e.EV_MSC, e.MSC_SCAN, code),
            evdev.InputEvent(0, 0, e.EV_KEY, code, value),
            evdev.InputEvent(0, 0, e.EV_SYN, e.SYN_REPORT, 0),
        ]

    def press(self, name):
        code = e.ecodes[name]
        self._down.add(code)
        self._emit(code, 1)

    def release(self, name):
        code = e.ecodes[name]
        self._down.discard(code)
        self._emit(code, 0)

    def read(self):
        events, self._pending = self._pending, []
        return iter(events)

    def active_keys(self, verbose=False):
        return [(e.KEY[code], code) if verbose else code for code in sorted(self._down)]


class _Hotkey:
    def __init__(self, key, modifiers):
        self.hotKey = key
        self.modifiers = modifiers
        self.windowInfoRegex = None
        self.isInverted = False


@pytest.fixture
def rig(monkeypatch, tmp_path):
    device_node = tmp_path / "event-fake"
    device_node.touch()
    keyboard = _FakeKeyboard(device_node)

    interface = uinput_interface.UInputInterface.__new__(uinput_interface.UInputInterface)
    interface.inv_map = interface._UInputInterface__reverse_mapping(e.keys)
    interface.ui = _KernelLikeUI()
    interface._ui_lock = threading.RLock()
    interface._ui_write_failures = 0
    interface.keyboards = [keyboard]
    interface.mice = []
    interface.devices = {keyboard.fd: keyboard}
    interface.device_paths = [keyboard.path]
    interface.sending = False
    interface._keys_passed_through = set()
    interface._releases_during_send = []
    interface._send_lock = threading.Lock()
    interface.shutdown = False
    interface.handle_keypress = MagicMock()
    interface.handle_keyrelease = MagicMock()
    interface.syn_raw = lambda: interface.ui.write(e.EV_SYN, 0, 0)
    interface.app = MagicMock()
    interface.app.configManager.hotKeys = [_Hotkey("z", ["<left_alt>", "<left_ctrl>"])]
    interface.app.configManager.globalHotkeys = []

    monkeypatch.setattr(uinput_interface.select, "select", lambda r, w, x, timeout: (list(r), [], []))

    def pump():
        interface._UInputInterface__flush_events()

    def script_sends_ctrl_v():
        """What a typical paste script ends up writing: keyboard.send_keys("<ctrl>+v")."""
        uinput_interface.UInputInterface.grab_keyboard.__wrapped__(interface)
        uinput_interface.UInputInterface.send_modified_key.__wrapped__(interface, "v", ["<ctrl>"])

    def script_finishes():
        uinput_interface.UInputInterface.ungrab_keyboard.__wrapped__(interface)

    return interface, keyboard, pump, script_sends_ctrl_v, script_finishes


def _press_hotkey(keyboard, pump):
    for name in ("KEY_LEFTALT", "KEY_LEFTCTRL", "KEY_Z"):
        keyboard.press(name)
        pump()
    keyboard.release("KEY_Z")  # AutoKey fires uinput hotkeys on the key release
    pump()


def test_modifiers_released_before_the_script_starts_sending_are_not_stuck(rig):
    """Control case: the user lets go quickly, before begin_send() is dequeued. This is the run that works."""
    interface, keyboard, pump, script_sends_ctrl_v, script_finishes = rig

    _press_hotkey(keyboard, pump)
    keyboard.release("KEY_LEFTALT")
    keyboard.release("KEY_LEFTCTRL")
    pump()

    script_sends_ctrl_v()
    script_finishes()

    assert interface.ui.held_names() == []


def test_modifiers_released_while_the_script_is_sending_are_not_stuck(rig):
    """
    The user is still holding Alt+Ctrl when the hotkey script starts sending, and lets go before it
    finishes. Ctrl is released by the script's own <ctrl>+v; Alt must be released when sending ends,
    which is the "Alt stays pressed" report from dlk3/autokey-wayland#39.
    """
    interface, keyboard, pump, script_sends_ctrl_v, script_finishes = rig

    _press_hotkey(keyboard, pump)

    script_sends_ctrl_v()
    keyboard.release("KEY_LEFTALT")
    keyboard.release("KEY_LEFTCTRL")
    pump()
    # Still held for the rest of the script, so its own Ctrl chord is not cut short.
    assert "KEY_LEFTALT" in interface.ui.held_names()
    script_finishes()

    assert interface.ui.held_names() == []


def test_a_key_typed_while_a_phrase_starts_expanding_is_not_stuck(rig):
    """
    The repeating-key variant from the issue comments: a letter pressed just before an expansion
    starts and released while it runs must be released when sending ends, or the focused Wayland
    client auto-repeats it forever.
    """
    _interface, keyboard, pump, script_sends_ctrl_v, script_finishes = rig

    keyboard.press("KEY_H")
    pump()
    script_sends_ctrl_v()
    keyboard.release("KEY_H")
    pump()
    script_finishes()

    assert _interface.ui.held_names() == []


def test_a_key_pressed_only_while_sending_is_not_released_afterwards(rig):
    """
    A press that arrives during sending was never forwarded, so its release must not be replayed
    when sending ends: the script may be holding that same key down on purpose.
    """
    interface, keyboard, pump, script_sends_ctrl_v, script_finishes = rig

    script_sends_ctrl_v()
    interface.ui.write(e.EV_KEY, e.KEY_X, 1)  # the script holds X across the end of the send
    keyboard.press("KEY_X")
    keyboard.release("KEY_X")
    pump()
    script_finishes()

    assert interface.ui.held_names() == ["KEY_X"]
