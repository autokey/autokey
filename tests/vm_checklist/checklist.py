#!/usr/bin/env python3
"""
Automates most of MANUAL_TESTING.rst's core checklist against a live VM
(see ../../VM_TESTING.md for how to set one up), using SSH + xdotool for
input and window control rather than VBoxManage
keyboardputscancode/keyboardputstring -- this gives precise window
targeting, real XTEST-level key events (needed to trigger AutoKey's X11
hotkey grabs correctly; xdotool key --window uses XSendEvent and does NOT
trigger passive grabs), and lets each check assert against real evidence
(AutoKey's own debug log, or the paste_probe.py/mouse_probe.py output
files) instead of eyeballing screenshots.

Usage:
    python3 checklist.py --vm m22
    python3 checklist.py --vm m22 --items 1,3,4
    python3 checklist.py --vm m22 --list
    python3 checklist.py --vm m22 --repo-path ~/autokey --keep-phrases

Each check function returns a CheckResult. Screenshots are still taken on
failure (and optionally always) for a human to look at afterward.

Items 6-8 (record a key combination via keyboard/mouse, window-detection
crosshair click-to-select) are NOT automated here and are not planned --
they require driving GTK dialog widgets (treeview navigation, popup
dialogs) with no accessibility API available to query real widget
coordinates. Blind xdotool coordinate/keyboard navigation against the
live config window proved too unreliable in practice (expander clicks
and keyboard focus behaved inconsistently across runs). Run those three
by hand per MANUAL_TESTING.rst.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Optional

# --------------------------------------------------------------------------
# VM registry -- see ../../VM_TESTING.md for how to set up matching VMs
# --------------------------------------------------------------------------

VMS = {
    # Rebuilt from scratch 2026-09-20 (fresh installs, "installed" snapshot
    # for reverting before re-testing install). l24/u22 retired, not rebuilt.
    #
    # "wayland": True selects ydotool (uinput/kernel-level injection)
    # instead of xdotool (XTEST) for key()/type_text()/click(). Confirmed
    # 2026-09-22 on k26: xdotool's XTEST calls succeed at the X11 protocol
    # level (exit 0, no error) but never reach XWayland clients at all --
    # verified via an instrumented Tk probe logging zero KeyPress/click
    # events, and a system-wide `xinput test-xi2 --root` capture showing
    # zero events for an `xdotool key` call (xinput itself warns: "running
    # xinput against an Xwayland server"). ydotool (uinput-level, same
    # injection path AutoKey's own uinput interface uses) does reach
    # XWayland clients correctly. xdotool is still used for window
    # discovery/activation (search/getwindowname/getactivewindow/
    # windowactivate), which all work fine even on Wayland -- only the
    # actual input *injection* needs to switch backend.
    "m22": {"vbox_name": "m22", "session_proc_pattern": "cinnamon$", "wayland": False},
    "u24": {"vbox_name": "u24", "session_proc_pattern": "gnome-shell", "wayland": True},
    "k26": {"vbox_name": "k26", "session_proc_pattern": "plasmashell", "wayland": True},
    # AcreetionOS (Arch-based), XLibre X server (X.Org fork), Cinnamon, X11.
    # Not a VirtualBox VM -- vbox_name=None disables screenshot() (which
    # already no-ops cleanly on a falsy vbox_name), and it uses xdotool/XTEST
    # like m22 since it's a real X11 session, not Wayland.
    "acreetion": {"vbox_name": None, "session_proc_pattern": "cinnamon-session-binary", "wayland": False},
}

# Linux KEY_* evdev keycodes (see /usr/include/linux/input-event-codes.h),
# needed because ydotool's `key` subcommand takes raw keycodes, not names.
# Only the keys checklist.py's hotkeys/escape actually use are mapped;
# extend as needed.
YDOTOOL_KEYCODES = {
    "escape": 1,
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7, "7": 8, "8": 9, "9": 10, "0": 11,
    "q": 16, "w": 17, "e": 18, "r": 19, "t": 20, "y": 21, "u": 22, "i": 23, "o": 24, "p": 25,
    "a": 30, "s": 31, "d": 32, "f": 33, "g": 34, "h": 35, "j": 36, "k": 37, "l": 38,
    "ctrl": 29, "leftctrl": 29, "rightctrl": 97,
    "shift": 42, "leftshift": 42, "rightshift": 54,
    "z": 44, "x": 45, "c": 46, "v": 47, "b": 48, "n": 49, "m": 50,
    "alt": 56, "leftalt": 56, "rightalt": 100,
}

# Confirmed live via `libinput debug-events`: even with GNOME's pointer
# accel-profile forced to "flat" and speed to 0, every relative delta
# ydotool sends is reported by libinput as exactly double the raw value
# (measured across several magnitudes: raw (7,3) -> accelerated (14,6);
# raw (300,300) -> accelerated (600,600)). Reproduced identically against
# both AutoKey's own combined uinput output device and ydotoold's raw
# device directly (with AutoKey not even running), so it is not specific
# to AutoKey's own device capabilities -- root cause not identified, only
# the ratio. NOTE: even with this correction applied, end-to-end click
# delivery to a real application window has not been reliable in live
# testing -- treat click() as unverified/best-effort on u24 until that's
# revisited. See VM._ensure_flat_mouse_accel().
YDOTOOL_ACCEL_FACTOR = 2

# Items whose failure is a known, accepted limitation, not something we're
# chasing further -- see each check's own docstring for the full writeup.
# Kept running (not skipped) so a real fix landing upstream would be
# noticed as a pass, not silently ignored; excluded from the pass/fail exit
# code and flagged in the summary so a run doesn't look like a regression.
WONT_FIX_ITEMS = {
    "5",  # mouse-selection paste: GTK3 bug serving text/plain;charset=utf-8
          # on X11 PRIMARY selection, not an AutoKey bug -- see
          # check_paste_selection()'s docstring and memory
          # project_gtk3_clipboard_text_plain_bug.md.
}

SCRATCH_DIR = Path(__file__).parent / "checklist-results"
LOG_PATH = "/tmp/autokey_integration.log"  # overridden by --log-path in main()
REPO_PATH = "~/autokey"  # overridden by --repo-path in main()


def ssh(host: str, cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", host, cmd], capture_output=True, text=True, timeout=timeout
    )


def ssh_ok(host: str, cmd: str, timeout: int = 30) -> str:
    """Run cmd over SSH, raise if it fails, return stdout."""
    result = ssh(host, cmd, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"ssh {host} failed (exit {result.returncode}): {cmd}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout


def get_session_env(host: str, proc_pattern: str) -> dict:
    """
    Auto-discover DISPLAY/XAUTHORITY/DBUS_SESSION_BUS_ADDRESS/XDG_RUNTIME_DIR
    from a live desktop-session process's /proc/<pid>/environ. SSH sessions
    do not inherit the desktop session's env, so this must be read fresh
    each run rather than assumed.
    """
    pids_out = ssh_ok(host, f"pgrep -f '{proc_pattern}' | head -5")
    wanted = {"DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR"}
    for pid in pids_out.split():
        try:
            environ = ssh_ok(
                host, f"tr '\\0' '\\n' < /proc/{pid}/environ 2>/dev/null"
            )
        except RuntimeError:
            continue
        env = {}
        for line in environ.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                if k in wanted:
                    env[k] = v
        if wanted.issubset(env.keys()):
            return env
    raise RuntimeError(
        f"Could not find a process matching {proc_pattern!r} on {host} "
        f"with a full desktop session environment"
    )


def env_prefix(env: dict) -> str:
    return " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items())


@dataclasses.dataclass
class CheckResult:
    item: str
    name: str
    passed: bool
    detail: str
    screenshot: Optional[str] = None


class VM:
    def __init__(self, alias: str):
        if alias not in VMS:
            raise ValueError(f"Unknown VM alias {alias!r}, known: {list(VMS)}")
        self.alias = alias
        self.vbox_name = VMS[alias]["vbox_name"]
        self.wayland = VMS[alias].get("wayland", False)
        self.env = get_session_env(alias, VMS[alias]["session_proc_pattern"])
        self._env_prefix = env_prefix(self.env)
        # Resolved once, not left as a literal "~": shlex.quote()-ing a path that
        # starts with ~ wraps it in single quotes, which disables tilde expansion
        # in the shell, so `cat > '~/foo'` tries to write a file literally named
        # "~" and fails.
        self.home = ssh_ok(alias, "echo $HOME").strip()
        self.ydotool_raw_keycodes = None
        if self.wayland:
            self._ensure_ydotoold()
            self.ydotool_raw_keycodes = self._detect_ydotool_flavor()
            if not self.ydotool_raw_keycodes:
                self._ensure_flat_mouse_accel()

    def _ensure_ydotoold(self) -> None:
        """Start ydotoold if it isn't already running (needed for key/type/click on Wayland)."""
        running = self.try_run("pgrep -x ydotoold").returncode == 0
        if not running:
            socket_path = f"{self.env.get('XDG_RUNTIME_DIR', '/run/user/1000')}/.ydotool_socket"
            self.run(
                f"nohup ydotoold --socket-path={socket_path} "
                f"> /tmp/ydotoold.log 2>&1 < /dev/null & disown -a"
            )
            time.sleep(1)

    def _ensure_flat_mouse_accel(self) -> None:
        """
        Only needed for the named-key ydotool flavor (u24), whose
        `mousemove` has no `-a`/absolute mode -- see move_mouse_into_window()
        and click(). Every call to that flavor's `mousemove X Y` internally
        warps the cursor to (0,0) first (confirmed live via
        `libinput debug-events`: each call emits a huge clamp-to-corner
        relative delta before the real one), then applies the real delta --
        making a bare relative move behave like an absolute one already.
        GNOME's default adaptive pointer-acceleration profile would then
        distort that "real delta" unpredictably depending on how fast the
        synthetic move looks, so this forces the "flat" profile with
        speed=0 to make the distortion a fixed, calibratable ratio instead
        (see YDOTOOL_ACCEL_FACTOR) rather than a speed-dependent curve.
        Also disables the hot-corner Activities-overview trigger, since
        every mousemove call's internal (0,0) warp would otherwise visit it
        on every single move.
        """
        self.run("gsettings set org.gnome.desktop.peripherals.mouse accel-profile flat")
        self.run("gsettings set org.gnome.desktop.peripherals.mouse speed 0.0")
        self.run("gsettings set org.gnome.desktop.interface enable-hot-corners false")

    def _detect_ydotool_flavor(self) -> bool:
        """
        Two incompatible ydotool CLIs exist in the wild under the same
        package name. Confirmed live: k26's build takes only raw evdev
        keycodes for `key` ("<keycode>:<pressed>", e.g. "29:1 29:0" for
        ctrl), explicitly because it dropped named-key support ("no way to
        know how many keyboard layouts are there in the world"); u24's
        packaged 0.1.8 build takes human-readable combos directly
        ("ctrl+alt+shift+c") and does not understand the keycode:state
        syntax at all. `key --help`'s usage line mentions "keycode"
        specifically only on the raw-keycode build.
        """
        help_text = self.try_run("ydotool key --help").stdout + self.try_run("ydotool key --help").stderr
        return "keycode" in help_text.lower()

    def run(self, cmd: str, timeout: int = 30) -> str:
        return ssh_ok(self.alias, f"{self._env_prefix} {cmd}", timeout=timeout)

    def try_run(self, cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
        return ssh(self.alias, f"{self._env_prefix} {cmd}", timeout=timeout)

    def screenshot(self, name: str) -> Optional[str]:
        if not self.vbox_name:
            return None
        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        path = SCRATCH_DIR / f"{self.alias}_{name}_{int(time.time())}.png"
        result = subprocess.run(
            ["VBoxManage", "controlvm", self.vbox_name, "screenshotpng", str(path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return None
        return str(path)

    def window_list(self) -> str:
        # wmctrl segfaults on KDE Plasma 6.6.6 Wayland (k26) on every
        # invocation, even `wmctrl -l` -- use xdotool instead, which works
        # on all VMs in the fleet. Builds "<id> <name>" lines to match what
        # find_window() expects.
        ids = self.try_run('xdotool search --name ".*"').stdout.split()
        lines = []
        for wid in ids:
            name = self.try_run(f"xdotool getwindowname {wid}").stdout.strip()
            lines.append(f"{wid} {name}")
        return "\n".join(lines)

    def find_window(self, name_fragment: str) -> Optional[str]:
        for line in self.window_list().splitlines():
            if name_fragment.lower() in line.lower():
                return line.split()[0]  # window id
        return None

    def find_window_exact(self, title: str) -> Optional[str]:
        """
        Like find_window(), but requires an exact title match rather than a
        substring. Needed on VMs where a substring match is ambiguous --
        confirmed live on acreetion, whose SSH username happens to be
        "autokey" (so the SSH terminal's own window title, "autokey@...",
        substring-matches "AutoKey" too), and whose autokey-gtk process
        additionally opens extra windows literally titled "autokey-gtk"
        (its own WM_CLASS, distinct from the real config window's actual
        title "AutoKey") -- both false positives that find_window("AutoKey")
        would return before ever reaching the real config window.
        """
        for line in self.window_list().splitlines():
            parts = line.split(maxsplit=1)
            if len(parts) == 2 and parts[1] == title:
                return parts[0]
        return None

    def move_mouse_into_window(self, window_id: str, x: int, y: int):
        """Move the pointer to a window-relative position without clicking."""
        if self.wayland:
            geom = self.get_window_geometry(window_id)
            abs_x, abs_y = geom["X"] + x, geom["Y"] + y
            if self.ydotool_raw_keycodes:
                self.run(f"ydotool mousemove -a -x {abs_x} -y {abs_y}")
            else:
                # No -a/absolute flag on this flavor -- see
                # _ensure_flat_mouse_accel()'s docstring for why a bare
                # relative move already behaves like an absolute one here,
                # and why the target needs dividing by YDOTOOL_ACCEL_FACTOR.
                self.run(f"ydotool mousemove {abs_x // YDOTOOL_ACCEL_FACTOR} {abs_y // YDOTOOL_ACCEL_FACTOR}")
        else:
            self.run(f"xdotool mousemove --window {window_id} {x} {y}")

    def activate(self, window_id: str):
        self.run(f"xdotool windowactivate {window_id}")
        time.sleep(0.4)

    def key(self, combo: str):
        """Key event on whatever currently has focus (real XTEST on X11, uinput on Wayland)."""
        if self.wayland:
            # ydotool's default (no --key-delay/-d) fires all events
            # back-to-back with no gap. For a multi-key combo (e.g.
            # ctrl+alt+shift+c), confirmed live that this can outrun
            # AutoKey's own uinput event processing: a modifier's press
            # event gets missed even though its later release is seen, so
            # AutoKey sees an incomplete modifier set (e.g. bare Ctrl
            # instead of Ctrl+Alt+Shift) and the intended hotkey never
            # matches. ~20ms between events is enough to avoid this in
            # practice, on both ydotool flavors below.
            if self.ydotool_raw_keycodes:
                keys = combo.lower().split("+")
                codes = [YDOTOOL_KEYCODES[k] for k in keys]
                presses = " ".join(f"{c}:1" for c in codes)
                releases = " ".join(f"{c}:0" for c in reversed(codes))
                self.run(f"ydotool key -d 20 {presses} {releases}")
            else:
                # The named-key ydotool flavor does not recognize "Escape"
                # (X11/xdotool's usual spelling) at all -- confirmed live
                # via an instrumented Tk probe: it silently falls through
                # to typing a literal "e" character instead of the real
                # Escape keysym. Its own binary strings show "KEY_ESC", and
                # empirically "esc" is what actually triggers a real
                # Escape keypress on this flavor.
                keys = "+".join(
                    "esc" if key.lower() == "escape" else key
                    for key in combo.split("+")
                )
                self.run(f"ydotool key --key-delay 20 {keys}")
        else:
            self.run(f"xdotool key {combo}")

    def type_text(self, text: str):
        if self.wayland:
            self.run(f"ydotool type {shlex.quote(text)}")
        else:
            self.run(f"xdotool type {shlex.quote(text)}")

    def get_window_geometry(self, window_id: str) -> dict:
        """Returns {'X':.., 'Y':.., 'WIDTH':.., 'HEIGHT':..} via xdotool (works on Wayland too)."""
        out = self.run(f"xdotool getwindowgeometry --shell {window_id}")
        geom = {}
        for line in out.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                geom[key] = int(value) if value.lstrip("-").isdigit() else value
        return geom

    def click(self, window_id: str, button: int = 1, x: Optional[int] = None, y: Optional[int] = None):
        self.activate(window_id)
        if self.wayland:
            # ydotool has no window-relative concept -- convert to absolute
            # screen coordinates using the window's real geometry.
            if x is not None and y is not None:
                geom = self.get_window_geometry(window_id)
                abs_x, abs_y = geom["X"] + x, geom["Y"] + y
                if self.ydotool_raw_keycodes:
                    self.run(f"ydotool mousemove -a -x {abs_x} -y {abs_y}")
                else:
                    # See move_mouse_into_window() / _ensure_flat_mouse_accel().
                    self.run(f"ydotool mousemove {abs_x // YDOTOOL_ACCEL_FACTOR} {abs_y // YDOTOOL_ACCEL_FACTOR}")
            if self.ydotool_raw_keycodes:
                # This flavor's `click` takes a bitmask button code.
                button_codes = {1: 0xC0, 2: 0xC2, 3: 0xC1}
                self.run(f"ydotool click {button_codes[button]:#x}")
            else:
                # This flavor's `click` takes a plain 1/2/3 (left/right/middle)
                # -- confirmed via its own --help, which explicitly differs
                # from the bitmask-code flavor above.
                self.run(f"ydotool click {button}")
        else:
            if x is not None and y is not None:
                self.run(f"xdotool mousemove --window {window_id} {x} {y} click {button}")
            else:
                self.run(f"xdotool click {button}")

    def launch(self, cmd: str, logfile: str = "/tmp/checklist_launch.log") -> None:
        self.run(f"nohup {cmd} > {logfile} 2>&1 < /dev/null & disown -a")
        time.sleep(1.5)

    def kill(self, pattern: str):
        self.try_run(f"pkill -f {shlex.quote(pattern)}")


# --------------------------------------------------------------------------
# Checklist items
# --------------------------------------------------------------------------

CHECKS: dict[str, Callable[[VM], CheckResult]] = {}


def check(item: str, name: str):
    def decorator(fn):
        CHECKS[item] = fn
        fn._item = item
        fn._name = name
        return fn
    return decorator


PROBE_DIR = "/tmp/checklist_probes"


def _ensure_probe(vm: VM, script_name: str, local_path: Path):
    vm.try_run(f"mkdir -p {PROBE_DIR}")
    subprocess.run(
        ["scp", "-q", str(local_path), f"{vm.alias}:{PROBE_DIR}/{script_name}"],
        check=True,
    )


# CONFIG_DATA_DIR is resolved per-VM via vm.home (see write_test_phrase),
# not a literal "~", since shlex.quote()-ing a ~-path breaks tilde expansion.
CONFIG_DATA_DIR_SUFFIX = ".config/autokey/data/Checklist"

PHRASE_TEMPLATE = """{{
    "modes": [{modes}],
    "usageCount": 0,
    "showInTrayMenu": false,
    "abbreviation": {{
        "abbreviations": [{abbr}],
        "backspace": true,
        "ignoreCase": false,
        "immediate": false,
        "triggerInside": false,
        "wordChars": "[\\\\w]"
    }},
    "hotkey": {{
        "modifiers": [{modifiers}],
        "hotKey": {hotkey}
    }},
    "filter": {{
        "regex": null,
        "isRecursive": false,
        "isInverted": false
    }},
    "description": "{description}",
    "prompt": false,
    "omitTrigger": false,
    "type": "phrase",
    "matchCase": false,
    "sendMode": {send_mode}
}}"""


def write_test_phrase(
    vm: VM,
    name: str,
    content: str,
    send_mode: Optional[str],
    abbreviation: Optional[str] = None,
    hotkey: Optional[tuple] = None,  # (["<left_ctrl>", "<left_alt>"], "z")
):
    """
    Write a throwaway phrase directly into a dedicated "Checklist" folder in
    the live config, bypassing the GUI. AutoKey's file watcher picks it up
    live (confirmed this session -- no restart needed), which is faster and
    more repeatable than driving the config dialogs for setup that isn't
    itself under test.
    """
    modes = []
    if abbreviation:
        modes.append("1")
    if hotkey:
        modes.append("3")
    abbr = f'"{abbreviation}"' if abbreviation else ""
    modifiers = ", ".join(f'"{m}"' for m in hotkey[0]) if hotkey else ""
    hotkey_key = f'"{hotkey[1]}"' if hotkey else "null"
    # SendMode.SELECTION serializes as JSON null (SendMode(None) is the enum
    # lookup used on load -- see model/phrase.py), not the string "None"; every
    # other mode is a plain string value like "kb" or "<ctrl>+v".
    send_mode_json = "null" if send_mode is None else f'"{send_mode}"'

    body = PHRASE_TEMPLATE.format(
        modes=", ".join(modes),
        abbr=abbr,
        modifiers=modifiers,
        hotkey=hotkey_key,
        description=name,
        send_mode=send_mode_json,
    )
    # The Checklist folder itself must already exist and be stably watched
    # (see ensure_checklist_dir) -- creating it and writing into it in the same
    # breath races AutoKey's inotify watch installation for the new directory,
    # and the file-creation events land before the watch exists, so they are
    # silently missed (confirmed: 0 "Checklist/<file>" log lines ever appeared
    # when the folder was recreated per-call).
    config_data_dir = f"{vm.home}/{CONFIG_DATA_DIR_SUFFIX}"
    json_path = shlex.quote(f"{config_data_dir}/{name}.json")
    txt_path = shlex.quote(f"{config_data_dir}/{name}.txt")
    # Write via a heredoc so we don't fight shell quoting on the JSON braces.
    vm.try_run(f"cat > {json_path} << 'CHECKLISTEOF'\n{body}\nCHECKLISTEOF")
    vm.try_run(f"cat > {txt_path} << 'CHECKLISTEOF'\n{content}\nCHECKLISTEOF")
    _created_phrase_names.append(name)
    time.sleep(1.5)  # let the file watcher pick it up


def ensure_checklist_dir(vm: VM):
    """
    Create the Checklist folder once, up front, and wait for AutoKey's file
    watcher to actually attach to it before any phrase files are written.
    Call this once per script run, before any write_test_phrase() calls.
    """
    config_data_dir = f"{vm.home}/{CONFIG_DATA_DIR_SUFFIX}"
    vm.try_run(f"mkdir -p {shlex.quote(config_data_dir)}")
    time.sleep(2.0)


def remove_test_phrase(vm: VM, name: str):
    config_data_dir = f"{vm.home}/{CONFIG_DATA_DIR_SUFFIX}"
    json_path = shlex.quote(f"{config_data_dir}/{name}.json")
    txt_path = shlex.quote(f"{config_data_dir}/{name}.txt")
    vm.try_run(f"rm -f {json_path} {txt_path}")
    time.sleep(0.5)


_created_phrase_names: list[str] = []


def cleanup_test_phrases(vm: VM):
    """
    Remove only the individual phrase files this run created, and leave the
    Checklist folder itself in place.

    Deliberately NOT `rm -rf` the whole folder: AutoKey's configmanager has a
    real bug (found while building this harness) where __remove_folder()
    never calls monitor.remove_watch(), so FileMonitor.has_watch(path) keeps
    returning True for the old path string after a folder is deleted. The
    next time a folder is recreated at that same path, __sort_and_watch_folder
    sees has_watch() == True and skips add_watch() entirely, so the recreated
    folder never gets a working inotify watch again for the life of the
    process. Keeping the folder alive across runs avoids ever triggering that
    path. Worth its own bug report separately.
    """
    for name in list(_created_phrase_names):
        remove_test_phrase(vm, name)
    _created_phrase_names.clear()


def ensure_probe_running(vm: VM, repo_path: Optional[str] = None) -> str:
    """
    Start paste_probe_gtk.py if it's not already running, return its
    window id. Uses the GTK probe rather than the Tk-based paste_probe.py:
    confirmed live that GTK's PRIMARY-selection clipboard implementation
    (used by AutoKey's GTK front end) does not correctly answer a Tk
    widget's selection request -- GTK-to-xclip and GTK-to-GTK both work,
    GTK-to-Tk does not, even though the click event itself demonstrably
    reaches the Tk widget. That is a Tk-vs-GTK3 toolkit incompatibility
    below AutoKey entirely, not something a real user hits (real paste
    targets are overwhelmingly GTK, Qt, or other modern toolkits, not
    Tk), so testing against Tk was never representative for item 5.
    """
    existing = vm.find_window("Paste Probe")
    if existing:
        return existing
    if repo_path is None:
        repo_path = REPO_PATH
    # GDK_BACKEND=x11: on a real Wayland session, GTK3 defaults to a native
    # Wayland surface unless told otherwise -- unlike Tk, which is always
    # X11/XWayland-backed. A native surface is completely invisible to
    # xdotool's X11-based window search, so find_window() would never find
    # this probe at all without forcing it through XWayland. Confirmed
    # live (u24, GNOME Wayland): the process ran fine, just with a window
    # xdotool could never see.
    vm.launch(
        f"env GDK_BACKEND=x11 python3 {repo_path}/tests/manual/paste_probe_gtk.py /tmp/paste-probe.out",
        logfile="/tmp/paste_probe_launch.log",
    )
    for _ in range(10):
        wid = vm.find_window("Paste Probe")
        if wid:
            # The window existing in an xdotool search does not mean it is
            # fully mapped and ready to actually receive focus/input yet,
            # especially over XWayland. Confirmed live on k26: the very
            # first interaction against a freshly-launched probe (only ever
            # seen as the first item in a combined run, never in isolation)
            # occasionally lost the first several characters even though
            # AutoKey's own log showed every character being sent correctly
            # -- a receiving-side settle race, not a sending-side one.
            time.sleep(0.5)
            return wid
        time.sleep(0.5)
    raise RuntimeError("Paste Probe window never appeared")


def read_probe_output(vm: VM) -> str:
    result = vm.try_run("cat /tmp/paste-probe.out 2>/dev/null")
    return result.stdout


def clear_probe(vm: VM, window_id: str):
    vm.activate(window_id)
    vm.key("Escape")
    time.sleep(0.3)
    vm.try_run("rm -f /tmp/paste-probe.out")


# --------------------------------------------------------------------------
# Item 1: Phrase expansion via abbreviation
# --------------------------------------------------------------------------

@check("1", "Phrase expansion via abbreviation")
def check_abbreviation(vm: VM) -> CheckResult:
    write_test_phrase(
        vm, "Check1 Abbreviation", "abbreviation expansion worked",
        send_mode="kb", abbreviation="chkabbr1",
    )
    wid = ensure_probe_running(vm)
    clear_probe(vm, wid)
    vm.activate(wid)
    vm.type_text("chkabbr1 ")  # trailing space is the trigger character
    time.sleep(1.0)
    content = read_probe_output(vm)
    passed = "abbreviation expansion worked" in content
    shot = None if passed else vm.screenshot("check1_abbreviation")
    return CheckResult("1", "Phrase expansion via abbreviation", passed,
                        f"probe content: {content!r}", shot)


# --------------------------------------------------------------------------
# Item 2: Phrase/script trigger via global hotkey
# --------------------------------------------------------------------------

@check("2", "Phrase/script trigger via global hotkey")
def check_hotkey(vm: VM) -> CheckResult:
    write_test_phrase(
        vm, "Check2 Hotkey", "hotkey trigger worked",
        send_mode="kb", hotkey=(["<left_ctrl>", "<left_alt>", "<left_shift>"], "z"),
    )
    wid = ensure_probe_running(vm)
    clear_probe(vm, wid)
    vm.activate(wid)
    vm.key("ctrl+alt+shift+z")
    time.sleep(1.0)
    content = read_probe_output(vm)
    passed = "hotkey trigger worked" in content
    shot = None if passed else vm.screenshot("check2_hotkey")
    return CheckResult("2", "Phrase/script trigger via global hotkey", passed,
                        f"probe content: {content!r}", shot)


# --------------------------------------------------------------------------
# Item 3: Paste method - keyboard
# --------------------------------------------------------------------------

@check("3", "Paste method: keyboard")
def check_paste_keyboard(vm: VM) -> CheckResult:
    write_test_phrase(
        vm, "Check3 Keyboard", "keyboard paste method worked",
        send_mode="kb", hotkey=(["<left_ctrl>", "<left_alt>", "<left_shift>"], "k"),
    )
    wid = ensure_probe_running(vm)
    clear_probe(vm, wid)
    vm.activate(wid)
    vm.key("ctrl+alt+shift+k")
    time.sleep(1.0)
    content = read_probe_output(vm)
    passed = content.strip() == "keyboard paste method worked"
    shot = None if passed else vm.screenshot("check3_keyboard")
    return CheckResult("3", "Paste method: keyboard", passed,
                        f"probe content: {content!r}", shot)


# --------------------------------------------------------------------------
# Item 4: Paste method - clipboard (Ctrl+V), with restore check
# --------------------------------------------------------------------------

@check("4", "Paste method: clipboard (Ctrl+V), original clipboard restored")
def check_paste_clipboard(vm: VM) -> CheckResult:
    sentinel = "checklist-sentinel-4-do-not-touch"
    # xclip forks to stay alive as the X11 clipboard owner (X11 clipboard is
    # owner-push, not server-stored) -- but without nohup/disown, closing this
    # SSH channel sends SIGHUP to the whole remote process group, killing that
    # forked child before it can serve a single read. Confirmed directly: a
    # bare `... | xclip -selection clipboard` set was immediately unreadable
    # afterward, by AutoKey's own clipboard backup AND a plain `xclip -o`.
    vm.try_run(
        f"nohup bash -c 'echo -n {shlex.quote(sentinel)} | xclip -selection clipboard' "
        f"> /tmp/checklist_xclip.log 2>&1 < /dev/null & disown -a"
    )
    time.sleep(0.5)

    write_test_phrase(
        vm, "Check4 Clipboard", "clipboard paste method worked",
        send_mode=r"<ctrl>+v", hotkey=(["<left_ctrl>", "<left_alt>", "<left_shift>"], "c"),
    )
    wid = ensure_probe_running(vm)
    clear_probe(vm, wid)
    vm.activate(wid)
    vm.key("ctrl+alt+shift+c")
    time.sleep(1.2)
    content = read_probe_output(vm)
    pasted_ok = "clipboard paste method worked" in content

    time.sleep(0.5)  # give AutoKey time to restore the original clipboard
    restored = vm.try_run("xclip -selection clipboard -o 2>/dev/null").stdout
    restore_ok = restored == sentinel

    passed = pasted_ok and restore_ok
    detail = (
        f"pasted={pasted_ok} (probe: {content!r}), "
        f"clipboard_restored={restore_ok} (got: {restored!r}, want: {sentinel!r})"
    )
    shot = None if passed else vm.screenshot("check4_clipboard")
    return CheckResult("4", "Paste method: clipboard (Ctrl+V)", passed, detail, shot)


# --------------------------------------------------------------------------
# Item 5: Paste method - mouse selection (middle-click / PRIMARY)
# --------------------------------------------------------------------------

@check("5", "Paste method: mouse selection (middle-click)")
def check_paste_selection(vm: VM) -> CheckResult:
    """
    _send_string_selection() clicks the MIDDLE button at whatever the CURRENT
    mouse position is (not a specified window) -- see iomediator.py:462-469 --
    so the mouse must already be hovering over the target before the hotkey
    fires, unlike the other paste checks which just need the target focused.

    WON'T FIX, expected to fail against this probe: root-caused (2026-09-26,
    via raw X11 protocol tracing on acreetion/AcreetionOS/XLibre) to a real
    GTK3 bug, not an AutoKey bug -- GTK's clipboard-owner code silently
    serves zero bytes for the PRIMARY selection's text/plain;charset=utf-8
    target on X11, while STRING/UTF8_STRING work correctly for the identical
    content at the identical moment. Both Tk (the original paste_probe.py)
    and GTK's own TextView (paste_probe_gtk.py, used here) apparently prefer
    that MIME-type target first, so both fail identically -- confirmed this
    is not a Tk-vs-modern-toolkit issue. AutoKey's own mouse-click mechanism
    is verified correct (the real queue-race bug this investigation also
    found is fixed separately, see interface.py/uinput_interface.py's
    _send_mouse_click_now()). Full writeup, evidence, and user-support
    guidance in memory `project_gtk3_clipboard_text_plain_bug.md`. Left
    running (not skipped) so a future GTK/probe change that happens to
    dodge this target would be noticed as a real pass, not silently
    ignored.
    """
    write_test_phrase(
        vm, "Check5 Selection", "selection paste method worked",
        send_mode=None,  # SendMode.SELECTION's value is None -> JSON null
        hotkey=(["<left_ctrl>", "<left_alt>", "<left_shift>"], "s"),
    )
    wid = ensure_probe_running(vm)
    clear_probe(vm, wid)
    vm.activate(wid)
    # Move the mouse into the probe's text area (not just window-active) so
    # the synthetic middle-click AutoKey sends lands inside the widget.
    vm.move_mouse_into_window(wid, 300, 150)
    vm.key("ctrl+alt+shift+s")
    time.sleep(1.0)
    content = read_probe_output(vm)
    passed = "selection paste method worked" in content
    shot = None if passed else vm.screenshot("check5_selection")
    return CheckResult("5", "Paste method: mouse selection (middle-click)", passed,
                        f"probe content: {content!r}", shot)


# --------------------------------------------------------------------------
# Item 9: Enable/disable expansions toggle
# --------------------------------------------------------------------------

DBUS_CALL = (
    "gdbus call --session --dest org.autokey.Service --object-path /AppService "
    "--method org.autokey.Service.{method}"
)


@check("9", "Enable/disable expansions toggle")
def check_enable_disable_toggle(vm: VM) -> CheckResult:
    """
    Calls Service.pause_service()/unpause_service() over D-Bus directly --
    this is what the tray icon/notifier menu's Enable/Disable item itself
    invokes, but clicking the actual tray icon is not automated here (no
    stable window id/coordinates for a tray icon over SSH+xdotool). This
    verifies the pause/resume mechanism itself works, not the menu click.
    """
    write_test_phrase(
        vm, "Check9 Toggle", "toggle test fired",
        send_mode="kb", hotkey=(["<left_ctrl>", "<left_alt>", "<left_shift>"], "t"),
    )
    wid = ensure_probe_running(vm)

    vm.run(DBUS_CALL.format(method="pause_service"))
    time.sleep(0.5)
    clear_probe(vm, wid)
    vm.activate(wid)
    vm.key("ctrl+alt+shift+t")
    time.sleep(1.0)
    fired_while_paused = "toggle test fired" in read_probe_output(vm)

    vm.run(DBUS_CALL.format(method="unpause_service"))
    time.sleep(0.5)
    clear_probe(vm, wid)
    vm.activate(wid)
    vm.key("ctrl+alt+shift+t")
    time.sleep(1.0)
    fired_while_active = "toggle test fired" in read_probe_output(vm)

    passed = (not fired_while_paused) and fired_while_active
    detail = f"fired_while_paused={fired_while_paused} (want False), fired_while_active={fired_while_active} (want True)"
    shot = None if passed else vm.screenshot("check9_toggle")
    return CheckResult("9", "Enable/disable expansions toggle", passed, detail, shot)


# --------------------------------------------------------------------------
# Item 10: Config GUI sanity
# --------------------------------------------------------------------------

@check("10", "Config GUI sanity")
def check_config_gui_sanity(vm: VM) -> CheckResult:
    """
    Confirms the config window is present, responsive (accepts a real window
    focus/activate round trip), and that nothing has logged a traceback.
    Does not restart AutoKey itself -- that would invalidate every other
    check's assumption of a stable, already-verified-clean process, so this
    only checks the window that should already be open.

    On KDE Wayland, autokey-qt's config window runs as a native Wayland
    surface, invisible to xdotool's X11-based window search entirely (only
    XWayland-backed clients like the Tk-based Paste Probe show up there).
    Full window discovery there would need KWin's own JS-scripting D-Bus
    interface (the same mechanism AutoKey's own kde_interface.py uses for
    its window API) -- real engineering effort for a single sanity check,
    so instead this falls back to calling AutoKey's own D-Bus
    show_configure() method as a liveness probe: if the whole process
    (including its Qt main loop) is alive and responsive enough to accept
    a GUI-triggering D-Bus call without hanging or erroring, combined with
    no recent traceback in the log, that is a reasonable proxy for "the
    config window is present and responsive" given the toolchain
    available here.
    """
    wid = vm.find_window_exact("AutoKey")
    if wid is not None:
        vm.activate(wid)
        title = vm.run(f"xdotool getwindowname {wid}").strip()
        log_tail = vm.try_run(f"tail -200 {shlex.quote(LOG_PATH)}").stdout
        has_traceback = "Traceback (most recent call last)" in log_tail
        passed = title == "AutoKey" and not has_traceback
        detail = f"window_title={title!r}, recent_traceback_in_log={has_traceback}"
        shot = None if passed else vm.screenshot("check10_config_gui")
        return CheckResult("10", "Config GUI sanity", passed, detail, shot)

    if vm.wayland:
        result = vm.try_run(DBUS_CALL.format(method="show_configure"))
        dbus_ok = result.returncode == 0
        log_tail = vm.try_run(f"tail -200 {shlex.quote(LOG_PATH)}").stdout
        has_traceback = "Traceback (most recent call last)" in log_tail
        passed = dbus_ok and not has_traceback
        detail = (
            f"no window titled 'AutoKey' found via xdotool (expected on KDE "
            f"Wayland's native Qt windows); fell back to D-Bus show_configure() "
            f"liveness probe: dbus_ok={dbus_ok}, recent_traceback_in_log={has_traceback}"
        )
        shot = None if passed else vm.screenshot("check10_config_gui")
        return CheckResult("10", "Config GUI sanity", passed, detail, shot)

    return CheckResult("10", "Config GUI sanity", False,
                        "no window titled 'AutoKey' found (is autokey-gtk running with -c?)")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vm", required=False, help="VM alias, e.g. m22")
    parser.add_argument("--items", default=None,
                         help="Comma-separated item numbers to run, default all implemented")
    parser.add_argument("--list", action="store_true", help="List implemented items and exit")
    parser.add_argument("--repo-path", default="~/autokey",
                         help="Path to the AutoKey git checkout on the VM (for paste_probe.py)")
    parser.add_argument("--keep-phrases", action="store_true",
                         help="Don't delete the Checklist test phrases afterward")
    parser.add_argument("--log-path", default="/tmp/autokey_integration.log",
                         help="Path to AutoKey's own log file on the VM (for item 10's traceback check)")
    args = parser.parse_args()
    global LOG_PATH, REPO_PATH
    LOG_PATH = args.log_path
    REPO_PATH = args.repo_path

    if args.list:
        for item, fn in sorted(CHECKS.items(), key=lambda kv: kv[0]):
            print(f"{item}: {fn._name}")
        return 0

    if not args.vm:
        parser.error("--vm is required unless --list is given")

    items = sorted(CHECKS.keys(), key=lambda i: int(i)) if args.items is None else args.items.split(",")

    vm = VM(args.vm)
    print(f"[{vm.alias}] session env: {vm.env}")
    ensure_checklist_dir(vm)

    results: list[CheckResult] = []
    try:
        for item in items:
            fn = CHECKS.get(item)
            if fn is None:
                print(f"[{vm.alias}] item {item}: no automated check implemented, skipping")
                continue
            print(f"[{vm.alias}] running item {item}: {fn._name} ...")
            try:
                result = fn(vm)
            except Exception as e:
                result = CheckResult(item, fn._name, False, f"exception: {e!r}")
            results.append(result)
            if result.passed:
                status = "PASS"
            elif item in WONT_FIX_ITEMS:
                status = "FAIL (known won't-fix, see docstring)"
            else:
                status = "FAIL"
            print(f"[{vm.alias}] item {item} [{status}]: {result.detail}")
            if result.screenshot:
                print(f"[{vm.alias}]   screenshot: {result.screenshot}")
    finally:
        if not args.keep_phrases:
            cleanup_test_phrases(vm)
        vm.kill("paste_probe_gtk.py")

    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    report_path = SCRATCH_DIR / f"{vm.alias}_report_{int(time.time())}.json"
    with open(report_path, "w") as f:
        json.dump([dataclasses.asdict(r) for r in results], f, indent=2)
    print(f"[{vm.alias}] report written to {report_path}")

    failed = [r for r in results if not r.passed]
    unexpected_failed = [r for r in failed if r.item not in WONT_FIX_ITEMS]
    passed_count = len(results) - len(failed)
    print(f"[{vm.alias}] {passed_count}/{len(results)} passed"
          + (f" ({len(failed) - len(unexpected_failed)} known won't-fix)" if len(failed) > len(unexpected_failed) else ""))
    return 1 if unexpected_failed else 0


if __name__ == "__main__":
    sys.exit(main())
