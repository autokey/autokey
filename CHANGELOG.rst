=========
Changelog
=========
.. contents::


Version 0.94.0 <2018-05-12>
===========================
- Various README updates
- Ported autokey-run from the legacy optparse module to the new Python 3 argparse module
- Use $XDG_RUNTIME_DIR and $XDG_DATA_HOME directories for lock and log file
- Added support for function keys F13 to F35
- Refactored the iomediator modules into a package. Applied various code cleanups and fixes.

Version 0.93.10 <2017-02-17>
============================
The scripting global storage now returns None if the requested key is not present.
Improved the error messages in autokey-run. It is now clear that autokey has to run in the background
for autokey-run to work.
Added a LICENSE file containing the GPL v3 license terms.

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
- EnsCompatibility with official python-xlib
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
++++++++++++++++++++++++
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
