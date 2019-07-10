=======
AutoKey
=======

.. image:: https://img.shields.io/badge/IRC-%23autokey%20on%20freenode-blue.svg
    :target: https://webchat.freenode.net/?channels=autokey

.. image:: https://badges.gitter.im/autokey/autokey.svg
   :alt: Join the chat at https://gitter.im/autokey/autokey
   :target: https://gitter.im/autokey/autokey

.. image:: http://img.shields.io/badge/stackoverflow-autokey-blue.svg
   :alt: Ask and answer questions on StackOverflow
   :target: https://stackoverflow.com/questions/tagged/autokey



.. contents::


About
=====
`AutoKey`_, a desktop automation utility for Linux and X11, formerly hosted at `OldAutoKey`_. Updated to run on Python 3. 

**Important**: This is an X11 application, and as such will not function 100% on distributions that default to using Wayland instead of Xorg.

.. _AutoKey: https://github.com/autokey/autokey
.. _OldAutoKey: https://code.google.com/archive/p/autokey/

Installation
============

**Please remove previous installations of both AutoKey and AutoKey-py3 fully before installing!**

For detailed installation instructions, please visit the `Installation`_ page. in our wiki.

.. _Installation: https://github.com/autokey/autokey/wiki/Installing

Zero-installation Method
++++++++++++++++++++++++

AutoKey can also be used directly from the cloned repository. This is useful, e.g., for trying
out a new version without removing a current installation.

1. Start the Autokey daemon

.. code:: sh

   cd lib
   python3 -m autokey.gtkui
   # or for KDE
   python3 -m autokey.qtui

2. Start the Autokey UI (if desired) by appending the --configure or -c command line switch to the end of the command.

The commands accept CLI switches just like the regular installation, so
:code:`python3 -m autokey.qtui -lc` works as expected.


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
.. _Gitter: https://gitter.im/autokey/autokey
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
`GNU GPL v3.`_ See the LICENSE file alongside this README for a plain text copy of the license text.

.. _GNU GPL v3.: https://www.gnu.org/licenses/gpl.html
