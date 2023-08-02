## Table of Contents
  * [Can I temporarily suspend/resume AutoKey?](#can-i-temporarily-suspendresume-autokey)
  * [Can I use AutoKey on Wayland?](#can-i-use-autokey-on-wayland)
  * [Can I use Caps Lock in Autokey?](#can-i-use-caps-lock-in-autokey)
  * [Does AutoKey work with scripts that were written with the popular Windows AutoHotKey application?](#does-autokey-work-with-scripts-that-were-written-with-the-popular-windows-autohotkey-application)
  * [How can I show the main AutoKey window?](#how-can-i-show-the-main-autokey-window)
    * [How can I show the main AutoKey window programmatically?](#how-can-i-show-the-main-autokey-window-programmatically)
  * [Is AutoKey available on Microsoft Windows?](#is-autokey-available-on-microsoft-windows)
  * [What are the dependency packages for AutoKey?](#what-are-the-dependency-packages-for-autokey)
  * [What are the trigger characters?](#what-are-the-trigger-characters)
  * [What if I would like to suggest a new feature for AutoKey?](#what-if-i-would-like-to-suggest-a-new-feature-for-autokey)
  * [What is the license of AutoKey?](#what-is-the-license-of-autokey)
  * [Where is my configuration information stored and can I copy it to other machines?](#where-is-my-configuration-information-stored-and-can-i-copy-it-to-other-machines)
  * [Why does nothing happen when I start AutoKey?](#why-does-nothing-happen-when-i-start-autokey)
    * [Why am I getting X protocol errors on launch?](#why-am-i-getting-x-protocol-errors-on-launch)
  * [Why is the text messed up when I use a phrase with LibreOffice Writer?](#why-is-the-text-messed-up-when-i-use-a-phrase-with-libreoffice-writer)

***

### Can I temporarily suspend/resume AutoKey?
Yes. To toggle AutoKey from suspend/resume, use the hotkey that you have specified in ```Settings -> Advanced Settings -> Special Hotkeys->Use a hotkey to toggle expansions```. Alternatively this can be controlled from the AutoKey system tray pop-up menu.

### Can I use AutoKey on Wayland?
This is an **X11** application and, as such, will not function on distributions that default to using **Wayland** instead of **Xorg**.

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


### What if I would like to suggest a new feature for AutoKey?
If a feature you'd like isn't available by default in AutoKey, you can file an enhancement request for it in the bug tracker. Some have already been submitted by others. To do so, you can visit the [Issues](https://github.com/autokey/autokey/issues) page, use the search box to search for the issue by keyword, and contribute your comments to an existing enhancement request if you found one or add one if
you didn't, making sure to use the "Enhancement" label so the developers will know that that's what it is.

### What is the license of AutoKey?
AutoKey is published under the [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.

### Where is my configuration information stored and can I copy it to other machines?
By default AutoKey stores your settings in the ```~/.config/autokey``` folder. You can create AutoKey folders anywhere you wish, as well, by using "Create New Top-Level Folder". Folders containing phrases and scripts can be freely copied between machines using your favorite file manager or synchronized using a program such as Dropbox. (For verions prior to 0.96.0) Please remember to also copy the hidden files, as each script and phrase has one.

### Why does nothing happen when I start AutoKey?
AutoKey actually starts and is usable. When starting AutoKey without any command line arguments, it starts in the background without opening any windows. It also puts an icon with an **A** on it in your tray.

Use the `--configure` or the `-c` command-line option to start AutoKey with the main window opened at start.

As an alternative, you can use the tray icon or the configured hotkey to show the main window.

#### Why am I getting X protocol errors on launch?
```X protocol error:
<class 'Xlib.error.BadAccess'>: code = 10, resource_id = 260, sequence_number = 17, major_opcode = 33, minor_opcode = 0
```
Most likely AutoKey has indeed started and these are just benign messages from python-xlib. Verify that AutoKey is running with `ps aux | grep autokey`

There is some indication that the above error(s) might be caused by AutoKey attempting to setup your hotkey triggers using triggers that are already in use by your desktop or other active software.

### Why is the text messed up when I use a phrase with LibreOffice Writer?

When using a text editor, pressing your hotkey or typing your abbreviation (shortcut) followed by a space or other trigger character that you've defined types your phrase. When doing the same thing with LibreOffice Writer, AutoKey types a mixture of your abbreviation and your phrase.

Basically, the keyed shortcut is not removed and the replacement word is not completed. This is an issue with the output arriving at the destination program too soon. It seems to be caused by the `keyboard` module (which we didn't write).

The first thing to try is always to select the **Paste using Ctrl+V** option for your phrases. That fixes most problems and avoids a number of others. If that doesn't work, recode one of your phrases as a script using the [type_slow](https://github.com/autokey/autokey/wiki/Advanced-Scripts#function-to-type-text-slowly) function from our wiki. Try the simple version first (the first one). If you're still having problems, then file an [issue](https://github.com/autokey/autokey/issues) here or reach out to our community on [Gitter](https://gitter.im/autokey/autokey) with the details of what you tried and we'll try to find another solution.
