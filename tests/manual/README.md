# Manual testing helpers

Scripts here are for testing AutoKey against a real desktop session
(X11 or Wayland, GNOME/KDE/other) — the kind of end-to-end behavior
the pytest suite in `tests/` can't exercise, since it has no real
compositor, clipboard owner, or input device.

## paste_probe.py

A small Tk window that mirrors its text content to a file on every
change, so a test script (local or driving the machine over SSH) can
verify exactly what AutoKey pasted without screenshots or OCR:

```
python3 tests/manual/paste_probe.py [outfile]
```

`outfile` defaults to `/tmp/paste-probe.out`. Typical loop when
testing an AutoKey hotkey/phrase that pastes into the active window:

1. Focus the Paste Probe window.
2. Press Escape (while focused) to clear it before a run.
3. Trigger the AutoKey hotkey under test.
4. Read `outfile` to see exactly what arrived.

Since it's a plain Tk window, it works identically as a paste target
across X11 and Wayland sessions and across GTK/Qt front ends, which
makes it useful for comparing AutoKey's clipboard-paste behavior
across desktop environments without needing a different verification
method per platform.

## mouse_probe.py

A small Tk window with four labeled target areas — left click, right
click, double click, and click-and-drag — for verifying mouse
automation. Every recognized event is appended as one line to a log
file, with both widget-relative and screen-absolute coordinates, so a
test script can verify exactly what was registered, where, and in
what order:

```
python3 tests/manual/mouse_probe.py [outfile]
```

`outfile` defaults to `/tmp/mouse-probe.out`. Typical loop when
testing a mouse-automation script driving AutoKey:

1. Focus the Mouse Probe window.
2. Press Escape (while focused) to clear the log and reset counters.
3. Drive the click/drag under test at the target area(s).
4. Read `outfile` to see exactly what was recorded — event type,
   coordinates, and (for drags) both the start and end position.

On-screen counters and a brief flash on each target also give quick
visual confirmation during manual testing.
