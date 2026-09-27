"""
Unit tests for uinput_interface.py's mouse click handling.
"""

import re
from unittest.mock import MagicMock, patch

from evdev import AbsInfo
from evdev import ecodes as e

from autokey import uinput_interface
from autokey.model.button import Button


def _make_interface():
    interface = uinput_interface.UInputInterface.__new__(uinput_interface.UInputInterface)
    interface.btn_map = {Button.LEFT: (272, 0x90001)}
    interface.ui = MagicMock()
    interface._move_cursor_now = MagicMock()
    interface.syn_raw = MagicMock()
    return interface


def test_send_mouse_click_settles_between_move_press_and_release(monkeypatch):
    """
    A button-down immediately followed by button-up, with no settling time
    after the cursor move or between the two, was confirmed to be silently
    dropped (not registered as a click at all) by a real GNOME Wayland
    session. There must be a delay both after the move and between press
    and release.
    """
    interface = _make_interface()

    events = []
    interface.ui.write.side_effect = lambda *args: events.append(("write", args))
    interface.syn_raw.side_effect = lambda: events.append(("syn_raw",))
    monkeypatch.setattr(uinput_interface.time, "sleep", lambda seconds: events.append(("sleep", seconds)))

    uinput_interface.UInputInterface.send_mouse_click.__wrapped__(
        interface, 10, 20, Button.LEFT, False
    )

    interface._move_cursor_now.assert_called_once_with(10, 20, False)

    event_types = [event[0] for event in events]
    assert event_types.count("sleep") == 2
    assert event_types.count("syn_raw") == 2

    # A sleep must occur before the first syn_raw (settling after the move
    # and/or before the button-down), and another sleep must occur between
    # the two syn_raw calls (between button-down and button-up).
    first_syn_index = event_types.index("syn_raw")
    assert "sleep" in event_types[:first_syn_index]

    second_syn_index = event_types.index("syn_raw", first_syn_index + 1)
    assert "sleep" in event_types[first_syn_index + 1:second_syn_index]


def test_send_mouse_click_does_not_call_queued_move_cursor():
    """
    move_cursor() is @queue_method-decorated: calling it from inside an
    already-dequeued method (like send_mouse_click, which runs on the
    queue's worker thread) doesn't block for the move -- it just
    re-enqueues a new task and returns immediately. That silently broke
    click positioning (the click fired at the cursor's stale, pre-move
    position; the real move only happened afterward, too late).
    send_mouse_click() must call the non-queued _move_cursor_now()
    directly so the move actually completes first.
    """
    interface = _make_interface()
    interface.move_cursor = MagicMock()

    uinput_interface.UInputInterface.send_mouse_click.__wrapped__(
        interface, 10, 20, Button.LEFT, False
    )

    interface.move_cursor.assert_not_called()
    interface._move_cursor_now.assert_called_once_with(10, 20, False)


def test_mouse_press_and_release_do_not_call_queued_move_cursor():
    interface = _make_interface()
    interface.move_cursor = MagicMock()

    uinput_interface.UInputInterface.mouse_press.__wrapped__(interface, 10, 20, Button.LEFT)
    uinput_interface.UInputInterface.mouse_release.__wrapped__(interface, 10, 20, Button.LEFT)

    interface.move_cursor.assert_not_called()
    assert interface._move_cursor_now.call_count == 2
    interface._move_cursor_now.assert_any_call(10, 20)


def test_mouse_press_and_release_settle_before_writing(monkeypatch):
    """
    mouse_press()/mouse_release() are typically called back-to-back with a
    real move_cursor() task in between (e.g. from Mouse.select_area()),
    with no other delay separating them on the queue's worker thread. A
    button event written the instant the cursor arrives, with zero
    elapsed time, was confirmed to be silently dropped by a real GNOME
    Wayland session (the same failure mode as send_mouse_click()).
    """
    interface = _make_interface()

    for method in (uinput_interface.UInputInterface.mouse_press, uinput_interface.UInputInterface.mouse_release):
        events = []
        interface.ui.write.side_effect = lambda *args: events.append(("write", args))
        interface.syn_raw.side_effect = lambda: events.append(("syn_raw",))
        monkeypatch.setattr(uinput_interface.time, "sleep", lambda seconds: events.append(("sleep", seconds)))

        method.__wrapped__(interface, 10, 20, Button.LEFT)

        assert events[0] == ("sleep", 0.2)
        assert events[-1] == ("syn_raw",)


def _fake_device(capabilities):
    dev = MagicMock()
    dev.capabilities.return_value = capabilities
    return dev


def test_merge_uinput_capabilities_fixes_zero_abs_resolution():
    """
    A grabbed device (e.g. a VM's guest-integration mouse) with an
    ABS_X/ABS_Y resolution of 0 makes libinput reject the resulting
    combined device outright ("libinput bug: missing tablet
    capabilities: resolution"). evdev.UInput.from_device() copies that
    zero verbatim; the merge must not.
    """
    zero_res = AbsInfo(value=0, min=0, max=65535, fuzz=0, flat=0, resolution=0)
    device = _fake_device({
        e.EV_KEY: [e.KEY_A],
        e.EV_ABS: [(e.ABS_X, zero_res), (e.ABS_Y, zero_res)],
    })

    with patch.object(uinput_interface.evdev, "InputDevice", return_value=device), \
         patch.object(uinput_interface.evdev, "UInput") as mock_uinput:
        uinput_interface._merge_uinput_capabilities(["/dev/input/eventX"], "autokey mouse and keyboard")

    merged = mock_uinput.call_args.kwargs["events"]
    for code, absinfo in merged[e.EV_ABS]:
        assert absinfo.resolution != 0


def test_merge_uinput_capabilities_drops_digitizer_button_codes():
    """
    Digitizer/stylus button codes (BTN_TOOL_PEN, BTN_STYLUS, BTN_TOUCH...)
    combined with ABS axes make libinput classify the merged device as a
    graphics tablet, routing its EV_KEY events through the tablet input
    path instead of the normal keyboard path -- so real key presses never
    reach any window even once the zero-resolution issue is fixed. AutoKey
    has no legitimate use for these codes, so the merge must drop them.
    """
    device = _fake_device({
        e.EV_KEY: [e.KEY_A, e.BTN_LEFT, e.BTN_TOOL_PEN, e.BTN_STYLUS, e.BTN_TOUCH],
    })

    with patch.object(uinput_interface.evdev, "InputDevice", return_value=device), \
         patch.object(uinput_interface.evdev, "UInput") as mock_uinput:
        uinput_interface._merge_uinput_capabilities(["/dev/input/eventX"], "autokey mouse and keyboard")

    merged_keys = mock_uinput.call_args.kwargs["events"][e.EV_KEY]
    assert merged_keys == {e.KEY_A, e.BTN_LEFT}


def test_merge_uinput_capabilities_filters_syn_and_ff():
    """evdev.UInput.from_device() also excludes EV_SYN/EV_FF; the merge must too."""
    device = _fake_device({
        e.EV_KEY: [e.KEY_A],
        e.EV_SYN: [0],
        e.EV_FF: [0],
    })

    with patch.object(uinput_interface.evdev, "InputDevice", return_value=device), \
         patch.object(uinput_interface.evdev, "UInput") as mock_uinput:
        uinput_interface._merge_uinput_capabilities(["/dev/input/eventX"], "autokey mouse and keyboard")

    merged = mock_uinput.call_args.kwargs["events"]
    assert e.EV_SYN not in merged
    assert e.EV_FF not in merged


def _letter_keycodes(count):
    """The first `count` letter keycodes, in a-z order, for boundary tests."""
    import string
    return [getattr(e, "KEY_" + ch) for ch in string.ascii_uppercase[:count]]


def test_is_keyboard_by_capabilities_detects_full_letter_set():
    """A real keyboard reporting all 26 letters must be detected (issue #1003)."""
    device = _fake_device({e.EV_KEY: _letter_keycodes(26)})
    assert uinput_interface._is_keyboard_by_capabilities(device) is True


def test_is_keyboard_by_capabilities_at_threshold_boundary():
    """
    Exactly the threshold count of letters must pass, one fewer must not --
    pins the boundary so a future edit to the threshold is a visible,
    deliberate change rather than an accidental off-by-one.
    """
    at_threshold = _fake_device({e.EV_KEY: _letter_keycodes(uinput_interface._KEYBOARD_LETTER_THRESHOLD)})
    below_threshold = _fake_device({e.EV_KEY: _letter_keycodes(uinput_interface._KEYBOARD_LETTER_THRESHOLD - 1)})

    assert uinput_interface._is_keyboard_by_capabilities(at_threshold) is True
    assert uinput_interface._is_keyboard_by_capabilities(below_threshold) is False


def test_is_keyboard_by_capabilities_rejects_media_remote():
    """
    A device with only a handful of buttons (e.g. a media remote or a
    volume-knob accessory) must not be misclassified as a full keyboard.
    """
    device = _fake_device({e.EV_KEY: [e.KEY_VOLUMEUP, e.KEY_VOLUMEDOWN, e.KEY_MUTE, e.KEY_PLAYPAUSE]})
    assert uinput_interface._is_keyboard_by_capabilities(device) is False


def test_is_keyboard_by_capabilities_handles_device_with_no_ev_key():
    """A device that reports no EV_KEY capability at all (e.g. a pure pointer) must not match."""
    device = _fake_device({e.EV_REL: [e.REL_X, e.REL_Y]})
    assert uinput_interface._is_keyboard_by_capabilities(device) is False


def test_is_mouse_by_capabilities_detects_real_mouse():
    """A real mouse reporting BTN_LEFT plus relative X/Y motion must be detected (issue #1003)."""
    device = _fake_device({
        e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
        e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
    })
    assert uinput_interface._is_mouse_by_capabilities(device) is True


def test_is_mouse_by_capabilities_rejects_touchpad():
    """
    A touchpad reports absolute positioning (EV_ABS), not relative motion --
    this must stay unmatched, the same scope as the existing name-based
    mouse check (which also never matched touchpads).
    """
    abs_info = AbsInfo(value=0, min=0, max=1000, fuzz=0, flat=0, resolution=1)
    device = _fake_device({
        e.EV_KEY: [e.BTN_LEFT, e.BTN_TOOL_FINGER],
        e.EV_ABS: [(e.ABS_X, abs_info), (e.ABS_Y, abs_info)],
    })
    assert uinput_interface._is_mouse_by_capabilities(device) is False


def test_is_mouse_by_capabilities_rejects_relative_device_without_click_button():
    """A relative-motion device with no left-click button (e.g. a scroll-only widget) must not match."""
    device = _fake_device({e.EV_REL: [e.REL_X, e.REL_Y]})
    assert uinput_interface._is_mouse_by_capabilities(device) is False


class _StubItem:
    """A hotkey-bearing item as __isAutoKeyHotkey() actually reads it."""

    def __init__(self, hot_key, modifiers, regex=None, is_inverted=False):
        self.hotKey = hot_key
        self.modifiers = modifiers
        self.windowInfoRegex = re.compile(regex) if regex is not None else None
        self.isInverted = is_inverted


def _make_hotkey_interface(hot_keys, window_title):
    """
    An interface with just enough real state for __isAutoKeyHotkey() to run
    its actual key-translation and window-filter logic unmocked.
    """
    interface = uinput_interface.UInputInterface.__new__(uinput_interface.UInputInterface)
    interface.inv_map = interface._UInputInterface__reverse_mapping(e.keys)
    interface.app = MagicMock()
    interface.app.configManager.hotKeys = hot_keys
    interface.app.configManager.globalHotkeys = []
    interface.mediator = MagicMock()
    interface.mediator.windowInterface.get_window_info.return_value = MagicMock(wm_title=window_title)
    return interface


def _held(*evdev_key_names):
    """A `held` list shaped like __flush_events() builds it: [(anything, code), ...]."""
    return [(None, e.ecodes[name]) for name in evdev_key_names]


class TestIsAutoKeyHotkeyWindowFilter:
    """
    Regression tests for the invert-unaware window-filter check found live-
    testing PR #1223 on Wayland/uinput: an inverted filter's whole point is
    to apply everywhere *except* a regex match, but this check only ever
    asked "does the regex match", so an inverted item was still treated as
    applying in the one window it was meant to exclude. The keystroke got
    blocked there -- with no phrase firing to replace it, since the model's
    own trigger-matching logic (elsewhere) correctly declines to fire --
    while every other, non-excluded window worked fine. Confirmed live via
    the manual VM test in this PR's discussion, on both synthetic and real
    physical keyboard input.
    """

    def test_uninverted_filter_blocks_only_in_the_matching_window(self):
        item = _StubItem("z", ["<ctrl>"], regex="Excluded", is_inverted=False)

        matching = _make_hotkey_interface([item], "Excluded")
        other = _make_hotkey_interface([item], "Other")

        assert matching._UInputInterface__isAutoKeyHotkey(_held("KEY_LEFTCTRL", "KEY_Z")) is True
        assert other._UInputInterface__isAutoKeyHotkey(_held("KEY_LEFTCTRL", "KEY_Z")) is False

    def test_inverted_filter_does_not_block_in_the_excluded_window(self):
        """The exact scenario from #1223: this must NOT block here anymore."""
        item = _StubItem("z", ["<ctrl>"], regex="Excluded", is_inverted=True)

        excluded = _make_hotkey_interface([item], "Excluded")

        assert excluded._UInputInterface__isAutoKeyHotkey(_held("KEY_LEFTCTRL", "KEY_Z")) is False

    def test_inverted_filter_still_blocks_everywhere_else(self):
        item = _StubItem("z", ["<ctrl>"], regex="Excluded", is_inverted=True)

        elsewhere = _make_hotkey_interface([item], "Some Other Window")

        assert elsewhere._UInputInterface__isAutoKeyHotkey(_held("KEY_LEFTCTRL", "KEY_Z")) is True

    def test_no_window_filter_is_unaffected(self):
        item = _StubItem("z", ["<ctrl>"], regex=None, is_inverted=False)

        interface = _make_hotkey_interface([item], "Anything")

        assert interface._UInputInterface__isAutoKeyHotkey(_held("KEY_LEFTCTRL", "KEY_Z")) is True
