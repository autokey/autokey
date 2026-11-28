#!/usr/bin/env python3
"""
Reproduce dlk3/autokey-wayland#39 (a modifier stays "pressed" after a hotkey)
on a real Wayland session, with exact timing instead of human fingers.

AutoKey grabs every keyboard and re-injects what it reads through its own
"autokey mouse and keyboard" uinput device; the compositor only sees that
device.  This script:

1. creates a fake physical keyboard (its name contains "keyboard", so AutoKey
   grabs it like a real one),
2. presses the hotkey on it, keeps the modifiers held for a chosen time after
   the hotkey fires, then releases them,
3. asks the kernel which keys are still down on AutoKey's output device.  That
   is exactly the state KWin/Mutter use, so "still down" means "stuck".

Any stuck key is released again afterwards, so the session is left usable.

Setup:
  * Start this script first, then (re)start AutoKey: AutoKey only grabs
    keyboards at startup, and a virtual device does not trigger its hotplug
    handling.
  * Bind a script to <left_alt>+<left_ctrl>+z (or pass --hotkey).  Either:
      - fixed send window, no output at all:
            import time
            keyboard.mediator.begin_send()
            time.sleep(1.0)
            keyboard.mediator.finish_send()
      - what real scripts do:
            keyboard.send_keys("<ctrl>+v")
        (raise "uinputDelay" in autokey.json, e.g. to 100, to widen its window)
  * Focus a harmless window (a text editor) and keep your hands off the keyboard.

Usage:
  python3 tests/manual/stuck_key_repro.py [--holds 0,100,200,400,800] [--repeat 3]
"""

import argparse
import errno
import sys
import time

import evdev
from evdev import ecodes as e

AUTOKEY_OUTPUT_NAME = "autokey mouse and keyboard"
FAKE_KEYBOARD_NAME = "AutoKey stuck-key repro keyboard"


def find_device(name):
    for path in evdev.list_devices():
        device = evdev.InputDevice(path)
        if device.name == name:
            return device
        device.close()
    return None


def is_grabbed_by_someone_else(path):
    device = evdev.InputDevice(path)
    try:
        device.grab()
    except OSError as ex:
        return ex.errno == errno.EBUSY
    else:
        device.ungrab()
        return False
    finally:
        device.close()


def wait_for_autokey(fake):
    print("Waiting for AutoKey to start and grab \"{}\" ...".format(FAKE_KEYBOARD_NAME))
    while True:
        output = find_device(AUTOKEY_OUTPUT_NAME)
        if output is not None:
            # AutoKey grabs keyboards before it creates its output device, so this check cannot race its grab.
            if is_grabbed_by_someone_else(fake.device.path):
                print("AutoKey is running and has grabbed the fake keyboard.\n")
                return output
            output.close()
            sys.exit("AutoKey is running but did not grab the fake keyboard: restart AutoKey while this script runs.")
        time.sleep(0.5)


class FakeKeyboard:
    def __init__(self, fake):
        self.fake = fake

    def key(self, code, value, pause):
        self.fake.write(e.EV_KEY, code, value)
        self.fake.syn()
        time.sleep(pause)


def run_trial(keyboard, output_name, modifiers, trigger, hold, settle):
    for code in modifiers:
        keyboard.key(code, 1, 0.04)
    keyboard.key(trigger, 1, 0.06)
    keyboard.key(trigger, 0, hold)  # AutoKey fires uinput hotkeys on this release
    for code in reversed(modifiers):
        keyboard.key(code, 0, 0.03)
    time.sleep(settle)

    output = find_device(output_name)
    if output is None:
        sys.exit("AutoKey's output device disappeared; is AutoKey still running?")
    try:
        used = set(modifiers) | {trigger}
        stuck = sorted(code for code in output.active_keys() if code in used)
    finally:
        output.close()

    for code in stuck:  # the press is dropped by the kernel as a duplicate, the release clears it
        keyboard.key(code, 1, 0.03)
        keyboard.key(code, 0, 0.03)
    return stuck


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hotkey", default="KEY_LEFTALT,KEY_LEFTCTRL,KEY_Z",
                        help="evdev key names, modifiers first and the trigger key last")
    parser.add_argument("--holds", default="0,50,100,200,300,500,800,1200",
                        help="ms the modifiers stay held after the trigger key is released")
    parser.add_argument("--repeat", type=int, default=3, help="trials per hold time")
    parser.add_argument("--settle", type=float, default=2.0, help="seconds to let the script finish before checking")
    args = parser.parse_args()

    codes = [e.ecodes[name] for name in args.hotkey.split(",")]
    modifiers, trigger = codes[:-1], codes[-1]
    holds = [int(ms) for ms in args.holds.split(",")]

    capabilities = {e.EV_KEY: [code for code in e.keys if isinstance(code, int) and 0 < code < e.BTN_MISC]}
    with evdev.UInput(capabilities, name=FAKE_KEYBOARD_NAME) as fake:
        wait_for_autokey(fake).close()
        keyboard = FakeKeyboard(fake)
        print("{:>8}  {:>6}  stuck keys per trial".format("hold ms", "stuck"))
        for hold in holds:
            results = [run_trial(keyboard, AUTOKEY_OUTPUT_NAME, modifiers, trigger, hold / 1000, args.settle)
                       for _ in range(args.repeat)]
            hits = sum(1 for stuck in results if stuck)
            print("{:>8}  {:>3}/{:<2}  {}".format(
                hold, hits, args.repeat,
                "  ".join(",".join(e.KEY[c] for c in stuck) or "-" for stuck in results)))


if __name__ == "__main__":
    main()
