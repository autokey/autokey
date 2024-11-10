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
`AutoKey`_, a desktop automation utility for Linux and X11, formerly hosted on `Google`_, has been updated to run on Python 3.

**Important**: This is an X11 application and, as such, will not function correctly when Wayland is in use instead of Xorg.

.. _AutoKey: https://github.com/autokey/autokey
.. _Google: https://code.google.com/archive/p/autokey/

Installation
============

**Important**: Please remove previous installations of AutoKey fully before installing!

For detailed installation instructions, please visit the `Installing`_ page in our wiki.

.. _Installing: https://github.com/autokey/autokey/wiki/Installing

Documentation
=============
AutoKey documentation is available `here <https://autokey.github.io/index.html>`__ and, for versions prior to 0.96.0, `here <https://autokey.github.io/autokey/index.html>`__. Example code and explanations for how AutoKey works can be found in our `wiki`_ and, in particular, on the `Features`_ and `Example Scripts`_ pages. Additional information can be found by searching `Stack Overflow`_ and `GitHub`_.

.. _wiki: https://github.com/autokey/autokey/wiki
.. _Features: https://github.com/autokey/autokey/wiki/Features
.. _Example Scripts: https://github.com/autokey/autokey/wiki/Example-Scripts
.. _Stack Overflow: https://stackoverflow.com/questions/tagged/autokey
.. _GitHub: https://github.com/search?l=Python&q=autokey&ref=cmdform&type=Repositories

Support
=======

Please do not request support on the issue tracker. Instead, head over to the autokey-users `Google Groups`_ forum, `Gitter`_ web-based chat, on `IRC`_ (#autokey on `Libera.Chat`_), or `Stack Overflow`_.

We'd appreciate it if you take a look at our `Troubleshooting`_ wiki page before posting. You'll be more likely to get a good answer quickly by providing as much information as you can.

.. _Google Groups: https://groups.google.com/forum/#!forum/autokey-users
.. _Stack Overflow: https://stackoverflow.com/questions/tagged/autokey
.. _IRC: https://web.libera.chat/#autokey
.. _Libera.Chat: https://libera.chat/guides/
.. _Gitter: https://gitter.im/autokey/autokey
.. _Troubleshooting: https://github.com/autokey/autokey/wiki/Troubleshooting

Bug reports
===========
Bug reports are welcome. Please use the `GitHub Issue Tracker`_ to report bugs. When reporting a suspected bug, please make sure to include as much information as possible to expedite troubleshooting and resolution.

Here are some possible examples of the types of information you might need to provide:

* Details on how to reproduce the issue you are experiencing are always helpful.
* An `AutoKey error message`_ is helpful when something is wrong with your AutoKey script.
* An `AutoKey traceback`_ is helpful when AutoKey runs without crashing, a trigger was used, and the expected event either didn't occur or something other than the expected result occurred.
* A `Python traceback`_ is helpful when something is wrong with your AutoKey script, causing an exception to be shown in your AutoKey error message.

If you're not sure your issue is a bug or you'd like help with reporting it, you can post about it first on one of the `platforms used by our community`_ and we'll assist you.

.. _GitHub Issue Tracker: https://github.com/autokey/autokey/issues
.. _AutoKey error message: https://github.com/autokey/autokey/wiki/Troubleshooting#autokey-error-message
.. _AutoKey traceback: https://github.com/autokey/autokey/wiki/Troubleshooting#autokey-traceback
.. _Python traceback: https://github.com/autokey/autokey/wiki/Troubleshooting#python-traceback
.. _platforms used by our community: https://github.com/autokey/autokey/wiki/Community

Contributing or modifying the source
====================================

Pull requests are welcome from anyone who would like to modify or contribute to the source code. Useful tips for working with and testing the code can be found in the `CONTRIBUTORS.rst`_ file. AutoKey also participates in `CodeTriage`_, where members can sign up to receive a periodic email with a link to an open AutoKey issue that needs help.

.. _CodeTriage: https://www.codetriage.com/autokey/autokey
.. _CONTRIBUTORS.rst: https://github.com/autokey/autokey/blob/master/CONTRIBUTORS.rst

Changelog
=========
Our `changelog`_ is the best source of information for what's new and fixed in each release.

.. _changelog: https://github.com/autokey/autokey/blob/master/CHANGELOG.rst

License
=======
AutoKey uses the `GNU GPL v3`_. See the `LICENSE`_ file for a plain text copy of the license.

.. _GNU GPL v3: https://www.gnu.org/licenses/gpl-3.0.html
.. _LICENSE: https://github.com/autokey/autokey/blob/master/LICENSE
