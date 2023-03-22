## Contents 

* [Getting help with AutoKey](#getting-help-with-autokey)
  * [AutoKey error message](#autokey-error-message)
  * [AutoKey traceback](#autokey-traceback)
  * [Python traceback](#python-traceback)
* [Troubleshooting FAQ](#troubleshooting-faq)

# Getting help with AutoKey

When AutoKey does something unfortunate or unexpected, you can sometimes figure out what went wrong by examining the error message that AutoKey created. If that doesn't solve the problem, you can get additional help in one or more of these ways:

* By posting a message in [AutoKey's Google Groups forum](https://groups.google.com/forum/?hl=en#!forum/autokey-users).
* By posting a message in [AutoKey's Gitter community platform](https://app.gitter.im/#/room/#autokey_autokey:gitter.im).
* By creating a new issue or participating in an existing issue in [AutoKey's issue tracker](https://github.com/autokey/autokey/issues).

You'll want to specify the operating system you're using, the AutoKey version you're using, exactly what you did, a description of what did or didn't happen, a description of what you expected to happen, and a copy of your script or phrase. In some cases, it can also be helpful for you to provide the [AutoKey error message](#autokey-error-message) or an [AutoKey traceback](#autokey-traceback) or a [Python traceback](#python-traceback) by pasting the contents of any of those into various places in our AutoKey community in a variety of ways:

* as is into [a Google Groups message](https://groups.google.com/forum/?hl=en#!forum/autokey-users)
* as is into [the text-box that asks for the output of the AutoKey command in a new AutoKey issue](https://github.com/autokey/autokey/issues)
* with a row of triple backticks (\```) above and below it in [a comment text-box beneath an existing AutoKey issue](https://github.com/autokey/autokey/issues) or [a Gitter message](https://app.gitter.im/#/room/#autokey_autokey:gitter.im)

## AutoKey error message
This can be helpful when something is wrong with your AutoKey script.

1. When there's something wrong with your AutoKey script, AutoKey will display an error pop-up.
2. View the error by right-clicking the AutoKey icon in the system tray and choosing **View script error**. The error message will sometimes contain one or more Python tracebacks.
3. Examine the information in the AutoKey error message. It may show you what went wrong.
4. If it doesn't make sense or if you have questions, select all of the error message and copy it.

## AutoKey traceback
This can be helpful when AutoKey runs without crashing, a trigger was used, and the expected event either didn't occur or something other than the expected result occurred. This information can be obtained by starting the `autokey-gtk` or `autokey-qt` front-end from a terminal window with the `--verbose` option:

1. Close AutoKey if it's currently running.
2. Open a terminal window.
3. Make sure the AutoKey process has ended by typing this command into the terminal window and pressing the **Enter** key:
   ```python
   pkill autokey
   ```
4. Start AutoKey GTK or QT in verbose mode by typing one of these commands and pressing the **Enter** key:
   ```
   autokey-gtk --verbose
   ```
   or:
   ```
   autokey-qt --verbose
   ```
5. Using AutoKey, repeat the action that caused the problem. Note that this will produce a log in the terminal window of what AutoKey is doing.
6. Close AutoKey.
7. Examine the output inside of the terminal window. It may show you what went wrong.
8. If it doesn't make sense or if you have questions, select all of the output and copy it.

## Python traceback
This can be helpful when something is wrong with your AutoKey script, causing an exception to be shown in an AutoKey error message in the form of a [Python traceback](https://www.coursera.org/tutorials/python-traceback):

  1. When there's something wrong with your AutoKey script, AutoKey will display an error pop-up.
  2. View the error by right-clicking the AutoKey icon in the system tray and choosing **View script error**. If it contains one or more Python tracebacks, they will look something like this example of a Python traceback in which the nonexistent **foo** function was called:

     ```python
     Traceback (most recent call last):
       File "/home/john_doe/Documents/example.py", line 28, in <module>
         foo()
     NameError: name 'foo' is not defined
     ```
  3. Examine the information in the traceback(s). It/they may show you what went wrong.
  4. If it doesn't make sense or if you have questions, select all of the error message and copy it.

# Troubleshooting FAQ

This section contains frequently asked questions about solutions to problems experienced by AutoKey users.

## I have remapped my Caps-lock key to something else (like `[Ctrl]`). My defined abbreviations don’t work or the output case is inverted after pressing the Caps-lock key. How do I fix this?

Due to the way AutoKey monitors the keyboard, it still sees the remapped Caps-lock key as "Caps-lock", even though other applications see the remapped key. So AutoKey can not automatically detect this situation. Support for remapped Caps-lock keys was added in version 0.95.10.

So to fix this, make sure you run at least version 0.95.10. Then go to the AutoKey applications settings and check the option "Disable handling of the Capslock key", then restart AutoKey (Use `File` → `Quit`, then start AutoKey again). 

## AutoKey (Qt) + KDE desktop: Automatically starting AutoKey shows the GUI during login, even if `Show main window when starting` is disabled

Explanation:\
On KDE Plasma, AutoKey gets started twice during the login process. Once by the enabled Autostart setting in the Settings dialogue, and another time by the session restoration functionality built into the KDE desktop. When AutoKey is running, another starting instance causes the first to open it’s GUI. That’s why it shows up, even if disabled in the settings.

Solution:\
Either disable the Autostart option in the AutoKey settings and let the KDE session restoration mechanism restart AutoKey.\
Or exclude AutoKey from said mechanism and keep the Autostart setting in the AutoKey settings active.\
The exclusion feature is here: Open the KDE5 systemsettings (`systemsettings5`). In the settings application, navigate to `Workspace`→`Startup and Shutdown`→`Desktop Session`→`On Login`. Add `autokey-qt` to the applications listed in the text field labeled `Applications to be excluded from sessions:`.

## Feature X is not working correctly for me. How do I post useful debugging information on the list?

Start by opening a terminal. Then start AutoKey with the debug logging turned on:

Start the GTK interface using `autokey-gtk -l`
Or start the Qt interface using `autokey-qt -l` 

Next, perform whatever action is causing the problem. Lastly, capture the output and include it with your posting.

## How do I know which interface to use? (Settings->Advanced Settings->Device Interface)

When you start AutoKey for the first time, it attempts to choose the best possible option for you. For most people, this should work fine. As the dialog states, only change the setting if AutoKey is not responding to hotkeys and abbreviations. In that case, you can simply try the various options and see which works best for you. Note that some of the interfaces don't work at all, depending on your distribution. To summarise:

- X Record: Will work in any distribution using X.org server prior to version 1.6. E.g. Ubuntu Jaunty upgrades the server to v1.6, and as a result XRecord will not work. The problem is fixed in Lucid (10.04).
- AT-SPI: Only works when the active window is a GTK-based application (including Firefox 3). Also requires certain configuration items in your Gnome environment to be enabled (see below).

## The AT-SPI device interface option is greyed out/disabled.

To enable this (assistive tech) interface, you must have the AT-SPI packages installed and be running a GNOME-based distribution. The AT-SPI interface is a last-ditch option in case the other two options don't work. It only works in certain applications (to be exact, GTK-based applications that have the ATK bridge compiled in).

To enable it, run the following:

`sudo apt-get install python-pyatspi`

You must then enable accessible technologies via the Gnome Accessibility Settings applet. Another way to get this interface up and running is to install an application called Accersizer. The first time you start Accersizer, it will enable the correct settings for you.

## I disabled the notification icon, and I don't know the hotkey for displaying the configuration window. How do I bring it up?

The default key binding to show the main window is `<Super>+k`. (On most keyboards,`<Super>` is the Windows logo key.)

As an alternative, or if you disabled / changed the hotkey, simply start AutoKey again while it is already running. This will cause the configuration window to be shown.

## How can one send em dash or another Unicode special character in new, python3 version of AutoKey? 

One of the many options is to use the sample script below and modify `TextToType="—"` to your desired special character (or sequence), for example `TextToType="≠≠≠"` ([source](https://github.com/autokey/autokey/issues/29#issuecomment-437426992)).
```
OldClipboard=clipboard.get_clipboard()
TextToType="┐(´-｀)┌"
clipboard.fill_clipboard(TextToType)
keyboard.send_keys("<ctrl>+v")
time.sleep(0.1)
clipboard.fill_clipboard(OldClipboard)
```
