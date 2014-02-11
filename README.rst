===========
AutoKey-Py3
===========
.. contents::

About
=====
AutoKey-Py3 is a Python 3 port of `AutoKey`__, a desktop automation utility for Linux and X11.

__ https://code.google.com/p/autokey/

Installation
============
There are two GUIs for AutoKey-Py3, GTK and QT, and they have different dependencies. If you use the GTK GUI, there is no need to install dependencies for the QT GUI and vice versa.

The “--user” option for pip may be removed if you intend to do a system-wide install. You can also add the “-e” option to pip to install in `editable mode`__. “Editable” installs currently works only with the GTK GUI.

__ http://www.pip-installer.org/en/latest/logic.html#editable-installs

Debian
++++++
.. code:: sh

   # common dependencies
   apt-get install python3-pyinotify wmctrl
   # dependencies for GTK GUI, install only if you intend to use the GTK GUI.
   apt-get install python3-gi gir1.2-gtk-3.0 gir1.2-gtksource-3.0 gir1.2-glib-2.0 gir1.2-notify-0.7 python3-dbus zenity
   # dependencies for QT GUI, install only if you intend to use the QT GUI.
   apt-get install python3-pykde4 python3-pyqt4.qsci python3-dbus.mainloop.qt kde-baseapps-bin
   # execute as non root
   pip3 install --user python3-xlib
   # install AutoKey-Py3 from PyPI or …
   pip3 install --user autokey-py3
   # get the development version from GitHub
   pip3 install --user git+https://github.com/guoci/autokey-py3

Arch Linux
++++++++++
.. code:: sh

   pacman -S --needed wmctrl hicolor-icon-theme python-dbus python-pyinotify zenity
   # dependencies for GTK GUI, install only if you intend to use the GTK GUI.
   pacman -S --needed python-gobject gtksourceview3 libnotify
   # dependencies for QT GUI, install only if you intend to use the QT GUI.
   pacman -S --needed python-qscintilla kdebindings-python
   # execute as non root
   pip3 install --user python3-xlib
   # install AutoKey-Py3 from PyPI or …
   pip3 install --user autokey-py3
   # get the development version from GitHub
   pip3 install --user git+https://github.com/guoci/autokey-py3

Starting AutoKey-Py3
++++++++++++++++++++

.. code:: sh

   # make sure that autokey is in your search path.
   PATH="$HOME/.local/bin/:$PATH" # if installed with the --user option
   autokey-gtk # to start with the GTK3 GUI *OR*
   autokey-qt # to start with the QT4 GUI

Documentation
=============
Please refer to the original AutoKey's `scripting API`_ and `wiki`_.

.. _scripting API: http://autokey.googlecode.com/svn/trunk/doc/scripting/index.html
.. _wiki: https://code.google.com/p/autokey/w/list

Porting your scripts
====================
Changes were made to source code to keep the scripting API stable. system.exec_command() returns a string. But if you use functions from the standard library you will have to fix that, as your script runs on a Python 3 interpreter. For example, expect subprocess.check_output() to return a bytes object.

`2to3`_ can be used to do an automatic transformation of source code.

Some guides on porting code to Python 3:
 - http://python3porting.com/
 - http://www.diveintopython3.net/porting-code-to-python-3-with-2to3.html

.. _2to3: http://docs.python.org/dev/library/2to3.html

Bug reports
===========
Logging information can be obtained by starting the launcher with the “-l” option.

.. code:: sh

   autokey-gtk -l # or
   autokey-qt -l

Please use the `GitHub Issue Tracker`_ for bug reports.

.. _GitHub Issue Tracker: https://github.com/guoci/autokey-py3/issues

Changelog
=========
Here__.

.. PyPI doesn't accept relative links.
__ https://github.com/guoci/autokey-py3/blob/master/CHANGELOG.rst

License
=======
GNU GPL v3.
