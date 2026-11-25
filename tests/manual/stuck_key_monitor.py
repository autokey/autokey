#!/usr/bin/env python3
"""
Watch for keys the compositor would consider stuck, from the compositor's point of view.

Like KWin/Mutter (through libinput), this opens every keyboard without grabbing it, plus AutoKey's
own "autokey mouse and keyboard" output device, and tracks presses and releases per device from the
events it actually receives. An exclusive grab by AutoKey hides events from it exactly as it does
from the compositor. A key this view still has pressed while the kernel says it is up on that device
is a key the compositor never got the release for. For AutoKey's output device, a key held there
while no physical keyboard holds it is reported too.

Only stuck keys are logged, with the recent history of that one key; ordinary typing is not.

Start it before AutoKey so it has the devices open first, the way the compositor does:
  python3 tests/manual/stuck_key_monitor.py [logfile]
"""

import collections
import select
import sys
import time

import evdev
from evdev import ecodes as e

AUTOKEY_OUTPUT_NAME = "autokey mouse and keyboard"
STUCK_AFTER = 3.0  # seconds a key must stay inconsistent before it is reported
RESCAN_EVERY = 0.2


def log(out, message):
    line = "{} {}".format(time.strftime("%Y-%m-%d %H:%M:%S"), message)
    print(line, flush=True)
    if out:
        out.write(line + "\n")
        out.flush()


def key_name(code):
    name = e.KEY.get(code, code)
    return name[0] if isinstance(name, list) else name


def is_keyboard(device):
    keys = set(device.capabilities().get(e.EV_KEY, ()))
    return device.name == AUTOKEY_OUTPUT_NAME or len(keys & {e.KEY_A, e.KEY_Z, e.KEY_H, e.KEY_LEFTALT}) == 4


class Tracked:
    def __init__(self, device):
        self.device = device
        #  EVIOCGKEY (active_keys()) discards the unread key events of the handle it is called on, so the
        #  kernel's key state is read through a second handle, never through the one events are read from.
        self.state = evdev.InputDevice(device.path)
        self.down = {}  # code -> time this view saw it pressed
        self.reported = set()


def main():
    out = open(sys.argv[1], "a") if len(sys.argv) > 1 else None
    tracked = {}  # path -> Tracked
    history = collections.defaultdict(lambda: collections.deque(maxlen=8))  # code -> (time, device, value)
    last_rescan = 0.0
    last_check = 0.0
    log(out, "monitor started")

    while True:
        now = time.monotonic()
        if now - last_rescan >= RESCAN_EVERY:
            last_rescan = now
            present = set(evdev.list_devices())
            for path in list(tracked):
                if path not in present:
                    log(out, "device gone: {} ({})".format(tracked[path].device.name, path))
                    tracked[path].device.close()
                    tracked[path].state.close()
                    del tracked[path]
            for path in present - set(tracked):
                try:
                    device = evdev.InputDevice(path)
                except OSError:
                    continue
                if is_keyboard(device):
                    tracked[path] = Tracked(device)
                    log(out, "watching: {} ({})".format(device.name, path))
                else:
                    device.close()

        fds = {t.device.fd: t for t in tracked.values()}
        ready, _, _ = select.select(list(fds), [], [], 0.1)
        for fd in ready:
            t = fds[fd]
            try:
                events = list(t.device.read())
            except OSError:
                continue
            for event in events:
                if event.type == e.EV_SYN and event.code == e.SYN_DROPPED:
                    t.down = {code: time.monotonic() for code in t.device.active_keys()}
                elif event.type == e.EV_KEY and event.value in (0, 1):
                    history[event.code].append((time.strftime("%H:%M:%S") + ".%03d" % (time.time() % 1 * 1000),
                                                t.device.name, "down" if event.value else "up"))
                    if event.value:
                        t.down.setdefault(event.code, time.monotonic())
                    else:
                        t.down.pop(event.code, None)
                        if event.code in t.reported:
                            t.reported.discard(event.code)
                            log(out, "recovered: {} on {}".format(key_name(event.code), t.device.name))

        now = time.monotonic()
        if now - last_check < 1.0:
            continue
        last_check = now
        physical_held = set()
        for t in tracked.values():
            if t.device.name != AUTOKEY_OUTPUT_NAME:
                try:
                    physical_held |= set(t.state.active_keys())
                except OSError:
                    pass
        for t in tracked.values():
            try:
                kernel_held = set(t.state.active_keys())
            except OSError:
                continue
            is_output = t.device.name == AUTOKEY_OUTPUT_NAME
            for code, since in list(t.down.items()):
                if now - since < STUCK_AFTER or code in t.reported:
                    continue
                if is_output:
                    stuck = code not in physical_held
                    why = "held on AutoKey's output device while no keyboard holds it"
                else:
                    stuck = code not in kernel_held
                    why = "released on the keyboard, but the release never reached readers (grabbed?)"
                if stuck:
                    t.reported.add(code)
                    log(out, "STUCK: {} on {}: {}. Recent history of this key: {}".format(
                        key_name(code), t.device.name, why,
                        "; ".join("{} {} {}".format(*h) for h in history[code])))


if __name__ == "__main__":
    main()
