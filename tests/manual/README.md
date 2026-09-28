# Manual testing helpers

Scripts here are for testing AutoKey against a real desktop session
(X11 or Wayland, GNOME/KDE/other) — the kind of end-to-end behavior
the pytest suite in `tests/` can't exercise, since it has no real
compositor, clipboard owner, or input device.

**Keep the target window on top and unobstructed before triggering a
test.** These tools interact with real screen coordinates, not a
specific window handle — if another window (AutoKey's own config
window included) overlaps the target, a click can land on whatever is
actually on top instead, and `gopher_hunt.py` specifically can miss
entirely: it works by screenshotting the whole screen, so a sprite
hidden behind another window is invisible to it and every round comes
back not-found, not just misdirected. Bring the target window to the
front (`wmctrl -a "<title>"` or equivalent) immediately before each
run, not just once at the start of a session.

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

## gopher_hunt.py / gopher.png

A "whack-a-mole" style target for testing AutoKey's image-matching
scripting API (`autokey.scripting.highlevel`: `visgrep`/`click_on_pat`,
which wrap xautomation's `xte`/`visgrep` and imagemagick's `xwd` — X11
only, does not work under Wayland). A gopher sprite (`gopher.png`)
appears at a random position on a canvas; an AutoKey script is
expected to locate it on screen by image match and click it:

```
python3 tests/manual/gopher_hunt.py [gopher.png] [logfile]
```

`gopher.png` defaults to the file next to the script; `logfile`
defaults to `/tmp/gopher-hunt.log` (JSON lines, one per spawn/hit/miss
event, each with a timestamp). A hit increments the score and moves
the gopher to a new random position; a miss decrements the score and
leaves it where it is. Press Escape while the window is focused to
reset the score and log.

Example AutoKey script exercising it (`highlevel` is injected directly
into script scope like `mouse`/`window` — no `import` needed):

```python
import time

for i in range(20):
    try:
        highlevel.click_on_pat("/tmp/gopher.png", mousebutton=highlevel.LEFT)
    except highlevel.PatternNotFound:
        pass
    time.sleep(0.05)
```

Each logged hit's `elapsed` field (seconds since that round's gopher
spawned) measures how fast a real find-and-click automation loop runs
end to end, dominated by the `xwd`/`convert`/`visgrep` subprocess
chain — useful for judging whether image-matching automation is fast
enough for a given use case before committing a real script to it.
