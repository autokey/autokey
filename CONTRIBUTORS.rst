Contributing
============
When you want to contribute new features or fix things, you are free to take virtually any task you wish. Just open a PR for discussion and maintainers will try to answer any questions that arise.

Setting up the development environment
--------------------------------------
First create a personal fork of the repository, and create a new branch based off the `develop` branch to make your changes in. Base it on `master` only if there is a compelling reason to change `master` between releases.

You will then need to follow the Zero-installation instructions `here <https://github.com/autokey/autokey/wiki/Installing#zero-installation-method>`_, but cloning your new branch instead. Note particularly the required installation of dependencies.

Making your changes
-------------------
After step 5 of the Zero-installation instructions make any desired changes to your local copy. Then continue with steps 6 onwards for running the project with your changes, repeating as necessary until you are satisfied with your update.

Please don't edit CHANGELOG.rst in your branch. The maintainers update it in
batches, in separate changelog PRs, from the titles and contents of the PRs that have been merged.

If you make any scripting API changes please be sure to run `python3 extractDoc.py` to regenerate the autocompletion text files used by both Qt and GTK (and add the changes to your commit!). This script only produces the editor autocompletion files. It does not generate the published documentation.

The published user and API documentation lives in the separate `autokey.github.io <https://github.com/autokey/autokey.github.io>`_ repository and is rebuilt by the maintainers, so please don't edit it as part of a code PR. If you have ideas for the documentation, open an issue or discussion thread, or add tips to the wiki.

Once you are done, push the changes back into your github personal fork.

Performing tests
----------------
Tests must pass before you submit a PR. At a minimum this means running the automated tests in your local copy.

Install `tox` through `pip` or `python-tox` through your package manager.
Tox will install pytest and PyHamcrest in its virtualenv when run, so you do not need to install them yourself.

Running the tests is simple: Run `tox`.
Running individual test files or folders, or using pytest arguments, can be
done with `tox -- tests/[test file] [--opt]`.

Lint the project (using flake8) with `tox -e lint`

Test coverage reports can be generated with
`tox -e clean,coverage,report`

The `tests` directory on `master` belongs to the old 0.96.x code and is deprecated, so run the tests from the `develop` branch.

To run the automated tests before every push, you can optionally add the following lines to the file `.git/hooks/pre-push`:

.. code:: sh

    #!/bin/sh
    tox
    exit $?

This will abort a push to your fork if any tests fail.

Automated and manual tests can be run locally, but they should also be run on fresh VMs, as described in VM_TESTING.md at the root of this repository, to check that local environmental quirks don't obscure build issues.
VM_TESTING.md also explains how to set up virtual machines covering AutoKey's
X11, GNOME/Wayland, and KDE Plasma/Wayland targets, and how to run both
the automated (`tests/vm_checklist/checklist.py`) and manual
(`tests/manual/`) checks against them.

See MANUAL_TESTING.rst for the manual verification checklist (in addition to the manual tests described in VM_TESTING.md) required for
PRs that change AutoKey's runtime behavior.

Additional test scenarios are welcome. Please contribute a PR to MANUAL_TESTING.rst if you know of a case it should cover.

Make a pull request
-------------------
Once you are done with testing, and your changes are in your fork, you can make a pull request to merge changes in your new branch back into the target branch of autokey (usually `develop`)

GitHub Actions are used to run tests on pull requests to `master` and
`develop` branches.

Tagged releases merged into `develop`, `beta` and `master` will automatically be built.

Optional: Install your modified version
---------------------------------------
It may be convenient to change your `pip` installation of autokey to use the source folder. `cd` to your `autokey` source folder and install with `pip3 install -e .`. This means the pip scripts installed in your `PATH` will run any changes you make to the source.

Reviewing and merging
---------------------
Before merging a PR that changes AutoKey's runtime behavior, verify it
by actually running the affected code path, ideally comparing behavior
across `master`, `develop`, and the PR branch, rather than relying on
code review alone. Purely cosmetic changes (comments, dead code, debug
output, formatting) don't need this level of verification.

Don't merge a PR while another maintainer has an open, unresolved concern
on it without checking with them first. Either resolve the concern
together, or get their explicit agreement to proceed anyway.

Program Structure
=================

Entry points to autokey are through the various UIs, which implement AutokeyApplication.
AutokeyApplication starts the autokey service and file monitor when it initialises.

The autokey service starts a new IoMediator, ScriptRunner and PhraseRunner.

If another autokey process is running, the application tries to show its config window then exit.
This is done by a lock file containing the original process's PID, and checking that that PID's command contains "autokey"

Communication between autokey and autokey-run is done via DBus.
AutokeyApplication registers itself with DBus for this.

`interface.py` handles communication with X. This includes grabbing hotkeys and sending keypresses.
It also handles a lot of clipboard mechanics.

https://github.com/autokey/autokey/issues/255 contains a good explanation of how sending text works.

Creating and modifying phrases and hotkeys is done through the ConfigManager.

For a detailed walkthrough of how phrases work, see `this comment <https://github.com/autokey/autokey/issues/334#issuecomment-564203873>`_


Autocomplete in the text Editors
--------------------------------
Ironically, Qt API autocomplete is super easy to implement but macro/phrase autocomplete appears to be relatively complex.

Gtk Autocomplete is a bit different but I think I've handled it in a pretty good way here.

Both autocomplete implementations are designed to use the output of the extractDoc.py script, this uses the `ast` python module to read in and parse the scripting api and the currently available macros.
Developers should be aware of exactly where all that information gets pulled from;
- args come straight from `ast`` and removes `self` if it's present. 
- It pulls the "comment" from the first line of the DocString, so this should be a short and concise description of the method.

For Macros (currently GTK Autocomplete only):
- uses the ID, TITLE and ARGS values to generate the lines
- the was the translation function is used needs to be consistent because it changes the AST, just make any new macros look like the old ones. 


For the GTK autocomplete it's sort of custom handling to read in the information for autocompletion, it requires an entire class, Qt interface uses QScintilla text editor which makes it pretty easy.


Qt Autocomplete
^^^^^^^^^^^^^^^
API Autocomplete happens by using the `QSci.QsciAPIs`, this just reads in the content of the api.txt file.

At this time it doesn't seem like there is a super easy way to add autocomplete to the phrase page, it appears to use a QTextEdit widget, and from what I've read/seen online there is not a super easy way to add autocomplete to that. PRs welcome!


GTK Autocomplete
^^^^^^^^^^^^^^^^
API Autocomplete reads in the content of the `lib/autokey/gtkui/data/api.csv`, where column 0 is the API call and column 1 is the description. 

Uses the same class for Macro autocomplete, makes the logic a bit tricky, may be worth separating them to be simpler to read. PRs welcome.
