===========
AutoKey-Py3
===========

.. image:: https://img.shields.io/badge/IRC-%23autokey%20on%20freenode-blue.svg
    :target: https://webchat.freenode.net/?channels=autokey

.. image:: https://badges.gitter.im/autokey-py3/autokey.svg
   :alt: Join the chat at https://gitter.im/autokey-py3/autokey
   :target: https://gitter.im/autokey-py3/autokey

.. image:: http://img.shields.io/badge/stackoverflow-autokey-blue.svg
   :alt: Ask and answer questions on StackOverflow
   :target: https://stackoverflow.com/questions/tagged/autokey


About
=====
AutoKey-Py3 (`GitHub`_) is a Python 3 port of `AutoKey`_, a desktop automation utility for Linux and X11.

New features have since been added to AutoKey-Py3 after the initial porting. Read `new features`_ for details.

.. _GitHub: https://github.com/autokey-py3/autokey
.. _AutoKey: https://code.google.com/archive/p/autokey/
.. _new features: https://github.com/autokey-py3/autokey/blob/master/new_features.rst

Installation
============

**Please remove previous installations of both AutoKey and AutoKey-Py3 fully before installing!**

Dependencies
++++++++++++

Python: 3.5

Python modules (common):

- dbus-python
- pyinotify
- python-xlib

GTK frontend only:

- GObject Introspection
- PyGTK
- GtkSourceView
- libappindicator

QT frontend only:

- PyQt4
- PyKDE4

Manual install via pip
++++++++++++++++++++++

pip will automatically resolve and install dependencies, but dbus-python requires the dbus headers be present on your system. These are usually installed through your package manager, and usually are named dbus-devel or libdbus-dev or similar.

.. code:: sh

   pip3 install --user git+https://github.com/autokey-py3/autokey

The "--user" option for pip may be removed if you intend to do a system-wide install.

Ubuntu/Mint/Debian
++++++++++++++++++

Try the (experimental) PPA! Note that only Ubuntu 16.04, Mint 18, or above are supported for now as they supply Python 3.5 by default. Earlier versions of Python <= 3.4 require the ``typing`` module be installed separately.

.. code:: sh

   sudo add-apt-repository ppa:troxor/autokey
   sudo apt update
   sudo apt install autokey-gtk

Packages for other Debian-based distros can be built using files under ``debian/``

Arch Linux
++++++++++

Available in the `AUR`_. Unfortunately, Arch has removed the kdebindings-python package, so only the GTK frontend is usable for now.

.. _AUR: https://aur.archlinux.org/packages/autokey-py3

Gentoo
++++++

Available via layman_.

.. _layman: https://github.com/y2kbadbug/gentoo-overlay/tree/master/app-misc/autokey-py3

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
Documentation for `new features`_. For older features, please refer to the original AutoKey's `scripting API`_, `wiki`_, and `Stack Overflow`_.

Examples of AutoKey scripts can be found by `searching GitHub`_ and reading AutoKey's `wiki`_.

.. _scripting API: https://autokey-py3.github.io/index.html
.. _searching GitHub: https://github.com/search?l=Python&q=autokey&ref=cmdform&type=Repositories
.. _wiki: https://github.com/autokey-py3/autokey/wiki
.. _Stack Overflow: https://stackoverflow.com/questions/tagged/autokey

Porting your scripts from Python 2
==================================
Changes were made to source code to keep the scripting API stable. ``system.exec_command()`` returns a string. But if you use functions from the standard library you will have to fix that, as your script runs on a Python 3 interpreter. For example, expect subprocess.check_output() to return a bytes object.

`2to3`_ can be used to do automatically translate source code.

Some guides on porting code to Python 3:
 - http://python3porting.com/
 - http://www.diveintopython3.net/porting-code-to-python-3-with-2to3.html

.. _2to3: http://docs.python.org/dev/library/2to3.html

Support
=======

Please do not request support on the issue tracker. Instead, head over to the autokey-users `Google Groups`_ forum, `StackOverflow`_, on `IRC`_ (#autokey on Freenode), or `Gitter`_ web-based chat.

We'd appreciate it if you take a look at `Problem reporting guide`_ before posting. By providing as much information as you can, you'll have a much better chance of getting a good answer in less time.

.. _Google Groups: https://groups.google.com/forum/#!forum/autokey-users
.. _StackOverflow: https://stackoverflow.com/questions/tagged/autokey
.. _IRC: irc://irc.freenode.net/#autokey
.. _Gitter: https://gitter.im/autokey-py3
.. _Problem reporting guide: https://github.com/autokey/autokey/wiki/Problem-Reporting-Guide

Bug reports and Pull Requests
=============================
Bug reports and PRs are welcome. Please use the `GitHub Issue Tracker`_ for bug reports. When reporting a suspected bug, please test against latest ``git HEAD`` and make sure to include as much information as possible to expedite troubleshooting and resolution. For example,

* **required:** How to reproduce the issue you are experiencing
* Python tracebacks, if any
* Verbose logging information obtained by starting the frontend (``autokey-gtk`` or ``autokey-qt``) from terminal with the ``--verbose`` option.

.. _GitHub Issue Tracker: https://github.com/autokey-py3/autokey/issues

Changelog
=========
Here__.

__ https://github.com/autokey-py3/autokey/blob/master/CHANGELOG.rst

License
=======
GNU GPL v3.


