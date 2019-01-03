There are situations that AutoKey (currently) can not handle. This page should give an overview and list known limitations.

Some of these limitations can be worked around, some may be fixed in future versions and some limitations are hard limitations that can not be fixed.

# Interacting with pure X toolkit applications does not work
Reason:
The X server interface used by AutoKey marks the generated events (key presses, releases, etc.) as `synthetic`, i.e. programmatically generated. Most programs written using the pure X11 toolkit ignore such events. Thus AutoKey does not work with them. Most of those applications have a name that starts with `X`.

Known not working applications:

- `xterm` (Can be configured to accept the events: `<Ctrl>+<Left mouse button>` in the window to open the main menu, in there activate `Allow SendEvents`)
- `xsane`

Workaround: Use AutoKey scripts to call `xdotool`. `xdotool` can be used to generate »non-synthetic« events that should work with those applications.

# Phrases
## Undo functionality
Performing a perfect undo is sometimes not possible:

- You can not reliably undo phrase expansion that contain cursor movement keys or other function keys, for example `<left>`, `<shift>+<left>`, `<Alt>+<F4>`, `<shift>+<insert>`, etc.
If you try to undo such phrases, it will result in weird behaviour, like removing too many or too few characters.
- If you use a Phrase containing tabulator characters (`	`) to move between input fields in a GUI form, hitting the `<backspace>` key does not go back. Instead it may delete the content of the currently active field.
- If your text editor replaces tabulator characters with spaces, AutoKey can not undo the expansion, because it can not determine the expanded text length. Many IDEs do this, e.g. PyCharm, the AutoKey script editor itself, Kate (if configured to indent with spaces), etc.

## Phrase expansion

- You can only place one `<cursor>` macro into a phrase.
- If you use a `<script>` macro, your script may not alter the system state, otherwise the expansion _will_ fail.

# Scripts