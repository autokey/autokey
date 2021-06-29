## Table of Contents
  * [Can I temporarily suspend/resume AutoKey?](#can-i-temporarily-suspendresume-autokey)
  * [Can I use Caps Lock in Autokey?](#can-i-use-caps-lock-in-autokey)
  * [Does AutoKey work with scripts that were written with the popular Windows AutoHotKey application?](#does-autokey-work-with-scripts-that-were-written-with-the-popular-windows-autohotkey-application)
  * [How can I show the main AutoKey window?](#how-can-i-show-the-main-autokey-window)
    * [How can I show the main AutoKey window programmatically?](#how-can-i-show-the-main-autokey-window-programmatically)
  * [Is AutoKey available on Microsoft Windows?](#is-autokey-available-on-microsoft-windows)
  * [What are the dependency packages for AutoKey?](#what-are-the-dependency-packages-for-autokey)
  * [What are the trigger characters?](#what-are-the-trigger-characters)
  * [What is the license of AutoKey?](#what-is-the-license-of-autokey)
  * [Where is my configuration information stored and can I copy it to other machines?](#where-is-my-configuration-information-stored-can-i-move-it-to-other-machines)
  * [Why does nothing happen when I start AutoKey?](#why-does-nothing-happen-when-i-start-autokey)
    * [Why am I getting X protocol errors on launch?](#why-am-i-getting-x-protocol-errors-on-launch)

***

### Can I temporarily suspend/resume AutoKey?
Yes. To toggle AutoKey from suspend/resume, use the hotkey that you have specified in ```Settings -> Advanced Settings -> Special Hotkeys->Use a hotkey to toggle expansions```. Alternatively this can be controlled from the AutoKey system tray pop-up menu.

### Can I use Caps Lock in Autokey?
1.  Disable caps lock:

`xmodmap -e 'clear Lock'`

2. Use xcape to assign a key sequence e.g. Left super+f

`xcape -e '#66=Super_L|f'`

3. Attach autokey script to the assigned key sequence.

4. Reassign capslock to (say) pressing both shift keys.

`setxkbmap -option "caps:none"`
`setxkbmap -option "shift:both_capslock"`

Caps lock key is really out of AutoKey's scope, so you will need to use other utilities to get the desired effect.

### Does AutoKey work with scripts that were written with the popular Windows AutoHotKey application?
No. AutoKey's built-in Python scripting is arguably much more powerful than the AutoHotKey language and makes it possible to do many of the things that AutoHotKey scripts can do in Windows in addition to some things AutoHotKey doesn't support.

### How can I show the main AutoKey window?
You can click on the tray icon to show the main window. If you disabled the tray icon:
You can use the global hotkey, as defined in the settings, to show the window (it defaults to `<super>+k`).
If you also disabled the global hotkey, see the next question.

#### How can I show the main AutoKey window programmatically?
If it has to be a command/executable you want to call to show the main window, you can just try to start another instance (with either `autokey-qt` or `autokey-gtk`).
The new instance checks if another instance is already running. If so, it pings the running instance to show its main window (using a dbus call) and then exits.
That is the canonical way.

If you wish, you can emit that dbus call directly by, for example, using the `dbus-send` command in a terminal window. The interface name is `org.autokey.Service` and the method name is `show_configure`.

In short, this command uses the dbus directly to open the main window of a running AutoKey instance:
``` shell
dbus-send --session --type=method_call --dest="org.autokey.Service" "/AppService" "org.autokey.Service.show_configure"
```

### Is AutoKey available on Microsoft Windows?
No. There are similar alternatives on Windows, like [PhraseExpress](http://www.phraseexpress.com/) and [AutoHotKey](http://www.autohotkey.com/). For an alternative that both uses Python and is free on Github, there's [Pywinauto](https://github.com/pywinauto/pywinauto).

### What are the dependency packages for AutoKey?
An overview of the dependencies can be found in the [Dependencies](https://github.com/autokey/autokey/wiki/Installing#Dependencies) section of the [Installing](https://github.com/autokey/autokey/wiki/Installing) page.

### What are the trigger characters?
The default trigger characters are dependent on your locale. They are any characters that are not normally considered part of a word. For English locales, these are characters like Enter (Return), Tab, Space, and punctuation keys, among others.

### What is the license of AutoKey?
AutoKey is published under the [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.

### Where is my configuration information stored and can I copy it to other machines?
By default AutoKey stores your settings in the ```~/.config/autokey``` folder. You can create AutoKey folders anywhere you wish, as well, by using "Create New Top-Level Folder". Folders containing phrases and scripts can be freely copied between machines using your favorite file manager or synchronized using a program such as Dropbox. Please remember to also copy the hidden files, as each script and phrase has one.

### Why does nothing happen when I start AutoKey?
AutoKey actually starts and is usable. When starting AutoKey without any command line arguments, it starts in the background without opening any windows. It also puts an icon with an **A** on it in your tray.

Use the `--configure` or the `-c` command-line option to start AutoKey with the main window opened at start.

As an alternative, you can use the tray icon or the configured hotkey to show the main window.

#### Why am I getting X protocol errors on launch?
```X protocol error:
<class 'Xlib.error.BadAccess'>: code = 10, resource_id = 260, sequence_number = 17, major_opcode = 33, minor_opcode = 0
```
Most likely AutoKey has indeed started and these are just benign messages from python-xlib. Verify that AutoKey is running with `ps aux | grep autokey`
