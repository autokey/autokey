#!/usr/bin/env python3
"""GTK-based paste-target for manual/VM testing.

Same purpose as paste_probe.py (a window whose text content is
continuously mirrored to a file, so an external process can verify
exactly what got pasted without screenshots or OCR), but backed by a
GTK TextView instead of a Tk Text widget.

Needed specifically for verifying SendMode.SELECTION (mouse
middle-click paste): confirmed live that GTK's own PRIMARY-selection
clipboard implementation (used by AutoKey's GTK front end) does not
correctly answer a Tk widget's selection request -- GTK-to-xclip and
GTK-to-GTK both work, GTK-to-Tk does not, even though the click event
itself demonstrably reaches the Tk widget. Tk's own X11
selection-request code is decades old and predates GTK entirely; the
mismatch is between those two toolkits' selection implementations, not
an AutoKey bug. Since real users overwhelmingly paste into GTK, Qt, or
other modern toolkits rather than Tk, this probe verifies the paste
paths against a target that is actually representative.

Usage:
    python3 paste_probe_gtk.py [outfile]

outfile defaults to /tmp/paste-probe.out (the same default as
paste_probe.py, so existing checklist.py helpers work against either
probe without changes). Focus the window, trigger an AutoKey
phrase/hotkey configured to paste into the active window, then read
outfile to see exactly what arrived. Press Escape while the window is
focused to clear it between test runs.
"""
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/paste-probe.out"

win = Gtk.Window(title="Paste Probe")
win.set_default_size(600, 300)

textview = Gtk.TextView()
textview.set_wrap_mode(Gtk.WrapMode.WORD)
buffer = textview.get_buffer()

scroller = Gtk.ScrolledWindow()
scroller.add(textview)
win.add(scroller)


def write_content(*_args):
    start, end = buffer.get_bounds()
    content = buffer.get_text(start, end, True)
    with open(OUTFILE, "w") as f:
        f.write(content)


buffer.connect("changed", write_content)


def on_key_press(widget, event):
    if event.keyval == Gdk.KEY_Escape:
        buffer.set_text("")
        return True
    return False


win.connect("key-press-event", on_key_press)
win.connect("destroy", Gtk.main_quit)
win.show_all()
textview.grab_focus()

Gtk.main()
