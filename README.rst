=======
AutoKey
=======

.. image:: https://img.shields.io/badge/IRC-%23autokey%20on%20freenode-blue.svg
    :target: https://webchat.freenode.net/?channels=autokey

.. image:: https://badges.gitter.im/autokey/autokey.svg
   :alt: Join the chat at https://gitter.im/autokey-py3/autokey
   :target: https://gitter.im/autokey-py3/autokey

.. image:: http://img.shields.io/badge/stackoverflow-autokey-blue.svg
   :alt: Ask and answer questions on StackOverflow
   :target: https://stackoverflow.com/questions/tagged/autokey


About
=====
`AutoKey`_, a desktop automation utility for Linux and X11, formerly hosted at `OldAutoKey`_. Updated to run on Python 3.

.. _AutoKey: https://github.com/autokey/autokey
.. _OldAutoKey: https://code.google.com/archive/p/autokey/

Installation
============

**Please remove previous installations of both AutoKey and AutoKey fully before installing!**

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

   pip3 install autokey
   # or, if you want the latest from this repository,
   pip3 install git+https://github.com/autokey3/autokey

The "--user" option for pip may be added to install for the current user only.

Ubuntu/Mint/Debian
++++++++++++++++++

Try the (experimental) PPA! Note that only Ubuntu 16.04, Mint 18, or above are supported for now as they supply Python 3.5 by default. Earlier versions of Python <= 3.4 require the ``typing`` module be installed separately.

.. code:: sh

   sudo add-apt-repository ppa:troxor/autokey
   sudo apt update
   sudo apt install autokey-gtk

Distro package not provided? Create your own package for Debian-based distros using files under ``debian/`` . Check out the `Packaging`_ wiki page for details.

.. _Packaging: https://github.com/autokey/autokey/wiki/Packaging

Arch Linux
++++++++++

Available in the `AUR`_. Unfortunately, Arch has removed the kdebindings-python package, so only the GTK frontend is usable for now.

.. _AUR: https://aur.archlinux.org/packages/autokey

Gentoo
++++++

Available via layman_.

.. _layman: https://github.com/y2kbadbug/gentoo-overlay/tree/master/app-misc/autokey

.. code:: sh

   layman -a y2kbadbug
   emerge --sync
   emerge -av autokey

Fedora
++++++

Build package using provided .spec file (may be outdated)

Documentation
=============
Documentation for `new features`_. For older features, please refer to the original AutoKey's `scripting API`_, `wiki`_, and `Stack Overflow`_.

Examples of AutoKey scripts can be found by `searching GitHub`_ and reading AutoKey's `wiki`_.

.. _scripting API: https://autokey.github.io/index.html
.. _searching GitHub: https://github.com/search?l=Python&q=autokey&ref=cmdform&type=Repositories
.. _wiki: https://github.com/autokey/autokey/wiki
.. _Stack Overflow: https://stackoverflow.com/questions/tagged/autokey
.. _new features: https://github.com/autokey/autokey/blob/master/new_features.rst

Support
=======

Please do not request support on the issue tracker. Instead, head over to the autokey-users `Google Groups`_ forum, `StackOverflow`_, on `IRC`_ (#autokey on Freenode), or `Gitter`_ web-based chat.

We'd appreciate it if you take a look at `Problem reporting guide`_ before posting. By providing as much information as you can, you'll have a much better chance of getting a good answer in less time.

.. _Google Groups: https://groups.google.com/forum/#!forum/autokey-users
.. _StackOverflow: https://stackoverflow.com/questions/tagged/autokey
.. _IRC: irc://irc.freenode.net/#autokey
.. _Gitter: https://gitter.im/autokey-py3/autokey
.. _Problem reporting guide: https://github.com/autokey/autokey/wiki/Problem-Reporting-Guide

Bug reports and Pull Requests
=============================
Bug reports and PRs are welcome. Please use the `GitHub Issue Tracker`_ for bug reports. When reporting a suspected bug, please test against latest ``git HEAD`` and make sure to include as much information as possible to expedite troubleshooting and resolution. For example,

* **required:** How to reproduce the issue you are experiencing
* Python tracebacks, if any
* Verbose logging information obtained by starting the frontend (``autokey-gtk`` or ``autokey-qt``) from terminal with the ``--verbose`` option.

.. _GitHub Issue Tracker: https://github.com/autokey/autokey/issues

Changelog
=========
Here__.

__ https://github.com/autokey/autokey/blob/master/CHANGELOG.rst

License
=======
GNU GPL v3.


.. image:: https://badges.gitter.im/autokey/autokey.svg
   :alt: Join the chat at https://gitter.im/autokey/autokey
   :target: https://gitter.im/autokey/autokey?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge