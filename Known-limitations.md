There are situations that AutoKey (currently) can not handle. This page should give an overview and list known limitations.

Some of these limitations can be worked around, some may be fixed in future versions and some limitations are hard limitations that can not be fixed.

# Secondary keyboard layouts configured in KDE do not work with AutoKey
If you have multiple keyboard layouts configured using the KDE keyboard layout manager and use a non-default layout, i.e. not the first in the list, the keyboard output AutoKey generates is mangled by KDE, causing AutoKey to output nonsense.

Depending on how different the layouts are, this can result in some slight mistakes for similar layouts or complete nonsense for quite different layouts (e.g. `querty` vs `Dvorak` or `neo2`).

AutoKey outputs the keys suitable for the currently active layout, but the KDE keyboard monitor thinks it has to apply the same layout conversion as to your physical keyboard key presses. This causes a double key translation, and in turn messes up the AutoKey output.

Workaround: Don’t use the secondary layouts and switch to the first in the list, before using AutoKey features.

# Interacting with pure X toolkit applications does not work
Reason:
The X server interface used by AutoKey marks the generated events (key presses, releases, etc.) as `synthetic`, i.e. programmatically generated. Most programs written using the pure X11 toolkit ignore such events. Thus AutoKey does not work with them. Most of those applications have a name that starts with `X`.

Known not working applications:

- `xterm` (Can be configured to accept the events: `<Ctrl>+<Left mouse button>` in the window to open the main menu, in there activate `Allow SendEvents`)
- `xsane`

Workaround: Use AutoKey scripts to call `xdotool`. `xdotool` can be used to generate »non-synthetic« events that should work with those applications.

# Abbreviations
AutoKey uses a Queue to find abbreviations in the last pressed keys.
## Mouse clicks
Because clicking with the mouse may switch between input fields or windows, the input queue is emptied whenever a mouse button is pressed.
* Useful: You can use this as a feature to abort Phrase expansion or script execution by clicking a mouse button while typing an abbreviation.
* Drawback/Limitation: You cannot use the mouse to click, while typing an abbreviation. Frequent mouse clicks, maybe done by an “auto-fire” feature built into your mouse, will interfere with the abbreviation trigger mechanism.

## Input queue length hard-coded to 150 characters
AutoKey only ever stores up to the last 150 typed keys. This imposes two limitations:

* You can not define “abbreviations” longer than 150 characters.
* You can not go back indefinitely in the typed key history by pressing the `<backspace>` key. If your abbreviation rotated out of the input buffer, expansion won’t happen any more, even if your text cursor reaches the unexpanded, previously typed abbreviation.

# Phrases
## Limitations of the Undo functionality
You can not undo phrase expansion that contain any kind of special keys, i.e. keys in AutoKey’s special key syntax `<key_name>` or `<codeXX>` where `XX` is a X11 key symbol number.
This includes all keys listed [here](https://github.com/autokey/autokey/blob/master/lib/autokey/iomediator/key.py). For example:  `<code160>`, `<left>`, `<shift>+<left>`, `<Alt>+<F4>`, `<shift>+<insert>`, etc.

AutoKey versions ≥ 0.95.5:\
AutoKey refuses to undo phrases containing special keys, because it cannot reliably determine how those keys alter the system state.

Older versions (≤ 0.95.4, everything older than [f3f3ed05c18388eb08032b43a2e70539e0ced93c](https://github.com/autokey/autokey/commit/f3f3ed05c18388eb08032b43a2e70539e0ced93c)):\
Older versions will try to undo such Phrases and most probably fail. This most probably results in the erasure of more characters than desired.

### Performing a perfect undo is sometimes not possible:

- If you use a Phrase containing tabulator characters (`	`) to move between input fields in a GUI form, hitting the `<backspace>` key does not go back. Instead it may delete the content of the currently active field.
- If your text editor replaces tabulator characters with spaces, AutoKey can not undo the expansion, because it can not determine the expanded text length. Many IDEs do this, e.g. PyCharm, the AutoKey script editor itself, Kate (if configured to indent with spaces), etc.

## Phrase expansion

- You can only place one `<cursor>` macro into a phrase.
- If you use a `<script>` macro, your script may not alter the system state, otherwise the expansion _will_ fail. See the `Run script` section [here](https://github.com/autokey/autokey/wiki/Dynamic-Phrases,-Using-Macros-as-placeholders-in-Phrases#run-script) for additional details.

# Scripts