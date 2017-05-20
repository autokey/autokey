===========
AutoKey-Py3
===========

.. image:: https://img.shields.io/badge/IRC-%23autokey%20on%20freenode-blue.svg
    :target: https://webchat.freenode.net/?channels=autokey

.. image:: https://badges.gitter.im/autokey-py3/autokey.svg
   :alt: Join the chat at https://gitter.im/autokey-py3/autokey
   :target: https://gitter.im/autokey-py3/autokey

About
=====
AutoKey-Py3 (`GitHub`_) is a Python 3 port of `AutoKey`_, a text expansion and desktop automation utility for Linux and X11. It is comparable to TextExpander on MacOS and Breevy on Windows.

New features have since been added to AutoKey-Py3 after the initial porting. Read `new features`_ for details.

.. _GitHub: https://github.com/autokey-py3/autokey
.. _AutoKey: https://code.google.com/archive/p/autokey/
.. _new features: https://github.com/autokey-py3/autokey/blob/master/new_features.rst

Installation
============

See the Wiki for detailed installation instructions.

Documentation
=============
Documentation for `new features`_. For older features, please refer to the original AutoKey's `scripting API`_, `wiki`_ and `Stack Overflow`_.

Examples of AutoKey scripts can be found by `searching GitHub`_ and reading AutoKey's `wiki`_.

.. _scripting API: https://autokey-py3.github.io/index.html
.. _searching GitHub: https://github.com/search?l=Python&q=autokey&ref=cmdform&type=Repositories
.. _Stack Overflow: https://stackoverflow.com/questions/tagged/autokey
.. _wiki: https://github.com/autokey-py3/autokey/wiki

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

Please do not request support on the issue tracker. Instead, head over to the autokey-users `Google Groups`_ forum, on `IRC`_ (#autokey on Freenode), or `Gitter`_ web-based chat.

We'd appreciate it if you take a look at `Problem reporting guide`_ before posting. By providing as much information as you can, you'll have a much better chance of getting a good answer in less time.

.. _Google Groups: https://groups.google.com/forum/#!forum/autokey-users
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


