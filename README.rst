===========
AutoKey-Py3
===========
.. contents::

About
=====
AutoKey-Py3 (`GitHub`_) is a Python 3 port of `AutoKey`_, a desktop automation utility for Linux and X11.

New features have since been added to AutoKey-Py3 after the initial porting. Read `new features`_ for details.

.. _GitHub: https://github.com/autokey-py3/autokey-py3
.. _AutoKey: https://code.google.com/archive/p/autokey/
.. _new features: https://github.com/autokey-py3/autokey-py3/blob/master/new_features.rst

Installation
============

Dependencies
++++++++++++
There are two GUIs for AutoKey-Py3, GTK and QT, and they have different dependencies. If you use the GTK GUI, there is no need to install dependencies for the QT GUI and vice versa.

Python modules (common):

- dbus-python
- pyinotify
- python-xlib
- typing

GTK GUI:

- PyGTK
- GtkSourceView

QT GUI:

- PyQt4
- PyKDE4

pip (recommended)
+++++++++++++++++
.. code:: sh

   pip install --user git+https://github.com/autokey-py3/autokey-py3

The "--user" option for pip may be removed if you intend to do a system-wide install. You can also add the "-e" option to pip to install in `editable mode`__. Editable installs currently work only with the GTK GUI.

__ https://pip.pypa.io/en/latest/reference/pip_install/#editable-installs

Virtualenv
++++++++++
.. code:: sh

   virtualenv --system-site-packages ~/autokey
   . ~/autokey/bin/activate
   pip install git+https://github.com/autokey-py3/autokey-py3

Ubuntu/Debian
+++++++++++++
.. code:: sh

   # common dependencies
   apt-get install python3-pyinotify wmctrl xautomation imagemagick
   # dependencies for GTK GUI, install only if you intend to use the GTK GUI.
   apt-get install python3-gi gir1.2-gtk-3.0 gir1.2-gtksource-3.0 gir1.2-glib-2.0 gir1.2-notify-0.7 python3-dbus zenity
   # dependencies for QT GUI, install only if you intend to use the QT GUI.
   apt-get install python3-pykde4 python3-pyqt4.qsci python3-dbus.mainloop.qt kde-baseapps-bin
   # execute as non root
   pip3 install --user python3-xlib
   # install AutoKey-Py3 from PyPI or
   pip3 install --user autokey-py3
   # get the development version from GitHub
   pip3 install --user git+https://github.com/autokey-py3/autokey-py3

Fedora/CentOS
+++++++++++++

Arch Linux
++++++++++

Available in the `AUR`_.

.. _AUR: https://aur.archlinux.org/packages/autokey-py3

To install from PyPI:

.. code:: sh

   pacman -S --needed wmctrl hicolor-icon-theme python-dbus python-pyinotify zenity xautomation imagemagick xorg-xwd
   # dependencies for GTK GUI, install only if you intend to use the GTK GUI.
   pacman -S --needed python-gobject gtksourceview3 libnotify
   # dependencies for QT GUI, install only if you intend to use the QT GUI.
   pacman -S --needed python-qscintilla kdebindings-python
   # execute as non root
   pip3 install --user python3-xlib
   # install AutoKey-Py3 from PyPI or
   pip3 install --user autokey-py3
   # get the development version from GitHub
   pip3 install --user git+https://github.com/autokey-py3/autokey-py3

Gentoo
++++++

Available via layman_, thanks to y2kbadbug.

.. _layman: https://github.com/y2kbadbug/gentoo-overlay/tree/master/app-misc/autokey-py3

To install:

.. code:: sh

   layman -a y2kbadbug
   emerge --sync
   emerge -av autokey-py3

Starting AutoKey-Py3
++++++++++++++++++++

.. code:: sh

   # make sure that autokey is in your search path.
   PATH="$HOME/.local/bin/:$PATH" # if installed with the --user option
   autokey-gtk # to start with the GTK3 GUI *OR*
   autokey-qt # to start with the QT4 GUI

Documentation
=============
Documentation for `new features`_. For older features, please refer to the original AutoKey's `scripting API`_, `wiki`_ and `Stack Overflow`_.

Examples of AutoKey scripts can be found by `searching GitHub`_ and reading AutoKey's `wiki`_.

.. _scripting API: https://autokey-py3.github.io/index.html
.. _searching GitHub: https://github.com/search?l=Python&q=autokey&ref=cmdform&type=Repositories
.. _Stack Overflow: https://stackoverflow.com/questions/tagged/autokey
.. _wiki: https://github.com/autokey-py3/autokey-py3/wiki

Porting your scripts
====================
Changes were made to source code to keep the scripting API stable. system.exec_command() returns a string. But if you use functions from the standard library you will have to fix that, as your script runs on a Python 3 interpreter. For example, expect subprocess.check_output() to return a bytes object.

`2to3`_ can be used to do automatically translate source code.

Some guides on porting code to Python 3:
 - http://python3porting.com/
 - http://www.diveintopython3.net/porting-code-to-python-3-with-2to3.html

.. _2to3: http://docs.python.org/dev/library/2to3.html

Support
=======

Please do not request support on the issue tracker. Instead, head over to the autokey-users `Google Groups`_ forum, or on `IRC`_ (#autokey on Freenode).

.. _Google Groups: https://groups.google.com/forum/#!forum/autokey-users
.. _IRC: irc://irc.freenode.net/#autokey

Bug reports and Pull Requests
=============================
Bug reports and pull requests are welcome. Please use the `GitHub Issue Tracker`_ for bug reports. When reporting a suspected bug, please test against latest ``git HEAD`` and make sure to include as much information as possible to expedite troubleshooting and resolution. For example,

* **required:** How to reproduce the issue you are experiencing
* **required:** The exact version of Autokey that you're using
* Python tracebacks
* Verbose logging information obtained by starting the frontend (``autokey-gtk`` or ``autokey-qt``) from terminal with the ``--verbose`` option.

.. _GitHub Issue Tracker: https://github.com/autokey-py3/autokey-py3/issues

Changelog
=========
Here__.

__ https://github.com/autokey-py3/autokey-py3/blob/master/CHANGELOG.rst

License
=======
GNU GPL v3.
