=========
Changelog
=========
.. contents::


Version 0.95.9 <2019-12-07>
===========================

Bug fixes
---------

- Prevent data losses when deleting or moving directories from within AutoKey. AutoKey will only delete data it knows
  and keep unknown user data. So adding $HOME and then removing it again will not purge everything below it.
  Affected were deleting directories and moving them via drag & drop. Fixes issues #171, #332

Version 0.95.8 <2019-11-07>
===========================

Bug fixes
---------

- Qt GUI: Fix issue with Python 3.7.4 and PyQt 5.11-5.13.0 that prevented AutoKey from starting on certain
  distributions shipping this configuration, notably Kubuntu 19.10. Fixes issues #313, #301
- Qt GUI: Fix crash when saving the currently edited item, after deselecting it in the tree view. Fixes issue #285
- Qt GUI: Disable Main window -> Tools -> Insert Macro when not editing a Phrase. Fixes issue #276
- Qt GUI: Add a warning that explains possible data loss when creating top level directories at used specified
  locations. See issue #171
- GTK GUI: Fix application hang when setting a custom value for "Trigger on" in the Abbreviation settings dialogue.
  Fixes issue #315


Version 0.95.7 <2019-04-29>
===========================

Bug fixes
---------

- GTK GUI: Fixed system tray icon context menu entry :code:`View script error`, which was non-functional,
  if the main window is closed. The entry now opens the main window first as a workaround,
  because a proper fix will require a major code overhaul. Fixes #222
- Qt GUI: Fixed the truncated GPLv3 license text shown in the About AutoKey dialogue.
  The dialogue window now shows the full license text. Fixes #258
- Hardened the logic to read application window titles. AutoKey now works,
  if applications do not set the :code:`_NET_WM_VISIBLE_NAME` property of their windows. Fixes #257
- Fixed Phrase expansion using the Keyboard method, which was broken if AutoKey was started for the first time.
  Fixes #274


Other fixes
-----------
- Improved the debug logging output: Removed unnecessary output, clarified wordings, etc. See #230
- Qt GUI: Display the current Python version number in the About dialogue.


Version 0.95.6 <2019-02-09>
===========================

Bug fixes
---------

- Fix the combination of phrase settings :code:`Match phrase case to typed abbreviation` and
  :code:`Trigger immediately` to cause Scripts and Phrases to trigger on each and every key press.
  Fixes issue #254 introduced in 0.95.5.

Version 0.95.5 <2019-02-07>
===========================

Bug fixes
---------

- Fix window filter detection always returning Title: :code:`FocusProxy`, Class: `Focus-Proxy-Window.FocusProxy` on
  Java AWT applications. It now detects the proper window title and WM_CLASS attribute for Java AWT applications.
  Fixes issue #113
- GTK GUI: Fix the window filter detection dialogue. On clicking OK, it hung the whole application.
  Now the dialogue window works as intended. Fixes issue #229
- Fix abbreviation case folding (ignore case option) with abbreviations defined as UPPER CASE in the abbreviation
  dialogue. Options :code:`Ignore case` and :code:`Match case` now work with upper case abbreviations. Fixes issue #197
- Prevent the keyboard from staying grabbed by AutoKey if exceptions are thrown while AutoKey performs a
  clipboard pasting action. Fixes issues #72, #225
- Prevent writing :code:`None` to the clipboard. This prevents autokey-gtk from deadlocking,
  caused by an unreleased mutex. Fixes issue #226
- Restrict Phrase Undo functionality to phrases without special keys, because phrases containing special keys cannot
  be reliably undone. Fixes issue #196
- Clarified autosave option wording in the settings window. The option now explicitly states what it does.
  Fixes issue #194
- Force AutoKey to exit, if the X server connection closes, most probably at logout or session end. Fixes issue #198

Qt tray icon fixes and improvements
+++++++++++++++++++++++++++++++++++

- Added »View script error« entry to the Tray icon context menu, like in the GTK GUI. Part of issue #158
- Tray icon turns red, when scripts raise an error, like in the GTK GUI. Part of issue #158
- If changing the tray icon theme in the settings (light or dark), instantly apply the new theme,
  without requiring an application restart. Part of issue #158
- The tray icon now works, after if it is disabled in the settings and then enabled again. Fixes issue #223

Other fixes
-----------

- Enable :code:`setup.py` to be directly called from the system shell. Fixes issue #218
- Cleaned up some legacy leftovers in the autokey repository

Version 0.95.4 <2018-10-14>
===========================

Bug fixes
---------

- Fix grabbed hotkeys being incorrectly received by other applications.
- Fixed crashes when processing `<code>` literals in strings.
  It is now possible to place `<code>` and `<code/>` literals in Phrases.
  Additionally, such literals can be typed in scripts using the keyboard.send_keys function.
- Increased the reliability of the window filter detection dialog in autokey-qt. The dialog allows sampling windows
  to aid writing window filters. Due to timing issues in certain cases, sometimes the window title of the previously
  active window was returned.

Version 0.95.3 <2018-08-21>
===========================

Features
--------

- Phrase expansion can now always be undone using the backspace key, if the feature is enabled in the settings.
  Previously it was only be possible if the phrase was triggered by an abbreviation.
  Now it also works when using hotkeys or selecting phrases from menus.
  This also prevents crashes in `certain cases`_.
- Qt GUI: Add support for automatically starting `autokey-qt` during login. It can be configured in the settings
  dialogue. The configuration option allows to choose which GUI is automatically started, if both `autokey-qt` and
  `autokey-gtk` are installed simultaneously, and whether the main window should be shown automatically on launch.
- Qt GUI: Added the notification icon theme selection to the settings dialogue. The added section in the general
  settings allow to choose between the light and dark theme, like in the `autokey-gtk` settings dialogue. Changing
  this setting currently requires an application restart to take effect.

Bug fixes
---------
- Scripting API: The Python `__file__` global variable is now properly set for AutoKey scripts.
  It contains the full path to the Python script file currently running. Previously, it contained the full path to
  the `service.py` file of the currently running AutoKey instance.
- Crash fix: Skip import of the AT-SPI interface, if importing of `pyatspi` fails with a SyntaxError. This may happen
  with certain versions of `pyatspi` on Python 3.7. For details see `#173`_
- Fix serializing the store during saving, if user stores recursive data structures. It now handles/skips lists that
  contain themselves or other circular referenced data structures.
- GTK GUI: Fix autostart handling: Create the `$XDG_CONFIG_HOME/autostart` (`~/.config/autostart`) directory, if it is
  not already present. Fixes `#149`_
- Qt GUI: Create the user data directories before initializing the logger system. This prevents crashes when autokey-qt
  is used for the first time or when the user wiped all previous data. Fixes `#170`_
- Qt GUI: Fix saving the "Always prompt before running this script" checkbox content when editing scripts. This option
  now works as intended again.

Packaging
---------
- Stop shipping the `autokey.png` icon file inside a `scalable` icon theme directory. Moved to the appropriate raster
  image directory.
- Corrected broken dependency package name in setup.py. The library is called `python-xlib` and not `python3-xlib` on
  PyPI.


.. _certain cases: https://github.com/autokey/autokey/issues/164
.. _`#173`: https://github.com/autokey/autokey/issues/173
.. _`#149`: https://github.com/autokey/autokey/issues/149
.. _`#170`: https://github.com/autokey/autokey/issues/170


Version 0.95.2 <2018-07-16>
===========================

- Fix broken imports in autokey-shell script
- Skip non-json-serializable data in script storage (both script local and global) during saving. This allows putting
  non-serializable items (like function objects) into the store without crashing autokey during saving.
- Qt GUI: Fix minor bug when creating new items. Created items are now properly selected for renaming directly after
  creation.
- Minor code simplifications. Removed unnecessary functions that were obsoleted during prior changes.

Version 0.95.1 <2018-06-30>
===========================
This is a small bug fixing release.

- Fix a long standing bug that errors occurring during phrase parsing or script execution can lock up the user keyboard.
  Make sure to always release the keyboard after grabbing it. See `#72`_, launchpad_1551054_
- Qt GUI: Fix saving the content of the log view to a file using the context menu entry.
- Some small, internal code quality improvements.

.. _`#72`: https://github.com/autokey/autokey/issues/72
.. _launchpad_1551054: https://bugs.launchpad.net/ubuntu/+source/autokey/+bug/1551054

Version 0.95.0 <2018-06-28>
===========================

Rewritten the Qt GUI, ported to PyQt5
-------------------------------------

Resurrected, re-written and cleaned up the `autokey-qt` Qt GUI. `autokey-qt` is now a pure `PyQt5` application, only
dependent on currently supported libraries.

Added improvements
++++++++++++++++++
- The main window now keeps its complete state when closed and re-opened (excluding complete application restarts). This includes the currently selected item(s) in the tree view on the left of the main window, selected text and cursor position in the editor on the right if currently editing a script or phrase.
- The entries in the popup menu, that is shown when a hotkey assigned to a folder is pressed, now show icons based on their type (folder, phrase or script). This also works when items are configured to be shown in the system tray icon context menu.
- The *A* autokey application icons are now always displayed correctly, both in the main window and the system tray icon.
- Various menu actions now have system dependent keyboard shortcuts, that should adjust to the expected default of the user’s current platform/desktop environment.
- Added icons and descriptive tooltip texts to various buttons.
- The `enable monitoring` checkboxes (both in the `Settings` menu and the tray icon context menu) now properly react to pressing the global hotkey for this action and thus stay in sync. (Even if the hotkey is used while the menu is shown.)

Regressions
+++++++++++
- Customizing the main window toolbar entries and keyboard shortcuts to trigger various UI actions is no longer possible. This feature was provided by the KDE4 libraries and is currently dropped.
- The previous, KDE4-based About dialogue is replaced with a very minimalistic one.
- The settings dialogue heavily used the KDE4 functionalities. During the port to Qt5, the dialogue lost some visual style, but all core functionality is kept.

Runtime dependencies
++++++++++++++++++++
- Removed dependencies on deprecated and unmaintained PyQt4 and PyKDE4 libraries.
- Removed dependency on `dbus.mainloop.qt`, instead use the DBus support built into Qt5.
- Now depend on PyQt5, the Qt5 SVG module and the Qt5 QScintilla2 module.

Build-time dependencies
+++++++++++++++++++++++
Optionally depend on `pyrcc5` command line tool to compile Qt resources into a Python module.

Qt UI files are no longer compiled using `pykdeuic4`, Removed the old compiler wrapper script in commit 6eeeb92f_.

.. _6eeeb92f: https://github.com/autokey/autokey/commit/6eeeb92f14c694979c1367d51350c1e6509329b1

Known bugs
++++++++++
The system tray icon is shown, but non-functional, after enabling it in the settings dialogue. AutoKey Qt has to be restarted for the tray icon to start working. This should have no impact on the normal daily use.

Changed features
++++++++++++++++
The `hide tray icon` entry in the tray icon context menu now hides the icon for the current session only. The entry does not permanently disable the tray icon any more without any confirmation. Now, the only way to permanently disable the tray icon is through using the appropriate setting in the settings dialogue.

Fixed the broken `Clipboard` and `Mouse selection` phrase paste modes
---------------------------------------------------------------------
- Pasting using both `Clipboard` and `Mouse selection` works in both the Qt and GTK GUI. See `#101`_
- Fixed restoring the clipboard after a paste is performed. Both GUIs now restore the previous clipboard content, after a phrase is pasted.

.. _`#101`: https://github.com/autokey/autokey/issues/101

Scripting API Changes
---------------------

Additions
+++++++++

- Added a colour picker dialogue to the GTK dialog class, because the used `zenity` now supports it.
- The picked colour is returned as three integers using the ColourData NamedTuple, providing both index based access and attribute  access, using the channel names (`r`, `g`, `b`). Additionally, ColourData provides some conversion methods.

Breaking changes
++++++++++++++++
- See Pull request `#148`_. The `dialog` classes for user input in scripts now return typed NamedTuple tuples instead of plain tuples. This change is safe as long as users do not perform needlessly restrictive type checks in their scripts (e.g. `if type(returned_data) == type(tuple()): ...`). User scripts doing so will break.
- The KDialog based colour picker now also returns a ColourData instance instead of a HTML style hex string, thus making this portable between both GTK and Qt GUIs. AutoKey users previously using the old KDE GUI and using the colour picker dialogue have to port their scripts. A simple fix is using the `html_code` property of the returned ColourData instance.

.. _`#148`: https://github.com/autokey/autokey/pull/148

Fixes
+++++
- Re-introduce the newline trimming for system.exec_command() function. During the porting to Python 3, the newline trimming was removed, causing users various issues with unexpected newline characters at end of output. Now properly remove the _last_ newline at end of command output. (See issues `#75`_, `#92`_, `#145`_)
- Applied various code style improvements to the scripting module.

.. _`#75`: https://github.com/autokey/autokey/issues/75
.. _`#92`: https://github.com/autokey/autokey/issues/92
.. _`#145`: https://github.com/autokey/autokey/issues/145

Other fixes and improvements
----------------------------
- Fix the KDialog based colour picker provided in the scripting API. Newer versions of KDialog require an additional parameter, which is added now.
- Fixed crashes related to mouse pasting when using the GTK GUI.
- Both `autokey-gtk` and `autokey-qt` are now automatically generated setuptools entry-points.
- `autokey-gtk` can now be launched directly from the autokey source tree.

From the shell, `cd` into the `lib` directory, then use

.. code-block:: sh

    <path_to_autokey_source_dir>/lib$ python3 -m autokey.gtkui [-l] [-c]
    # Or alternatively, to launch autokey-qt use:
    <path_to_autokey_source_dir>/lib$ python3 -m autokey.qtui [-l] [-c]


- Various internal code style improvements at various locations, like added type hints, PEP8 style fixes, etc.

Version 0.94.0 <2018-05-12>
===========================
- Various README updates
- Ported autokey-run from the legacy optparse module to the new Python 3 argparse module
- Use $XDG_RUNTIME_DIR and $XDG_DATA_HOME directories for lock and log file
- Added support for function keys F13 to F35
- Refactored the iomediator modules into a package. Applied various code cleanups and fixes.

Version 0.93.10 <2017-02-17>
============================
- The scripting global storage now returns None if the requested key is not present.
- Improved the error messages in autokey-run. It is now clear that autokey has to run in the background for autokey-run to work.
- Added a LICENSE file containing the GPL v3 license terms.

Version 0.93.9 <2017-01-11>
===========================
Fixed a regression with setup.py install_requires keyword argument.
Updated the GitHub issue template.

Version 0.93.8 <2017-01-09>
===========================
- Readme updates
- Depend on Ubuntu appindicator
- Leverage libappindicator completely, fix "View script error"

Version 0.93.7 <2016-12-21>
===========================
This release contains various bug/crash fixes

- Renamed repository from autokey-py3 to autokey
- Moved the AutoKey source code out of src folder one level up.
- Removed donate button
- autokey-gtk script is now a setuptools generated entry point
- Require GTK 3.0 to fix autokey-gtk startup
- Updated various web links around the codebase
- New feature: Return the result of wait events in the iomediator module.


Version 0.93.6 <2016-08-13>
===========================
- Ensure Compatibility with official python-xlib
- Fixed several GTK related warnings
- GTK GUI:  Add feature to trigger popupmenu items with letters, rather than numbers.
- Add an AUR link

Version 0.93.4 <2015-02-17>
===========================
Bugfix: Prevent clipboard related crashes with GTK3.

Version 0.93.3 <2015-02-20>
===========================
Bugfix for defining abbreviations by `@kuhanalog`_

.. _@kuhanalog: https://github.com/kuhanalog

Version 0.93.2 <2014-08-09>
===========================
Read user scripts with UTF-8 encoding.

Version 0.93.1 <2014-03-02>
===========================
Internal changes: Changed the data structure of the input stack.


Version 0.93.0 <2014-02-27 Thu>
===============================

Added functions “acknowledge_gnome_notification” and “move_to_pat”, more details `here`_.

.. _here: https://github.com/autokey/autokey/blob/master/new_features.rst

Version 0.92.0 <2014-02-21 Fri>
===============================
Added an interactive shell launcher, “autokey-shell”. “autokey-shell” allows you to run some AutoKey functions interactively. Read `this`_ for more details.


Version 0.91.0 <2014-02-14 Fri>
===============================
Added a new function “click_on_pat” for use in user scripts. See `this`_ for more details.

.. _this: https://github.com/autokey/autokey/blob/master/new_features.rst


First release <2014-01-31 Fri>
==============================
This describes some of the changes to the original AutoKey source code.

Python 3 related changes
------------------------
Python 3 is less tolerant of circular imports so some files were split into several files. Those pieces of the original have their file names prefixed with the original's.

Bug fixes
+++++++++
Eliminate possible deadlock.
Changed

.. code-block:: python

        p = subprocess.Popen([…], stdout=subprocess.PIPE)
        retCode = p.wait()
        output = p.stdout.read()[:-1] # Drop trailing newline

to

.. code:: python

        p = subprocess.Popen([…], stdout=subprocess.PIPE)
        output = p.communicate()[0].decode()[:-1] # Drop trailing newline
        retCode = p.returncode

The former may cause a deadlock, for more information, see `Python docs`_. This pattern appears several times in the source codes.

.. _Python docs: http://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait

For a “gi.repository.Notify.Notification” object, test if method “attach_to_status_icon” exists before calling. After this fix, errors in user scripts will trigger a notification.

Respect XDG standard. Details `here`__.

__ https://code.google.com/p/autokey/issues/detail?id=266

Corrected a typo in manpage of autokey-run.

For the GTK GUI, after script error is viewed, tray icon is reverted back to original.

Other changes
+++++++++++++
In setup.py, the “/usr/” prefix to the directory names in the data_files argument were removed to allow for non-root install.

Removed the “WINDOWID” environment variable so that zenity is not tied to the window from which it was launched.

Modified the launcher and other files to allow for editable installs (“pip install -e”).

Added an “about” dialog for the Python 3 port.

Changed hyperlink for bug reports.
