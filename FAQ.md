### What are the dependency packages for AutoKey?
See here for an overview, including the dependencies: https://github.com/autokey/autokey/wiki/Installing

### What is the license of AutoKey?
AutoKey is published under GNU GPL v3 license.

### I start autokey, but nothing happens??
When starting AutoKey without any command line arguments, it starts in the background without opening any windows.
The same thing happens, if the menu entry does not launch AutoKey using the `--configure` command line switch.
AutoKey actually starts and is usable.
Use the `--configure` or `-c` command line switch to start AutoKey with the main window opened at start or use the tray icon or configured hotkey to show the main window.
#### X protocol errors on launch! 
```X protocol error:
<class 'Xlib.error.BadAccess'>: code = 10, resource_id = 260, sequence_number = 17, major_opcode = 33, minor_opcode = 0
```
Most likely Autokey has indeed started, and these are just benign messages from python-xlib. Verify that autokey is running with `ps aux | grep autokey`
### Does AutoKey work with scripts which were written with the popular AutoHotKey Windows application?
No. AutoKey's built-in Python scripting is arguably much more powerful than the AHK language and makes it possible to do many of the things that AutoHotKey? scripts can do on Windows, in addition to some things AHK doesn't support.

### Is AutoKey available on Microsoft Windows?
No. There are similar alternatives on Windows like [PhraseExpress](http://www.phraseexpress.com/) and [AutoHotKey](http://www.autohotkey.com/)

### Can I temporarily suspend/resume AutoKey?
To toggle !Autokey from suspend/resume, use the hotkey which you have specified in Settings -> Advanced Settings -> Special Hotkeys->Use a hotkey to toggle expansions. Alternatively this can be controlled from the system tray Autokey popup menu.

### How can I show the main AutoKey window?
You can click on the tray icon to show the main window. If you disabled the tray icon:
You can use the global hotkey, as defined in the settings to show the window. (It defaults to `<super>+k`).
If you also disabled the global hotkey, see the next question.

#### Can I show the main window programmatically?

If it has to be a command/executable you want to call to show the main window, you can just try to start another instance (`autokey-qt` or `autokey-gtk` does not matter).
The new instance checks if another one is running. If so, it pings the running instance to show its main window (using a dbus call) and then exits.
That is the canonical way.

If you wish, you can emit that dbus call directly, e.g. by using `dbus-send`. The interface name is `org.autokey.Service` and the method name is `show_configure`.

In short, this command uses the dbus directly to open the main window of a running AutoKey instance:
``` shell
dbus-send --session --type=method_call --dest="org.autokey.Service" "/AppService" "org.autokey.Service.show_configure"
```

### What are the trigger characters?
The default trigger characters are dependent on your locale. They are any characters that are not normally considered part of a word. For English locales, these are characters like Enter (Return), Tab, Space and punctuation, among others.

### Can I use Caps Lock in Autokey?
1.  Disable caps lock:

`xmodmap -e 'clear Lock'`

2. Use xcape to assign a key sequence e.g. Left super+f

`xcape -e '#66=Super_L|f'`

3. Attach autokey script to the assigned key sequence.

4. Reassign capslock to (say) pressing both shift keys.

`setxkbmap -option "caps:none"`
`setxkbmap -option "shift:both_capslock"`

Caps lock key is really out of autokey's scope, you just need to use other utilities to get the desired effect.

### Where is my configuration information stored? Can I move those to other machines?
By default AutoKey stores your settings under ~/.config/autokey. You can of course create AutoKey folders anywhere you wish as well, using "Create New Top-Level Folder". Folders containing phrases and scripts can be freely copied between machines using your favourite file manager, or synchronised using a program such as Dropbox. Please remember to also copy the hidden files as each script and phrase has one.
