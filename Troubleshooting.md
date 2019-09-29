# Introduction

This page contains solutions to problems frequently experienced by users of AutoKey.

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

## I disabled the notification icon, and I don't know the hotkey for displaying the configuration window.

Simply start AutoKey again while it is already running, and this will cause the configuration window to be shown.

## How can one send em dash or another Unicode special character in new, python3 version of AutoKey? 

One of the many options is to use the sample script bellow and modify `TextToType="—"` to your desired special character (or sequence), for example `TextToType="≠≠≠"` ([source](https://github.com/autokey/autokey/issues/29#issuecomment-437426992)).
```
OldClipboard=clipboard.get_clipboard()
TextToType="┐(´-｀)┌"
clipboard.fill_clipboard(TextToType)
keyboard.send_keys("<ctrl>+v")
time.sleep(0.1)
clipboard.fill_clipboard(OldClipboard)
```