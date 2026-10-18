#!/usr/bin/env python3
"""Minimal mouse-target for manual/VM testing.

A Tk window with four labeled target areas (left click, right click,
double click, click-and-drag). Every recognized event is appended as
one line to a log file, so an external process (e.g. a script driving
AutoKey/mouse automation through a real desktop session over SSH) can
verify exactly what was registered, where, and in what order.

Usage:
    python3 mouse_probe.py [outfile]

outfile defaults to /tmp/mouse-probe.out. Focus the window, drive
clicks/drags at the target areas, then read outfile to see exactly
what was recorded. Press Escape while the window is focused to clear
the log and reset the on-screen counters between test runs.
"""
import sys
import time
import tkinter as tk

OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mouse-probe.out"

root = tk.Tk()
root.title("Mouse Probe")
root.geometry("500x420")

counters = {"left_click": 0, "right_click": 0, "double_click": 0, "drag": 0}
count_labels = {}

log_file = open(OUTFILE, "a")


def log_event(event_type, widget_x, widget_y, root_x, root_y, extra=""):
    line = (
        f"{time.time():.3f} {event_type} "
        f"widget=({widget_x},{widget_y}) screen=({root_x},{root_y}){extra}\n"
    )
    log_file.write(line)
    log_file.flush()


def bump(event_type):
    counters[event_type] += 1
    count_labels[event_type].config(text=f"{event_type}: {counters[event_type]}")


def flash(widget, color="#8fdb8f", duration_ms=150):
    original = widget.cget("bg")
    widget.config(bg=color)
    widget.after(duration_ms, lambda: widget.config(bg=original))


def make_target(parent, text, base_color):
    frame = tk.Frame(parent, bg=base_color, width=460, height=70, relief="raised", bd=2)
    frame.pack_propagate(False)
    label = tk.Label(frame, text=text, bg=base_color, font=("Sans", 12))
    label.place(relx=0.5, rely=0.5, anchor="center")
    return frame, label


def clear(event=None):
    global log_file
    for key in counters:
        counters[key] = 0
        count_labels[key].config(text=f"{key}: 0")
    log_file.close()
    log_file = open(OUTFILE, "w")
    return "break"


root.bind("<Escape>", clear)

# --- Left click target ---
left_frame, left_label = make_target(root, "Left Click Here", "#dfe7fd")
left_frame.pack(pady=8)


def on_left_click(event):
    bump("left_click")
    flash(left_frame)
    log_event("left_click", event.x, event.y, event.x_root, event.y_root)


for w in (left_frame, left_label):
    w.bind("<Button-1>", on_left_click)

# --- Right click target ---
right_frame, right_label = make_target(root, "Right Click Here", "#fde2e2")
right_frame.pack(pady=8)


def on_right_click(event):
    bump("right_click")
    flash(right_frame, color="#f2a0a0")
    log_event("right_click", event.x, event.y, event.x_root, event.y_root)


for w in (right_frame, right_label):
    w.bind("<Button-3>", on_right_click)

# --- Double click target ---
double_frame, double_label = make_target(root, "Double Click Here", "#fff2c2")
double_frame.pack(pady=8)


def on_double_click(event):
    bump("double_click")
    flash(double_frame, color="#f2d675")
    log_event("double_click", event.x, event.y, event.x_root, event.y_root)


for w in (double_frame, double_label):
    w.bind("<Double-Button-1>", on_double_click)

# --- Drag target ---
drag_frame, drag_label = make_target(root, "Click and Drag Here", "#e2f5e2")
drag_frame.pack(pady=8)
drag_state = {}


def on_drag_start(event):
    drag_state["start"] = (event.x, event.y, event.x_root, event.y_root)
    flash(drag_frame, color="#a8e6a8", duration_ms=400)


def on_drag_end(event):
    if "start" not in drag_state:
        return
    sx, sy, srx, sry = drag_state.pop("start")
    bump("drag")
    log_event(
        "drag",
        sx,
        sy,
        srx,
        sry,
        extra=f" end_widget=({event.x},{event.y}) end_screen=({event.x_root},{event.y_root})",
    )


for w in (drag_frame, drag_label):
    w.bind("<ButtonPress-1>", on_drag_start)
    w.bind("<ButtonRelease-1>", on_drag_end)

# --- Counters display ---
counts_frame = tk.Frame(root)
counts_frame.pack(pady=12)
for key in counters:
    lbl = tk.Label(counts_frame, text=f"{key}: 0", font=("Monospace", 11))
    lbl.pack(anchor="w")
    count_labels[key] = lbl

hint = tk.Label(root, text="Press Escape to clear log + counters", fg="#888888")
hint.pack(pady=6)

root.mainloop()
