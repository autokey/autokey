# Testing AutoKey on Real Desktops with Virtual Machines

## Purpose

AutoKey's automated test suite (`pytest`) mocks the display server, the
input devices, and desktop-specific IPC (D-Bus, KWin scripting). This
keeps the suite fast and portable, but it cannot catch bugs that only
appear when AutoKey drives a *real* desktop session: a hotkey that never
reaches a real X11 grab, a clipboard paste that a real GTK or Qt window
handles differently than a mock, or a window-detection call that behaves
differently under Wayland than under X11.

To catch these bugs, we test AutoKey inside virtual machines that each
run one real desktop environment. This article explains how to build
that VM fleet, and how to run both the automated and the manual checks
against it.

We use three virtual machines, chosen to cover AutoKey's three supported
display environments:

| VM alias | Distribution | Desktop | Session type |
|---|---|---|---|
| m22 | Linux Mint 22 | Cinnamon | X11 |
| u24 | Ubuntu 24.04 | GNOME | Wayland |
| k26 | Kubuntu 26.04 | KDE Plasma | Wayland |

m22 is the only X11 machine in the fleet. Keep it, because some of
AutoKey's scripting API (image-matching functions such as `visgrep` and
`click_on_pat`) only works on a real X11 root window and cannot be
tested meaningfully under Wayland.

## Creating VMs

Each VM starts as a plain VirtualBox install and is brought to a known,
reusable state. Do these steps once per VM, then take a snapshot so you
can revert to a clean base before testing a fresh install again.

1. **Install the OS.** Use the standard installer for the distribution
   and desktop listed in the table above.
2. **Update packages.**
   ```
   sudo apt update
   sudo apt install -y openssh-server
   ```
3. **Set up SSH port forwarding.** In VirtualBox's network settings for
   the VM, add a port-forwarding rule:
   `127.0.0.1:<host-port> -> 10.0.2.15:22`. Pick a different
   `<host-port>` for each VM: 2222 for m22, 2223 for u24, 2224 for k26.
4. **Add the VM to your SSH config** (`~/.ssh/config` on the host), so
   you can reach it by a short alias:
   ```
   Host m22
       HostName 127.0.0.1
       Port <host-port>
       User autokey
       IdentityFile ~/.ssh/<your-key>
   ```
5. **Copy your SSH key to the guest and set permissions**, so later
   automation can log in without a password prompt:
   ```
   scp ~/.ssh/<your-key>.pub m22:~/key.pub
   ssh m22 "mkdir -p ~/.ssh && cat ~/key.pub >> ~/.ssh/authorized_keys && \
       chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
   ```
6. **Test passwordless SSH:** `ssh m22 echo ok`. If this asks for a
   password, check step 5 before moving on.
7. **Set dark mode** in the guest OS's appearance settings. This is
   cosmetic, but it makes screenshots taken during automated checks
   easier to read and keeps them visually consistent across VMs.
8. **Add the `autokey` user to sudoers, without a password prompt:**
   ```
   echo "autokey ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/autokey
   sudo chmod 440 /etc/sudoers.d/autokey
   ```
   This is a narrow, test-VM-only convenience. Never set this up on a
   machine other than a disposable test VM.
9. **Install a terminal editor** for quick on-VM edits:
   `sudo apt install -y neovim`.
10. **Create a clock-resync script.** VM clocks drift while a VM is
    stopped, and a stale clock makes `apt-get update` fail with a
    "Release file is not valid yet" error. Save this as
    `~/timesync.sh` and `chmod 700` it:
    ```
    #!/usr/bin/env bash
    # Works for either time-sync service; run whichever is present.
    if systemctl is-enabled chronyd &>/dev/null; then
        sudo systemctl restart chronyd
    else
        sudo timedatectl set-ntp false
        sudo timedatectl set-ntp true
    fi
    ```
    Run it after starting a VM that has been stopped for a while, before
    any `apt` command.
11. **Upgrade the rest of the system:** `sudo apt dist-upgrade -y`.
12. **Turn off automatic updates** in the guest's software settings, so
    a scheduled update cannot change the environment in the middle of a
    test run.
13. **Reboot** the VM.
14. **Take a VirtualBox snapshot named `installed`.** This captures a
    clean base OS with nothing AutoKey-related installed yet, so you can
    revert to it whenever you need to repeat fresh-install testing
    (checking `apt-requirements.txt`, first-run behavior, and so on).

After the `installed` snapshot, clone the AutoKey repository and install
its dependencies on each VM:

```
git clone -b develop https://github.com/autokey/autokey.git
cd autokey
sudo apt install -y $(cat debian/build_requirements.txt)
sudo apt install -y $(cat apt-requirements.txt)
```

On GNOME (u24), also build and install the GNOME Shell extension, then
copy over AutoKey's icons:

```
make -C autokey-gnome-extension
gnome-extensions install autokey-gnome-extension/autokey-gnome-extension@autokey.zip
gnome-extensions enable autokey-gnome-extension@autokey
mkdir -p ~/.local/share/icons
cp -vr config/*.png config/*.svg config/Humanity config/ubuntu-mono-* ~/.local/share/icons/
sudo cp config/10-autokey.rules /etc/udev/rules.d/
sudo reboot
```

See `CONTRIBUTORS.rst` for the full dependency/build details (venv
setup, `pip-requirements.txt`). Take a second snapshot once AutoKey
itself runs cleanly, so day-to-day testing does not have to repeat the
dependency install every time.

## Running Automated Tests

Two different kinds of automation run against this fleet: the unit test
suite (no VM needed) and the live-VM integration checklist.

### Unit tests

The `pytest` suite runs on the host, against a Python environment that
has AutoKey's runtime dependencies installed (a bare checkout does not
have them):

```
source <path-to-conda>/etc/profile.d/conda.sh
conda activate autokey
cd autokey
PYTHONPATH=lib python -m pytest tests/ -q
```

To reproduce a GitHub Actions CI run locally instead of pushing and
waiting, use `bin/act` (present at the repository root):

```
bin/act pull_request -j pytest \
    -P ubuntu-latest=catthehacker/ubuntu:act-latest \
    --matrix python-version:3.12 \
    -W .github/workflows/python-test.yml
```

For a hung test, get a real Python thread stack trace with
`py-spy dump --pid <pid>` instead of guessing from timestamps.
Intermittent, race-condition bugs need volume to confirm: run the
suspect path 20 to 40 times and count how often it fails, since a
single clean run (or a single failure) proves little.

### Live-VM integration checklist

`tests/vm_checklist/checklist.py` drives one of the real VMs over SSH,
using `xdotool` (X11) or `ydotool` (Wayland) for keyboard and mouse
input, and checks AutoKey's actual behavior against evidence: its debug
log, or the output files written by the manual test probes described
below. It automates most of the core checklist from `MANUAL_TESTING.rst`
(phrase expansion, hotkey triggering, each paste method, the
enable/disable toggle, and config-window sanity).

```
python3 tests/vm_checklist/checklist.py --list
python3 tests/vm_checklist/checklist.py --vm m22
python3 tests/vm_checklist/checklist.py --vm k26 --items 1,3,4
```

A few items are deliberately **not** automated: recording a key
combination, and window-detection by crosshair click. Both require
driving GTK dialog widgets (tree views, popups) with no accessibility
API available to query real widget positions; blind coordinate-based
navigation proved unreliable across runs. Run those by hand, following
`MANUAL_TESTING.rst`.

The script writes a JSON report and, on any failure, a screenshot under
`tests/vm_checklist/checklist-results/`. See
`tests/vm_checklist/README.md` for the full option list and how to add
a new VM to its registry.

### Fresh-install .deb packaging check

Items 1-10 above assume AutoKey is already installed (from source/pip),
so they never exercise the actual `.deb` packaging
(`debian/build.sh`/`debian/rules`, or `autokey-common`'s `postinst`/
`prerm` scripts) -- a packaging-only bug like #1277 is invisible to
them. `checklist.py --fresh-install` tests that path instead: it
reverts a VM to its clean `installed` snapshot, clones and builds the
`.deb` packages, installs them, and removes them again.

```
python3 tests/vm_checklist/checklist.py --vm u24 --fresh-install
```

This is destructive to whatever is currently running on the VM (it
prompts for confirmation unless `--yes` is given), and does not revert
back afterward -- revert to a snapshot by hand before reusing that VM
for the items 1-10 checks above. See `tests/vm_checklist/README.md` for
details.

## Running Manual Tests

For anything the checklist script doesn't cover, or when you want to see
AutoKey behave with your own eyes, `tests/manual/` has four small
GUI-based tools:

- **`paste_probe.py`** — a Tk window that mirrors everything pasted into
  it to a file, so you can verify exactly what text AutoKey sent, across
  any paste method and any desktop session.
- **`paste_probe_gtk.py`** — the same idea, backed by a GTK `TextView`
  instead. Use this one specifically for mouse-selection (middle-click)
  paste testing: GTK's PRIMARY-selection clipboard implementation does
  not correctly answer a Tk widget's selection request, so `paste_probe.py`
  gives a false negative there even though the paste itself works.
- **`mouse_probe.py`** — four labeled click targets (left, right,
  double, drag) that log every recognized event with its coordinates,
  for verifying mouse automation.
- **`gopher_hunt.py`** — a moving target for AutoKey's image-matching
  scripting API (`visgrep` / `click_on_pat`). X11 only; this does not
  work under Wayland.

Run any of them directly on the VM's desktop, or over SSH with the
session environment forwarded:

```
python3 tests/manual/paste_probe.py [outfile]
python3 tests/manual/paste_probe_gtk.py [outfile]
python3 tests/manual/mouse_probe.py [outfile]
python3 tests/manual/gopher_hunt.py [gopher.png] [logfile]
```

Typical loop: focus the probe window, press Escape to clear it, trigger
the AutoKey behavior under test, then read the output file.

**Important: keep the target window on top.** All four tools work
against real screen coordinates or a full-screen capture, not a specific
window handle. If another window overlaps the target — including
AutoKey's own configuration window — a click can land on whatever is
actually on top, and `gopher_hunt.py` can miss a hit entirely because it
never sees the sprite behind the obstruction. Bring the target window to
the front immediately before every test run, not just once at the start
of a session.

## Common Issues

- **`apt-get update` fails with "Release file... is not valid yet."**
  The VM's clock has drifted while it was stopped. Run the
  `timesync.sh` script from step 10 of VM creation, then retry.
- **`graphicsmagick-imagemagick-compat` fails to install.** This package
  (listed in `apt-requirements.txt`, needed for `highlevel.py`'s
  `convert` call) does not exist on newer Ubuntu releases. Install plain
  `imagemagick` instead.
- **`wmctrl` crashes on KDE Plasma Wayland (k26).** Every invocation,
  even `wmctrl -l`, segfaults on Plasma 6.6.6. Use `xdotool` for window
  listing, activation, and focus instead — it works reliably on all
  three VMs.
- **`Super+H` does nothing on KDE.** That shortcut minimizes a window on
  GNOME and Cinnamon, but has no effect on KDE. To get a window out of
  the way on k26, close it (AutoKey keeps running in the background) or
  move it off-screen with `xdotool windowmove`.
- **A launched process has no `DISPLAY` or clipboard access over SSH.**
  An SSH session does not inherit the desktop session's environment
  variables. Read them from a real session process instead of guessing:
  ```
  pgrep -u autokey -f "gnome-shell\|plasmashell\|cinnamon"
  tr '\0' '\n' < /proc/<pid>/environ | grep -E "DISPLAY|XAUTHORITY|DBUS_SESSION_BUS_ADDRESS|XDG_"
  ```
  A missing `XDG_SESSION_DESKTOP` specifically causes AutoKey's own
  desktop-detection code to misidentify a supported desktop as
  unsupported, even when everything else is set correctly.
- **`xdotool key`/`type` has no effect under Wayland.** `xdotool`'s key
  and mouse events use the X11 `XTEST` protocol, which does not reach
  XWayland client windows at all — confirmed with zero events observed
  on the receiving end even though `xdotool` itself reports success.
  Use `ydotool` (which injects through the kernel `uinput` device, the
  same path AutoKey's own input backend uses) for anything that needs
  to actually reach AutoKey or a target application on u24 or k26.
  `xdotool` remains fine for window discovery and activation on both.
- **KDE Wayland blocks the first synthetic input with a permission
  dialog.** The first time anything injects input via `uinput` in a
  session, KWin shows a native "Remote Control" permission dialog that
  cannot itself be dismissed with more `uinput` input. Use `ydotool` to
  click through it once per session before running any other check.
- **A screensaver silently swallows synthetic keystrokes.** On m22 and
  u24, an idle-triggered screen lock mid-test absorbs every keystroke
  sent afterward with no error. Disable idle-lock before a test session,
  and take a screenshot (`VBoxManage controlvm <name> screenshotpng
  <path>`) whenever input seems to stop having any effect.

## Tips and Tricks

- **Take a screenshot without a GUI viewer.** From the host:
  `VBoxManage controlvm <vboxname> screenshotpng <path>`, then open the
  PNG. Useful any time you're not physically watching the VM's console.
- **Fully stop VMs between real test sessions**, rather than leaving
  them merely idle. A cold `VBoxManage startvm <name> --type headless`
  followed by polling SSH until it answers gives a more predictable
  starting state than a VM that has been suspended or left running for
  days.
- **Use a separate git worktree for the branch under test**, instead of
  changing a VM's own checkout. This avoids clobbering any
  work-in-progress already sitting in the VM's copy of the repository.
- **Space out independent synthetic-input calls by two to three
  seconds**, especially right after restarting the target process or
  while the VM is otherwise busy (mid-`apt-get`, for example). Two input
  events sent too close together can arrive interleaved and produce a
  key combination that never matches the intended hotkey — this is a
  real input-injection race, not an AutoKey bug.
- **Treat KDE's two `ydotool` builds as genuinely different tools.**
  Depending on how the package was built, `ydotool key` either takes
  raw keycodes (`<code>:<pressed>` pairs) or human-readable combos
  (`ctrl+alt+c`), and the two are not interchangeable. Check
  `ydotool key --help` on each VM once, and remember which flavor it
  uses.
- **Rebuild the whole fleet occasionally, deliberately.** A full,
  from-scratch rebuild (fresh install, re-snapshot as `installed`)
  clears out accumulated one-off state from previous test sessions and
  is worth doing periodically rather than only when something breaks.
- **When in doubt about mouse acceleration on Wayland**, check whether
  the pointer's acceleration profile is set to anything other than
  `flat` with `speed 0`. GNOME's default adaptive profile distorts
  synthetic mouse movement unpredictably, which is confusing to debug
  if you don't already know to look for it.
