"""
Unit tests for uinput_interface.py's mouse click handling.
"""

from unittest.mock import MagicMock

from autokey import uinput_interface
from autokey.model.button import Button


def _make_interface():
    interface = uinput_interface.UInputInterface.__new__(uinput_interface.UInputInterface)
    interface.btn_map = {Button.LEFT: (272, 0x90001)}
    interface.ui = MagicMock()
    interface.move_cursor = MagicMock()
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

    interface.move_cursor.assert_called_once_with(10, 20, False)

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
