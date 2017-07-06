# Introduction

This page contains solutions to problems frequently experienced by users of AutoKey.

## Feature X is not working correctly for me. How do I post useful debugging information on the list?

Start by opening a terminal. Then start AutoKey with the debug logging turned on:

`autokey-gtk -l`

Next, perform whatever action is causing the problem. Lastly, capture the output and include it with your posting.

## How do I know which interface to use? (Settings->Advanced Settings->Device Interface)

When you start AutoKey for the first time, it attempts to choose the best possible option for you. For most people, this should work fine. As the dialog states, only change the setting if AutoKey is not responding to hotkeys and abbreviations. In that case, you can simply try the various options and see which works best for you. Note that some of the interfaces don't work at all, depending on your distribution. To summarise:

- X Record: Will work in any distribution using X.org server prior to version 1.6. E.g. Ubuntu Jaunty upgrades the server to v1.6, and as a result XRecord will not work. The problem is fixed in Lucid (10.04).
- X EvDev: Should work in most cases, except if you are using 'exotic' hardware such as Bluetooth keyboards (or any keyboard device that does not use the EvDev X driver).
- AT-SPI: Only works when the active window is a GTK-based application (including Firefox 3). Also requires certain configuration items in your Gnome environment to be enabled (see below).

## The AT-SPI device interface option is greyed out/disabled.

To enable this interface, you must have the AT-SPI packages installed and be running a GNOME-based distribution. The AT-SPI interface is a last-ditch option in case the other two options don't work. It only works in certain applications (to be exact, GTK-based applications that have the ATK bridge compiled in).

To enable it, run the following:

`sudo apt-get install python-pyatspi`

You must then enable accessible technologies via the Gnome Accessibility Settings applet. Another way to get this interface up and running is to install an application called Accersizer. The first time you start Accersizer, it will enable the correct settings for you.

## When I start AutoKey I get the message "Unable to connect to EvDev daemon"

Ensure that the AutoKey EvDev daemon is running by running the following command:

`sudo invoke-rc.d autokey restart`

## I disabled the notification icon, and I don't know the hotkey for displaying the configuration window.

Simply start AutoKey again while it is already running, and this will cause the configuration window to be shown.

## How can one send an 'mdash' with keyboard.send_keys() in a script? 
I tried:
`mdash = "\u2014"`
`keyboard.send_keys(mdash)`
and nothing gets printed. However, when I activate `Autokey-qt --verbose` in the terminal, it indicates the — mdashin the eterminal.

