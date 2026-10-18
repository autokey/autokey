#!/usr/bin/env python3
"""Minimal paste-target for manual/VM testing.

A Tk window whose Text widget content is continuously mirrored to a
file, so an external process (e.g. a script driving AutoKey through a
real desktop session over SSH) can query exactly what got pasted
without screenshots or OCR. Useful for verifying AutoKey's various
SendMode.CB_* paste paths end-to-end on a real X11/Wayland session,
where the usual pytest suite can't reach (no real clipboard owner,
no real compositor).

Usage:
    python3 paste_probe.py [outfile]

outfile defaults to /tmp/paste-probe.out. Focus the window, trigger
an AutoKey phrase/hotkey configured to paste into the active window,
then read outfile to see exactly what arrived. Press Escape while the
window is focused to clear it between test runs.
"""
import sys
import tkinter as tk

OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/paste-probe.out"

root = tk.Tk()
root.title("Paste Probe")
root.geometry("600x300")

text = tk.Text(root, font=("Monospace", 16))
text.pack(fill="both", expand=True)
text.focus_force()


def clear(event=None):
    text.delete("1.0", "end")
    return "break"


text.bind("<Escape>", clear)

last = None


def poll():
    global last
    content = text.get("1.0", "end-1c")
    if content != last:
        last = content
        with open(OUTFILE, "w") as f:
            f.write(content)
    root.after(150, poll)


root.after(150, poll)
root.mainloop()
