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
