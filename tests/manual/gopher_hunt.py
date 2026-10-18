#!/usr/bin/env python3
"""Whack-a-gopher target for testing AutoKey's image-matching scripting
API (autokey.scripting.highlevel: visgrep/click_on_pat).

A gopher sprite appears at a random position on the canvas. An
external automation script is expected to locate it on screen by
image match and click it. Every click is logged with a timestamp, so
consecutive hit timestamps measure how fast the find-and-click loop
runs. A hit increments the score and respawns the gopher at a new
random position; a miss decrements the score and leaves the gopher
where it is.

Usage:
    python3 gopher_hunt.py [gopher.png] [logfile]

gopher.png defaults to gopher.png next to this script; logfile
defaults to /tmp/gopher-hunt.log (JSON lines). Press Escape while the
window is focused to reset the score, round counter, and log file.
"""
import json
import os
import random
import sys
import time
import tkinter as tk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GOPHER_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRIPT_DIR, "gopher.png")
LOG_PATH = sys.argv[2] if len(sys.argv) > 2 else "/tmp/gopher-hunt.log"

CANVAS_WIDTH = 900
CANVAS_HEIGHT = 650

root = tk.Tk()
root.title("Gopher Hunt")

status = tk.Label(root, text="Score: 0   Round: 0", font=("Sans", 16))
status.pack(pady=8)

canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="#e8f5e0")
canvas.pack(padx=8, pady=8)

gopher_image = tk.PhotoImage(file=GOPHER_PATH)
gopher_w = gopher_image.width()
gopher_h = gopher_image.height()

state = {"score": 0, "round": 0, "gopher_id": None, "x": 0, "y": 0, "spawn_t": 0.0}

log_file = open(LOG_PATH, "a")


def log_event(event, **fields):
    record = {"event": event, "t": time.time()}
    record.update(fields)
    log_file.write(json.dumps(record) + "\n")
    log_file.flush()


def update_status():
    status.config(text=f"Score: {state['score']}   Round: {state['round']}")


def spawn_gopher():
    state["round"] += 1
    x = random.randint(0, CANVAS_WIDTH - gopher_w)
    y = random.randint(0, CANVAS_HEIGHT - gopher_h)
    state["x"], state["y"] = x, y
    state["spawn_t"] = time.time()
    if state["gopher_id"] is not None:
        canvas.delete(state["gopher_id"])
    state["gopher_id"] = canvas.create_image(x, y, anchor="nw", image=gopher_image)
    log_event("spawn", round=state["round"], x=x, y=y, w=gopher_w, h=gopher_h)
    update_status()


def on_canvas_click(event):
    gx, gy = state["x"], state["y"]
    hit = gx <= event.x <= gx + gopher_w and gy <= event.y <= gy + gopher_h
    elapsed = time.time() - state["spawn_t"]
    if hit:
        state["score"] += 1
        log_event(
            "hit", round=state["round"], click_x=event.x, click_y=event.y,
            gopher_x=gx, gopher_y=gy, elapsed=elapsed, score=state["score"],
        )
        flash("#8fdb8f")
        spawn_gopher()
    else:
        state["score"] -= 1
        log_event(
            "miss", round=state["round"], click_x=event.x, click_y=event.y,
            gopher_x=gx, gopher_y=gy, elapsed=elapsed, score=state["score"],
        )
        flash("#f2a0a0")
    update_status()


def flash(color, duration_ms=120):
    original = canvas.cget("bg")
    canvas.config(bg=color)
    canvas.after(duration_ms, lambda: canvas.config(bg=original))


def reset(event=None):
    global log_file
    state["score"] = 0
    state["round"] = 0
    log_file.close()
    log_file = open(LOG_PATH, "w")
    spawn_gopher()
    return "break"


canvas.bind("<Button-1>", on_canvas_click)
root.bind("<Escape>", reset)

spawn_gopher()
root.mainloop()
