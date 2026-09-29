# VM-driven checklist automation

`checklist.py` automates most of `MANUAL_TESTING.rst`'s core checklist
against a live virtual machine, instead of running it by hand. See
`../../VM_TESTING.md` for how to set up a VM this script can drive.

Unlike the probes in `tests/manual/`, this script runs on your host, not
on the VM -- it connects out over SSH and drives the VM's real desktop
session with `xdotool` (X11) or `ydotool` (Wayland), then checks
AutoKey's actual behavior against real evidence: its own debug log, or
the output files written by `paste_probe.py`/`paste_probe_gtk.py`.

## Requirements

On the host:

- `ssh`/`scp`, with a passwordless SSH alias already configured for the
  VM (see `VM_TESTING.md`).
- `VBoxManage`, if you want failure screenshots (optional -- the script
  degrades gracefully without it, e.g. for a non-VirtualBox machine).

On the VM:

- `xdotool` (X11 and Wayland window discovery/activation).
- `ydotool` + `ydotoold`, on Wayland sessions only (real input
  injection -- `xdotool`'s XTEST events never reach XWayland clients).
- AutoKey itself, already running with a real desktop session.

## Usage

```
python3 checklist.py --list
python3 checklist.py --vm m22
python3 checklist.py --vm k26 --items 1,3,4
python3 checklist.py --vm u24 --repo-path ~/autokey --keep-phrases
```

Each run writes a JSON report and, on any failure, a screenshot under
`checklist-results/` (created next to this script).

`--items` restricts the run to specific checklist item numbers.
`--keep-phrases` skips cleanup of the throwaway test phrases the script
writes into a dedicated `Checklist` config folder on the VM, useful for
inspecting them after a failure. `--repo-path` points at the AutoKey
checkout on the VM (default `~/autokey`), used to locate
`tests/manual/paste_probe_gtk.py` there.

## What isn't automated

Checklist items 6-8 (recording a key combination via keyboard or mouse,
and window detection by crosshair click-to-select) are not automated and
aren't planned to be. They require driving GTK dialog widgets (tree-view
navigation, popup dialogs) with no accessibility API available to query
real widget coordinates, and blind coordinate/keyboard navigation proved
too unreliable across runs in practice. Run those three by hand,
following `MANUAL_TESTING.rst`.

## Adding a VM

Add an entry to the `VMS` dict at the top of `checklist.py`:

```python
"myvm": {"vbox_name": "myvm", "session_proc_pattern": "gnome-shell", "wayland": True},
```

- `vbox_name`: the VirtualBox VM name, for `VBoxManage screenshotpng` on
  failure. Set to `None` for a non-VirtualBox machine (screenshots are
  then skipped).
- `session_proc_pattern`: a process name pattern (`pgrep -f`) matching a
  real desktop-session process, used to read `DISPLAY`/`XAUTHORITY`/
  `DBUS_SESSION_BUS_ADDRESS`/`XDG_RUNTIME_DIR` from its environment --
  SSH sessions don't inherit these.
- `wayland`: `True` to use `ydotool` for input injection, `False` for
  `xdotool`/XTEST on a real X11 session.
