=========
Changelog
=========

Version 0.96.0
============================

Bug fixes
---------

- Both Qt and GTK versions will reload hotkeys after a keymap change event.
- Fix locking issue.
- Expose Alt_GR as a hotkey modifier on GTK.
- (GTK) Fix GUI lock-up, if multiple script error notifications are posted in quick succession. The notifications
  are now rate-limited and won’t post more than one notification per second. Fixes issue #383.
- Fix issue with pip installation reporting a missing module.
- **Scripting API**
   - Fix API call `system.exec_command()` crashing if output capturing is active, but the executed command has
     empty output. Fixes issue #379.
- **Packaging**
   - Fix AutoKey PNG icon size. Now, the icon size is 96x96 pixels, fixing Lintian warnings on Debian. Fixes issue
     #369.

Documentation
-------------

- Change clipboard wording in the AutoKey documentation.
- Update formatting and wording in the AutoKey GTK and Qt clipboard API documentation.
- Remove one reference to **X** in the AutoKey GTK clipboard API documentation.
- Remove one reference to **mouse** from the AutoKey Qt clipboard API documentation.
- Fix typo: Replace all occurrences of "they key" with "the key" in the AutoKey documentation.
- Remove extra unneeded curly bracket from line 350 of engine.py for the API documentation.
- Update the **README.rst** file to satisfy part of issue #681 and issue #779.

Features
---------

Command line interface
^^^^^^^^^^^^^^^^^^^^^^

- Add a `--version` command-line switch. It prints the current AutoKey version on the standard output.

Graphical user interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^

- (GTK) Warn user about missing required and optional programs on startup.
- (GTK) UI will now update when changes are detected to watched files.
- (GTK) Refresh UI if script files are modified externally.
- Use system monospace font.
- Add setting to change GtkSourceView theme, (defaults to classic).

Scripting API
^^^^^^^^^^^^^

- **engine API object**
   - Deprecated: Confusingly-named `engine.create_abbreviation()` and `engine.create_hotkey()` are deprecated and
     will be removed in the future. Use `engine.create_phrase()` with appropriate arguments instead.
   - Extended: `engine.create_phrase()` now supports multiple new optional arguments, allowing to fully configure the
     created phrase. It can set everything the GUI can do.
   - New: Scripts can use `engine.get_triggered_abbreviation()` to read which abbreviation triggered its execution.
   
     | The function returns a tuple containing the abbreviation and the trigger character (the character that
       'completed' or 'confirmed' the abbreviation. Both tuple elements are **None** if the script was not triggered
        by an abbreviation. The trigger character is **None** if the script was configured to 'trigger immediately'.
        The function always returns a tuple, so direct tuple-unpacking like
        `abbreviation, trigger = engine.get_triggered_abbreviation()` will always work.
   - Allow creation of 'temporary' hotkeys and whole folders (which do not persist between sessions).
   - Allow overriding existing hotkeys when creating phrases with hotkeys.
   - Allow creation of folders.
   - Add `set_clipboard_image` methods for both GTK and Qt (takes a file path to an image to load into the
     clipboard).
- **keyboard API object**
   - `keyboard.send_keys()` got a new optional **send_mode** parameter allowing to specify how the given text is
     sent. It basically offers the same pasting options as are available to AutoKey phrases.
   - `keyboard.send_keys()` now raises a **TypeError** instead of a generic **AssertionError** if parameters don’t
     match the expected types.
- **New clipboard API method**
   - Change the default phrase send mode to `ctrl+v` (paste using clipboard) rather than sending keys one at a time.
- **New mouse API object**
   - Add mouse drag, click, and scroll options to the API.

Miscellaneous features
^^^^^^^^^^^^^^^^^^^^^^

- Add `wait_for_keyevent` scripting function.
- Rewrite script error-logging system, with a neat Script Error Dialog to go with it.
- `<script>` macros accept absolute paths.
- Macro arguments can be quoted, allowing arguments containing spaces.
- Macro arguments can contain angle bracket characters, if escaped.
- Add `<system>` macro for replacing phrase contents with output of an external process.
- Allow `autokey-run` to accept full paths to Python scripts (if no full path is given, will treat as an existing
  Autokey script-name instead).
- Expand Unicode characters using code points (hacky work-around for being unable to send actual Unicode).
- Allow disabling **Capslock** in settings
- Link to script `.py` and `.json` above editor.
- Add appropriate keywords to `.desktop` files for both UIs.
- Build debs and update PyPI on new releases

Important changes
-----------------

This version represents some significant refactoring since the previous update, so bug reports will be highly
appreciated.

- Script and phrase metadata are no longer stored as hidden dot-files. Existing scripts should be automatically
  converted, but if switching back to versions prior to this one, you will need to copy or symlink them back to
  dot-file form.
- Scripting API files are now in Python packages, which may require adjusting imports if you have scripts that
  import them directly.
- Change the default phrase send mode to `ctrl+v` (paste using clipboard) rather than sending keys one at a time.

Other changes
-------------

- Add CI for testing.
- Update pip installation requirements.
- Add `CONTRIBUTERS.rst` file.
- Internal code clean-up. The configuration handling module is split into multiple modules inside a dedicated
  package.
- AutoKey now has a working test environment again. `pytest` based unit-tests can be launched from the source
  checkout using the `python3 setup.py test` command.
- Add two sections to the issue template.
- Change all **sudo apt** references in **master** to **sudo apt-get** to satisfy part of issue #772.
- Bump Python version in **autokey.spec** AND **PKG-INFO**.
- Update the actions in the **build.yml** file to the latest versions in the GitHub Marketplace.
- Update the actions in the **pages.yml** file to the latest versions in the GitHub Marketplace.
- New Dependencies (test-time only): The new unit tests introduce two new, *test-time only* dependencies: `pytest`
  and `PyHamcrest`. These are used for unit tests only and not during normal AutoKey execution.
- Overhaul the CHANGELOG.rst file.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.11
======================

Bug fixes
---------

- Fix crash in Qt macro recording window.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.10
======================

Bug fixes
---------

- Beta: Fix segfault from modifying files when open in off-screen AK window.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.9
======================

Bug fixes
---------

- Fix Qt crashing when changing a hotkey.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.8
============================

Bug fixes
---------

- Fix installation not copying predefined user files. Fixes issue #578.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.5
============================

Bug fixes
---------

- Fix clear button not unsetting hotkeys.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.4
============================

Other fixes
-----------

- Fix updating of sidecar files.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.3
============================

Features
---------

- Build debs and update PyPI on new releases.
- Add `set_clipboard_image` methods for both GTK and Qt. Takes a file path to an image to load into the clipboard.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.2
============================

Bug fixes
---------

- Fix issue with pip installation reporting a missing module.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.96.0-beta.1
============================

Bug fixes
---------

- Both GTK and Qt versions will reload hotkeys after a keymap change event.
- Fix locking issue.
- Expose **Alt_GR** as a hotkey-modifier on GTK.
- (GTK) Fix GUI lock-up if multiple script error notifications are posted in quick succession. The notifications are
  now rate-limited and won't post more than one notification per second. Fixes issue #383.
- Packaging:
   - Fix AutoKey PNG icon size. Now, the icon size is 96x96 pixels, fixing Lintian warnings on Debian. Fixes issue
     #369.
- Scripting API:
   - Fix API call `system.exec_command()` crashing if output-capturing is active, but the executed command has
     empty output. Fixes issue #379.

Important changes
-----------------

- Script and phrase metadata are no longer stored as hidden dot-files. Existing scripts should be automatically
  converted, but if switch back to versions prior to this one, you will need to copy or symlink them back to dotfile
  form.
- Scripting API files are now in Python packages, which may require adjusting imports if you have scripts that
  import them directly.
- Change the default phrase send mode to `ctrl+v` (paste using clipboard) rather  than sending keys one at a time.
- This version represents some significant refactoring since the previous update, so bug reports will be highly
  appreciated.

Features
---------

Scripting API
^^^^^^^^^^^^^

- engine API object:
   - Deprecated: Confusingly-named `engine.create_abbreviation()` and `engine.create_hotkey()` are deprecated and
     will be removed in the future. Use `engine.create_phrase()` with appropriate arguments instead.
   - Extended: `engine.create_phrase()` now supports multiple new optional arguments allowing to fully configure
     the created phrase. It can set everything the GUI can do.
   - New: Scripts can use `engine.get_triggered_abbreviation()` to read which abbreviation triggered its execution.
   
     | The function returns a tuple containing the abbreviation and the trigger character (the character that
       'completed' or 'confirmed' the abbreviation. Both tuple elements are **None** if the script was not triggered
        by an abbreviation. The trigger character is **None** if the script was configured to 'trigger immediately'.
        The function always returns a tuple, so direct tuple-unpacking, like
        `abbreviation, trigger = engine.get_triggered_abbreviation()` will always work.
   - Allow creation of 'temporary' hotkeys and whole folders (which do not persist between sessions).
   - Allow overriding existing hotkeys when creating phrases with hotkeys.
   - Allow creation of folders.
- keyboard API object:
   - `keyboard.send_keys()` got a new optional parameter send_mode, allowing to specify how the given text is sent.
     It basically offers the same pasting options as are available to AutoKey phrases.
   - `keyboard.send_keys()` now raises a **TypeError** instead of a generic **AssertionError** if parameters don’t
     match the expected types.
- New clipboard API method:
   - Change the default phrase send mode to `ctrl+v` (paste using clipboard) rather than sending keys one at a time.
- New mouse API object:
   - Add mouse drag, click, and scroll options to the API.
- New window API method:
   - Add `center_window` to center selected window on selected monitor.
   - Add `get_window_geom` to fetch the window geometry of a window.
   - Add `get_window_hex` to get the hex ID of the first window that matches the given title.
   - Add `get_window_list` to get list of windows via the `wmctrl` command.

Command line interface
^^^^^^^^^^^^^^^^^^^^^^

- Add a `--version` command line switch. It prints the current AutoKey version on the standard output.

Graphical user interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^

- (GTK) Warn user about missing required and optional programs on startup.
- (GTK) UI will now update when changes are detected to watched files.
- (GTK) Refresh UI if script files are modified externally.
- Use system monospace font.
- Add setting to change GtkSourceView theme, (defaults to classic).

Miscellaneous features
^^^^^^^^^^^^^^^^^^^^^^

- Add `wait_for_keyevent` scripting function.
- Rewrite script error-logging system, with a neat Script Error Dialog to go with it.
- `<script>` macros accept absolute paths.
- Macro arguments can be quoted, allowing arguments containing spaces.
- Macro arguments can contain angle-bracket characters, if escaped.
- Add `<system>` macro for replacing phrase contents with output of an external process.
- Allow `autokey-run` to accept full paths to Python scripts (if no full path is given, will treat as an existing
  AutoKey script name instead).
- Expand Unicode characters using code points (hacky work-around for being unable to send actual Unicode).
- Allow disabling the **Capslock** modifier key in settings.
- Link to script `.py` and `.json` above editor.
- Add appropriate keywords to `.desktop` files for both UIs.

Other changes
-------------

- Add CI for testing.
- Update pip installation requirements.
- Add the `CONTRIBUTERS.rst` file.
- Internal code clean-up. The configuration-handling module is split into multiple modules inside a dedicated
  package.
- AutoKey now has a working test environment again. `pytest` based unit-tests can be launched from the source
  checkout using the `python3 setup.py test` command.
- New dependencies (test-time only): The new unit tests introduce two new *test-time only* dependencies: `pytest`
  and `PyHamcrest`. These are used for unit tests only and not during normal AutoKey execution.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.10 <2019-12-16>
============================

Bug fixes
---------

- Mitigate crashes when entering invalid Python regular expressions in the window filter dialogue. Fixes issue #212.
- Add option to disable the handling of the **Capslock** modifier key.
  Fixes issues when that key is remapped to something else, for example: **Ctrl**.
  The new option can be found in the settings dialogue. Fixes issues #95, #291.
- API function `system.exec_command()` now only trims the last character in the output
  if it is actually a newline character. If the executed command does not output a newline at the end,
  the full output is returned. Fixes issue #354.
- Fix wrong optional argument in man page for `autokey-run` (in pull request #361).
- Remove unnecessarily-set executable bit from several AutoKey SVG icons (in pull request #363).

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.9 <2019-12-07>
===========================

Bug fixes
---------

- Prevent data losses when deleting or moving directories from within AutoKey. AutoKey will only delete data it knows
  and keep unknown user data, so adding `$HOME` and then removing it again will not purge everything below it.
  Affected were deleting directories and moving them via drag & drop. Fixes issues #171, #332.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.8 <2019-11-07>
===========================

Bug fixes
---------

- Qt GUI: Fix issue with **Python 3.7.4** and **PyQt 5.11-5.13.0** that prevented AutoKey from starting on certain
  distributions shipping this configuration, notably **Kubuntu 19.10**. Fixes issues #313, #301.
- Qt GUI: Fix crash when saving the currently-edited item after deselecting it in the tree view. Fixes issue #285.
- Qt GUI: Disable Main window -> Tools -> Insert Macro when not editing a phrase. Fixes issue #276.
- Qt GUI: Add a warning that explains possible data loss when creating top-level directories at used specified
  locations. See issue #171.
- GTK GUI: Fix application hang when setting a custom value for "Trigger on" in the **Abbreviation** settings
  dialogue. Fixes issue #315.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.7 <2019-04-29>
===========================

Bug fixes
---------

- GTK GUI: Fix system tray icon context-menu entry :code:`View script error`, which was non-functional
  if the main window was closed. The entry now opens the main window first as a work-around,
  because a proper fix will require a major code overhaul. Fixes #222.
- Qt GUI: Fix the truncated GPLv3 license text shown in the About AutoKey dialogue.
  The dialogue window now shows the full license text. Fixes #258.
- Harden the logic to read application window titles. AutoKey now works
  if applications do not set the :code:`_NET_WM_VISIBLE_NAME` property of their windows. Fixes #257.
- Fix phrase expansion using the `keyboard` method, which was broken if AutoKey was started for the first time.
  Fixes #274.

Other fixes
-----------
- Improve the debug logging output: Remove unnecessary output, clarify wordings, etc. See #230.
- Qt GUI: Display the current Python version number in the About dialogue.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.6 <2019-02-09>
===========================

Bug fixes
---------

- Fix the combination of phrase settings :code:`Match phrase case to typed abbreviation` and
  :code:`Trigger immediately` to cause scripts and phrases to trigger on each and every key-press.
  Fixes issue #254 introduced in 0.95.5.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.5 <2019-02-07>
===========================

Bug fixes
---------

- Fix window filter detection always returning title: :code:`FocusProxy`, Class: `Focus-Proxy-Window.FocusProxy` on
  Java AWT applications. It now detects the proper window title and `WM_CLASS` attribute for Java AWT applications.
  Fixes issue #113.
- GTK GUI: Fix the window filter detection dialogue. On clicking OK, it hung the whole application.
  Now the dialogue window works as intended. Fixes issue #229.
- Fix abbreviation case-folding (ignore case option) with abbreviations defined as UPPER CASE in the abbreviation
  dialogue. Options :code:`Ignore case` and :code:`Match case` now work with upper-case abbreviations. Fixes issue
  #197.
- Prevent the keyboard from staying grabbed by AutoKey if exceptions are thrown while AutoKey performs a
  clipboard pasting action. Fixes issues #72, #225.
- Prevent writing :code:`None` to the clipboard. This prevents `autokey-gtk` from deadlocking,
  caused by an unreleased mutex. Fixes issue #226.
- Restrict phrase Undo functionality to phrases without special keys, because phrases containing special keys cannot
  be reliably undone. Fixes issue #196.
- Clarify autosave option wording in the settings window. The option now explicitly states what it does.
  Fixes issue #194.
- Force AutoKey to exit if the **X** server connection closes, most probably at log-out or session end. Fixes issue
  #198.
- Qt tray icon fixes and improvements:
   - Add **View script error** entry to the tray icon context menu, like in the GTK GUI. Part of issue #158.
   - Tray icon turns red, when scripts raise an error, like in the GTK GUI. Part of issue #158.
   - If changing the tray icon theme in the settings (light or dark), instantly apply the new theme without requiring
     an application restart. Part of issue #158.
   - The tray icon now works if it is disabled in the settings and then enabled again. Fixes issue #223.
   - Enable :code:`setup.py` to be directly called from the system shell. Fixes issue #218.
- Other fixes:
   - Clean up some legacy leftovers in the AutoKey repository.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.4 <2018-10-14>
===========================

Bug fixes
---------

- Fix grabbed hotkeys being incorrectly received by other applications.
- Fix crashes when processing `<code>` literals in strings.
  It is now possible to place `<code>` and `<code/>` literals in phrases.
  Additionally, such literals can be typed in scripts using the `keyboard.send_keys` function.
- Increase the reliability of the window-filter-detection dialogue in `autokey-qt`. The dialogue allows sampling windows
  to aid writing window filters. Due to timing issues in certain cases, sometimes the window title of the
  previously-active window was returned.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.3 <2018-08-21>
===========================

Bug fixes
---------
- Scripting API: The Python `__file__` global variable is now properly set for AutoKey scripts.
  It contains the full path to the Python script file currently running. Previously, it contained the full path to
  the `service.py` file of the currently-running AutoKey instance.
- Crash fix: Skip import of the AT-SPI interface if importing of `pyatspi` fails with a SyntaxError. This may happen
  with certain versions of `pyatspi` on Python 3.7. For details, see `#173`_.
- Fix serializing the store during saving if user stores recursive data-structures. It now handles/skips lists that
  contain themselves or other circular-referenced data-structures.
- GTK GUI: Fix autostart handling: Create the `$XDG_CONFIG_HOME/autostart` (`~/.config/autostart`) directory if it is
  not already present. Fixes `#149`_.
- Qt GUI: Create the user data directories before initializing the logger system. This prevents crashes when `autokey-qt`
  is used for the first time or when the user wiped all previous data. Fixes `#170`_.
- Qt GUI: Fix saving the "Always prompt before running this script" checkbox content when editing scripts. This option
  now works as intended again.

Features
--------

- Phrase expansion can now always be undone using the backspace key if the feature is enabled in the settings.
  Previously it was only be possible if the phrase was triggered by an abbreviation.
  Now it also works when using hotkeys or selecting phrases from menus.
  This also prevents crashes in `certain cases`_.
- Qt GUI: Add support for automatically starting `autokey-qt` during login. It can be configured in the settings
  dialogue. The configuration option allows to choose which GUI is automatically started if both `autokey-qt` and
  `autokey-gtk` are installed simultaneously and whether the main window should be shown automatically on launch.
- Qt GUI: Added the notification icon theme-selection to the settings dialogue. The added section in the general
  settings allows to choose between the light and dark theme, like in the `autokey-gtk` settings dialogue. Changing
  this setting currently requires an application restart to take effect.

Packaging
---------
- Stop shipping the `autokey.png` icon file inside a `scalable` icon theme directory. Moved to the appropriate raster
  image directory.
- Correct broken dependency package name in the `setup.py` file. The library is called `python-xlib` and not
  `python3-xlib` on PyPI.

.. _certain cases: https://github.com/autokey/autokey/issues/164
.. _`#173`: https://github.com/autokey/autokey/issues/173
.. _`#149`: https://github.com/autokey/autokey/issues/149
.. _`#170`: https://github.com/autokey/autokey/issues/170

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.2 <2018-07-16>
===========================

Bug fixes
---------

- Fix broken imports in the `autokey-shell` script.
- Skip non-json-serializable data in script storage (both script local and global) during saving. This allows putting
  non-serializable items (like function objects) into the store without crashing AutoKey during saving.
- Qt GUI: Fix minor bug when creating new items. Created items are now properly selected for renaming directly after
  creation.

Other fixes
-----------

- Minor code simplifications. Remove unnecessary functions that were obsoleted during prior changes.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.1 <2018-06-30>
===========================

Bug fixes
---------

- Fix a long-standing bug that errors occurring during phrase-parsing or script-execution that can lock up the user
  keyboard.
  Make sure to always release the keyboard after grabbing it. See `#72`_, launchpad_1551054_.
- Qt GUI: Fix saving the content of the log view to a file using the context-menu entry.
- Some small internal code-quality improvements.

.. _`#72`: https://github.com/autokey/autokey/issues/72
.. _launchpad_1551054: https://bugs.launchpad.net/ubuntu/+source/autokey/+bug/1551054

-------------------------------------------------------------------------------------------------------------------------------

Version 0.95.0 <2018-06-28>
===========================

Bug fixes
---------

- Fix the broken `Clipboard` and `Mouse selection` phrase paste modes.
   - Pasting using both `Clipboard` and `Mouse selection` works in both the Qt and GTK GUI. See `#101`_.
   - Fix restoring the clipboard after a paste is performed. Both GUIs now restore the previous clipboard content
     after a phrase is pasted.

   .. _`#101`: https://github.com/autokey/autokey/issues/101

Rewrite the Qt GUI, port to PyQt5
---------------------------------

- Resurrect, re-write and clean up the `autokey-qt` Qt GUI. `autokey-qt` is now a pure `PyQt5` application, only
  dependent on currently-supported libraries.

Added improvements
^^^^^^^^^^^^^^^^^^

- The main window now keeps its complete state when closed and re-opened (excluding complete application restarts).
  This includes the currently-selected item(s) in the tree-view on the left of the main window, selected text, and
  cursor position in the editor on the right if currently editing a phrase or script.
- The entries in the popup menu, that's shown when a hotkey assigned to a folder is pressed, now show icons based
  on their type (folder, phrase, or script). This also works when items are configured to be shown in the
  system-tray icon context menu.
- The *A* autokey application icons are now always displayed correctly, both in the main window and the system tray
  icon.
- Various menu actions now have system-dependent keyboard shortcuts that should adjust to the expected default of the
  user’s current platform/desktop environment.
- Add icons and descriptive tooltip texts to various buttons.
- The `enable monitoring` checkboxes (both in the `Settings` menu and the tray-icon context-menu) now properly react
  to pressing the global hotkey for this action and, thus, stay in sync even if the hotkey is used while the menu is
  shown.

Build-time dependencies
^^^^^^^^^^^^^^^^^^^^^^^

- Optionally depend on `pyrcc5` command-line tool to compile Qt resources into a Python module.
- Qt UI files are no longer compiled using `pykdeuic4`, Removed the old compiler wrapper script in commit 6eeeb92f_.

.. _6eeeb92f: https://github.com/autokey/autokey/commit/6eeeb92f14c694979c1367d51350c1e6509329b1

Changed features
^^^^^^^^^^^^^^^^

- The `hide tray icon` entry in the tray-icon context menu now hides the icon for the current session only. The entry
  does not permanently disable the tray icon any more without any confirmation. Now, the only way to permanently
  disable the tray icon is through using the appropriate setting in the settings dialogue.

Known bugs
^^^^^^^^^^

- The system tray icon is shown, but non-functional after enabling it in the settings dialogue. AutoKey Qt has to be
  restarted for the tray icon to start working. This should have no impact on normal, daily use.

Regressions
^^^^^^^^^^^

- Customizing the main window toolbar entries and keyboard shortcuts to trigger various UI actions is no longer
  possible. This feature was provided by the KDE4 libraries and is currently dropped.
- The previous, KDE4-based **About** dialogue is replaced with a very minimalistic one.
- The **Settings** dialogue heavily used the KDE4 functionalities. During the port to Qt5, the dialogue lost some
  visual style, but all core functionality is kept.

Runtime dependencies
^^^^^^^^^^^^^^^^^^^^

- Remove dependencies on deprecated and unmaintained PyQt4 and PyKDE4 libraries.
- Remove dependency on `dbus.mainloop.qt`. Instead, use the DBus support built into Qt5.
- Now depend on PyQt5, the Qt5 SVG module, and the Qt5 QScintilla2 module.

Scripting API Changes
---------------------

Additions
^^^^^^^^^

- Add a color-picker dialogue to the GTK `dialog` class, because the `zenity` now supports it.
- The picked color is returned as three integers using the `ColourData` NamedTuple, providing both index-based access
  and attribute access using the (`r`, `g`, `b`) channel names. Additionally, `ColourData` provides some conversion
  methods.

Breaking changes
^^^^^^^^^^^^^^^^

- See pull request `#148`_. The `dialog` classes for user-input in scripts now return typed NamedTuple tuples instead
  of plain tuples. This change is safe as long as users do not perform needlessly-restrictive type-checks in their
  scripts (e.g. `if type(returned_data) == type(tuple()): ...`). User scripts doing so will break.
- The KDialog-based color-picker now also returns a `ColourData` instance instead of an HTML-style hex string, thus
  making this portable between both GTK and Qt GUIs. AutoKey users previously using the old KDE GUI and using the
  color-picker dialogue have to port their scripts. A simple fix is using the `html_code` property of the returned
  `ColourData` instance.

.. _`#148`: https://github.com/autokey/autokey/pull/148

Fixes
^^^^^

- Re-introduce the newline-trimming for the `system.exec_command()` function. During the porting to Python 3, the
  newline-trimming was removed, causing users various issues with unexpected newline characters at end of output.
  Now properly remove the _last_ newline at the end of command output. See issues `#75`_, `#92`_, and `#145`_.
- Apply various code style-improvements to the scripting module.

.. _`#75`: https://github.com/autokey/autokey/issues/75
.. _`#92`: https://github.com/autokey/autokey/issues/92
.. _`#145`: https://github.com/autokey/autokey/issues/145

Other fixes and improvements
----------------------------

- Fix the KDialog-based color-picker provided in the scripting API. Newer versions of KDialog require an additional
  parameter, which is now added.
- Fix crashes related to mouse-pasting when using the GTK GUI.
- Both `autokey-gtk` and `autokey-qt` are now automatically-generated setuptools entry-points.
- `autokey-gtk` can now be launched directly from the AutoKey source tree.

  From the shell, `cd` into the `lib` directory, then use:

  .. code-block:: sh

    <path_to_autokey_source_dir>/lib$ python3 -m autokey.gtkui [-l] [-c]
    # Or alternatively, to launch `autokey-qt` use:
    <path_to_autokey_source_dir>/lib$ python3 -m autokey.qtui [-l] [-c]


- Various internal code style-improvements at various locations, like added type-hints, PEP8-style fixes, etc.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.94.0 <2018-05-12>
===========================

Documentation
-------------

- Various README updates.

Features
---------

- Add support for function keys F13 to F35.

Other changes
-------------

- Port `autokey-run` from the legacy `optparse` module to the new Python 3 `argparse` module.
- Use `$XDG_RUNTIME_DIR` and `$XDG_DATA_HOME` directories for lock and log file.
- Refactor the iomediator modules into a package.
- Apply various code cleanups and fixes.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.10 <2017-02-17>
============================

Other changes
-------------

- The scripting global storage now returns **None** if the requested key is not present.
- Improve the error messages in `autokey-run`. It is now clear that AutoKey has to run in the background for
  `autokey-run` to work.
- Add a `LICENSE` file containing the GPL v3 license terms.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.9 <2017-01-11>
===========================

Bug fixes
---------

- Fix a regression with the `install_requires` keyword argument in the `setup.py` file.
- Update the GitHub issue template.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.8 <2017-01-09>
===========================

Bug fixes
---------

- Leverage libappindicator completely. Fix "View script error".

Other changes
-------------

- Readme updates.
- Depend on Ubuntu appindicator.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.7 <2016-12-21>
===========================

Bug fixes/crash fixes
---------------------

- Rename repository from `autokey-py3` to `autokey`.
- Move the AutoKey source code one level upout of the `src` folder .
- Remove donate button.
- `autokey-gtk` script is now a `setuptools`-generated entry-point.
- Require GTK 3.0 to fix `autokey-gtk` startup.
- Update various web links around the code-base.
- New feature: Return the result of wait events in the iomediator module.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.6 <2016-08-13>
===========================

Bug fixes
---------

- Fix several GTK-related warnings.

Features
---------

- GTK GUI:  Add feature to trigger popup-menu items with letters rather than numbers.

Other changes
-------------

- Ensure compatibility with official `python-xlib`.
- Add an AUR link.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.4 <2015-02-17>
===========================

Bug fixes
---------

- Prevent clipboard-related crashes with GTK3.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.3 <2015-02-20>
===========================

Bug fixes
---------

- Bugfix for defining abbreviations by `@kuhanalog`_.

.. _@kuhanalog: https://github.com/kuhanalog

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.2 <2014-08-09>
===========================

Important changes
-----------------

- Read user scripts with UTF-8 encoding.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.1 <2014-03-02>
===========================

Other changes
-------------

- Internal changes: Change the data-structure of the input stack.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.93.0 <2014-02-27 Thu>
===============================

Features
---------

Add the `acknowledge_gnome_notification` and `move_to_pat` functions. More details `here`_.

.. _here: https://github.com/autokey/autokey/blob/master/new_features.rst

-------------------------------------------------------------------------------------------------------------------------------

Version 0.92.0 <2014-02-21 Fri>
===============================

Features
---------

- Add the `autokey-shell` interactive shell-launcher that allows you to run some AutoKey functions interactively.
  Read `this`_ for more details.

-------------------------------------------------------------------------------------------------------------------------------

Version 0.91.0 <2014-02-14 Fri>
===============================

Features
---------

- Add the new `click_on_pat` function for use in user-scripts. See `this`_ for more details.

.. _this: https://github.com/autokey/autokey/blob/master/new_features.rst

-------------------------------------------------------------------------------------------------------------------------------

First release <2014-01-31 Fri>
==============================
This describes some of the changes to the original AutoKey source code.

Bug fixes
---------

- Eliminate possible deadlock.

- Changed:

  .. code-block:: python

        p = subprocess.Popen([…], stdout=subprocess.PIPE)
        retCode = p.wait()
        output = p.stdout.read()[:-1] # Drop trailing newline

  to:

  .. code:: python

        p = subprocess.Popen([…], stdout=subprocess.PIPE)
        output = p.communicate()[0].decode()[:-1] # Drop trailing newline
        retCode = p.returncode

  The former may cause a deadlock. For more information, see `Python docs`_. This pattern appears several times in the source code.

  .. _Python docs: http://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait

- For a `gi.repository.Notify.Notification` object, test if method `attach_to_status_icon` exists before calling. After this fix, errors in user-scripts will trigger a notification.
- Respect XDG standard. See details `here`__.

__ https://code.google.com/p/autokey/issues/detail?id=266

- Correct a typo in the `autokey-run` man page.
- For the GTK GUI, after script error is viewed, tray icon is reverted back to original.

Python 3 changes
----------------

- Python 3 is less tolerant of circular imports, so some files were split into several files. Those pieces of the
original have their file names prefixed with the original files' names.

Other changes
-------------

- In the `setup.py` file, the `/usr/` prefix to the directory names in the `data_files` argument was removed to allow
for non-root install.
- Remove the “WINDOWID” environment variable so that zenity is not tied to the window from which it was launched.
- Modify the launcher and other files to allow for editable installs (`pip install -e`).
- Add an “about” dialogue for the Python 3 port.
- Change the hyperlink for bug reports.
