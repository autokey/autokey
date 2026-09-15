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
