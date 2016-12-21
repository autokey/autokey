=========
Changelog
=========
.. contents::

Version 0.93.0 <2014-02-27 Thu>
===============================

Added functions “acknowledge_gnome_notification” and “move_to_pat”, more details `here`_.

.. _here: https://github.com/autokey-py3/autokey/blob/master/new_features.rst

Version 0.92.0 <2014-02-21 Fri>
===============================
Added an interactive shell launcher, “autokey-shell”. “autokey-shell” allows you to run some AutoKey-Py3 functions interactively. Read `this`_ for more details.


Version 0.91.0 <2014-02-14 Fri>
===============================
Added a new function “click_on_pat” for use in user scripts. See `this`_ for more details.

.. _this: https://github.com/autokey-py3/autokey/blob/master/new_features.rst


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
