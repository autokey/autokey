Manual Verification
====================

Automated tests (see `Testing`_ in CONTRIBUTORS.rst) mock out the display
server, input devices, and desktop-specific IPC (D-Bus/KWin scripting), so
they can't catch bugs that only show up when AutoKey is actually driving a
real X11/Wayland session. This checklist is for verifying PRs that change
AutoKey's runtime behavior (input handling, clipboard, window detection,
UI notifiers), per the verification policy in CONTRIBUTORS.rst.

When to use this
-----------------
Run this checklist when a PR touches: keyboard/mouse input handling,
clipboard operations, window detection or manipulation, hotkey/abbreviation
triggering, or desktop-integration code (notifiers, tray icons, KWin/GNOME
extensions). Purely cosmetic changes don't need it.

How to compare
---------------
Where practical, check out ``master``, ``develop``, and the PR branch as
three separate installs (a plain ``pip install -e .`` in a venv is often
*not* enough -- some issues (e.g. desktop-launcher hooks) only appear in a
full package install). Reproduce the reported behavior on the base branch
first, then confirm the PR branch fixes or doesn't regress it.

Environments
-------------
Test on whichever of these the PR's changes actually touch:

- **X11** (any traditional X11 desktop)
- **GNOME / Wayland**
- **KDE Plasma / Wayland**

Core checklist
---------------
For each applicable environment:

1. **Phrase expansion via abbreviation** -- type a configured abbreviation, confirm it expands.
2. **Phrase/script trigger via global hotkey** -- confirm the hotkey fires the correct phrase/script.
3. **Paste method: keyboard** -- send a phrase via simulated keystrokes; confirm correct text in the target app.
4. **Paste method: clipboard (Ctrl+V)** -- confirm the phrase actually lands on the system clipboard and pastes; confirm the original clipboard contents are restored afterward.
5. **Paste method: mouse selection (middle-click)** -- confirm the phrase is pasted via PRIMARY selection.
6. **Record a key combination -- keyboard-triggered** -- open the dialog via keyboard, confirm the recorded key is correct.
7. **Record a key combination -- mouse-triggered** -- open the dialog by clicking a button, confirm the click doesn't get misrecorded as the key.
8. **Window detection (crosshair click-to-select)** -- confirm it correctly identifies both X11 and native-Wayland target windows, where applicable.
9. **Enable/disable expansions toggle** -- via tray icon/notifier menu, confirm expansions actually stop/resume.
10. **Config GUI sanity** -- open the relevant GTK or Qt config window, confirm no crash and settings persist.

Add or adjust steps as needed for what the specific PR changes -- this
list is a baseline, not exhaustive.

Contributing new scenarios
----------------------------
This checklist is a starting point, not a complete list. If you find a
bug that this checklist wouldn't have caught, or you know of an
interaction path worth covering, please contribute a PR adding it here.

.. _Testing: CONTRIBUTORS.rst#testing
