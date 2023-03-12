=======
AutoKey
=======

.. image:: https://img.shields.io/badge/IRC-%23autokey%20on%20Libera.Chat-blue.svg
    :target: https://web.libera.chat/#autokey

.. image:: https://badges.gitter.im/autokey/autokey.svg
   :alt: Join the chat at https://gitter.im/autokey/autokey
   :target: https://gitter.im/autokey/autokey

.. image:: http://img.shields.io/badge/stackoverflow-autokey-blue.svg
   :alt: Ask and answer questions on StackOverflow
   :target: https://stackoverflow.com/questions/tagged/autokey

.. image:: https://www.codetriage.com/autokey/autokey/badges/users.svg
    :target: https://www.codetriage.com/autokey/autokey

.. contents::

About
=====
`AutoKey`_, a desktop automation utility for Linux and X11, formerly hosted at `OldAutoKey`_. Updated to run on Python 3.

**Important**: This is an X11 application and, as such, will not function correctly when Wayland is in use instead of Xorg.

.. _AutoKey: https://github.com/autokey/autokey
.. _OldAutoKey: https://code.google.com/archive/p/autokey/

Installation
============

**Important**: Please remove previous installations of both AutoKey and AutoKey-py3 fully before installing!

For detailed installation instructions, please visit the `Installing`_ page. in our wiki.

.. _Installing: https://github.com/autokey/autokey/wiki/Installing

Documentation
=============
`Documentation`_ is available for `new features`_. For older features, please refer to the original AutoKey `scripting API`_, `Features wiki page`_ in the wiki, and `Stack Overflow`_. Examples of AutoKey scripts can be found by `searching GitHub`_ and reading AutoKey's `Example Scripts wiki page`_.

.. _scripting API: https://autokey.github.io/index.html
.. _Documentation: https://autokey.github.io/autokey/api.html
.. _searching GitHub: https://github.com/search?l=Python&q=autokey&ref=cmdform&type=Repositories
.. _Example Scripts wiki page: https://github.com/autokey/autokey/wiki/Example-Scripts
.. _Features wiki page: https://github.com/autokey/autokey/wiki/Features
.. _Stack Overflow: https://stackoverflow.com/questions/tagged/autokey
.. _new features: https://github.com/autokey/autokey/blob/develop/new_features.rst

Support
=======

Please do not request support on the issue tracker. Instead, head over to the autokey-users `Google Groups`_ forum, `StackOverflow`_, on `IRC`_ (#autokey on `Libera.Chat`_), or `Gitter`_ web-based chat.

We'd appreciate it if you take a look at `Troubleshooting`_ wiki page before posting. By providing as much information as you can, you'll have a much better chance of getting a good answer in less time.

.. _Google Groups: https://groups.google.com/forum/#!forum/autokey-users
.. _StackOverflow: https://stackoverflow.com/questions/tagged/autokey
.. _IRC: https://web.libera.chat/#autokey
.. _Libera.Chat: https://libera.chat/guides/
.. _Gitter: https://gitter.im/autokey/autokey
.. _Troubleshooting: https://github.com/autokey/autokey/wiki/Troubleshooting

Bug reports
===========
Bug reports are welcome. Please use the `GitHub Issue Tracker`_ for bug reports. When reporting a suspected bug, please test against the latest ``git HEAD`` and make sure to include as much information as possible to expedite troubleshooting and resolution. For example:

* **Required:** How to reproduce the issue you are experiencing
* Python tracebacks, if any
* Verbose logging information obtained by starting the front-end (``autokey-gtk`` or ``autokey-qt``) from terminal with the ``--verbose`` option.

.. _GitHub Issue Tracker: https://github.com/autokey/autokey/issues

Contributing or modifying the source
====================================

Pull requests are welcome from anyone who would like to modify or contribute to the source code. Useful tips for working with and testing the code can be found in the `CONTRIBUTORS.rst`_ file. AutoKey also participates in `CodeTriage`_, where members can sign up to receive a periodic email with a link to an open AutoKey issue that needs help.

.. _CodeTriage: https://www.codetriage.com/autokey/autokey
.. _CONTRIBUTORS.rst: https://github.com/autokey/autokey/blob/develop/CONTRIBUTORS.rst

Changelog
=========
The changelog is located here__.

__ https://github.com/autokey/autokey/blob/develop/CHANGELOG.rst

License
=======
AutoKey uses the `GNU GPL v3`_. See the `LICENSE`_ file for a plain text copy of the license.

.. _GNU GPL v3: https://www.gnu.org/licenses/gpl-3.0.html
.. _LICENSE: https://github.com/autokey/autokey/blob/master/LICENSE
