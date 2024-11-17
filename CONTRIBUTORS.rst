Contributing
============
When you want to contribute new features or fix things, you are free to take virtually any task you wish. Just open a PR for discussion and maintainers will try to answer any questions that arise. We suggest writing new features on top of develop.

Please add a line to CHANGELOG.rst when creating PRs

Please make sure tests pass before you submit PRs. To ensure this happens automatically, I recommend adding the following lines to the file `.git/hooks/pre-push`:

.. code:: sh

    remote="$1"
    url="$2"

    tox
    exit $?

This will abort the push if any tests fail.

It may also be convenient to change your `pip` installation of autokey to use the source folder. `cd` to your `autookey` source folder and install with `pip3 install -e .`. This means the pip scripts installed in your `PATH` will run any changes you make to the source.

GitHub Actions are used to run tests on pull requests to `master` and
`develop` branches.

Tagged releases merged into `develop`, `beta` and `master` will
automatically be built.

If you make any scripting API changes please be sure to run `python3 extractDoc.py` to regenerate the autocompletion text files used by both Qt and GTK. (and add the changes to your commit!)

Testing
=======
Running the tests is simple: Checkout `develop` (or v>0.96.0) and run `tox`
(`tox` must be installed).
Running individual test files or folders, or using pytest arguments, can be
done with `tox -- tests/[test file] [--opt]`.

Lint the project (using flake8) with `tox -e lint`


Test coverage reports can be generated with
`tox -e clean,coverage,report`


Testing requires tox, pytest and PyHamcrest as new test-time only
dependencies. Tox will install pytest and pyhamcrest in its virtualenv when
run, so you do not need to worry about it.  Tox itself does need manual
installation.  Install `tox` through `pip` or `python-tox` through your
package manager.

The current (0.95.x) `master` tests are deprecated and won’t work. They are still on Python 2 and nobody cared to update them throughout the years, not even the original developer. They test things long gone in the project code…
The old tests are scheduled to be replaced by a new suite in the `develop` branch, which will be merged as 0.96.0.

The current situation is a bit unfortunate: The new suite lives in the develop branch, which accumulates new features, but which can't be backported to master without introducing merge conflicts later on. So until develop gets merged in, you’d have to switch to develop to run the tests.

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

For a detailed walkthrough of how phrases work, see [this comment](https://github.com/autokey/autokey/issues/334#issuecomment-564203873)


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

Update workflows
================
1. **Update the project's action versions:**

   1. Open the workflow files in the `autokey/.github/workflows` directory on the **master** branch:

      * Open the ``pages.yml`` file.
      * Open the ``build.yml`` file.
      * Open the ``python-test.yml`` file.
   2. Check the action versions in **each** of those files:

      1. Do a search for **@** in the file.
      2. Find an action line that you're interested in (for example: **actions/cache@v2**).
      3. Open the `Actions section of the Github Marketplace <https://github.com/marketplace?category=&query=&type=actions&verification=>`_.
      4. Do a search for the name of the action (for example: **cache**) in the search-box near the top of the page.

         * If the action's name exists:
            1. Click on the action's name in the list of actions that show up in the search results (for example: `Cache <https://github.com/marketplace/actions/cache>`__).
            2. Check what that action's latest version is (for example: **3**).
            3. Compare that version with all instances of that action in the file (for example: **2**).
            4. If the versions are different, jot down the action name and its new version.
         * If the action's name doesn't exist:
            1. Open the `PyPi page <https://pypi.org>`_ and do a search for the action's name
            2. Compare its version with all instances of that action in the file.
            3. If the versions are different, jot down the action name and its new version.
   3. Update the files if the versions have changed:

      1. Create an `AutoKey issue <https://github.com/autokey/autokey/issues>`_ making it known that the action versions will be bumped.
      2. Edit the ``pages.yml`` file, updating it with the new action versions from your notes (our example **cache** version was different and would need to be updated).
      3. Commit the change with this title::

             Bump action versions in pages.yml.

      4. Edit the `build.yml` file, updating it with the new action versions from your notes (our example **cache** version was different and would need to be updated).
      5. Commit the change with this title::

             Bump action versions in build.yml.

      6. Edit the `python-test.yml` file, updating it with the new action versions from your notes (our example **cache** version was different and would need to be updated).
      7. Commit the change with this title::

             Bump action versions in python-test.yml.

   4. Update the CHANGELOG.rst file:

      1. Note the change to each of the files, referencing the related issue number in place of the underscores in the example::

         * Bump action versions in pages.yml to satisfy part of issue #___.
         * Bump action versions in build.yml to satisfy part of issue #___.
         * Bump action versions in python-test.yml to satisfy part of issue #___.

      2. Commit the change with this title::


             Update CHANGELOG.rst with bump to action versions in workflow files.

   5. Do a pull request with this title, referencing the related issue number in place of the underscores in the example::

          Bump Python versions in workflow files to satisfy issue #___.

2. **Update the project's Python versions:**

   1. Find out what the current minimum and maximum Python versions are:

      1. Get the **lowest** supported version of Python by finding the lowest version that's not red on python.org's `Status of Python Versions <https://devguide.python.org/versions/>`_ page and jot it down.
      2. Get the **highest** supported version of Python:

         1. Go to the `GitHub Actions Runner Images <https://github.com/actions/runner-images#available-images>`_ page.
         2. Scroll down to the **Available Images** section of the page.
         3. Click the **Included Software** link for the **most-recent** Ubuntu release (the top release listed) to open its page.
         4. Scroll down to the **Cached Tools** section.
         5. Scroll down to the **Python** section inside of that section.
         6. Jot down the current **highest** version of Python listed inside of that section.

   2. Open the relevant workflow files in the `autokey/.github/workflows` directory on the master branch:

      * Open the `build.yml` file.
      * Open the `python-test.yml` file.

   3. Do a search for **python-version: [** in each of the files. Note that the versions won't all be identical.
   4. Update the files if the versions have changed:

      1. Create an `AutoKey issue <https://github.com/autokey/autokey/issues>`_ making it known that the Python versions will be bumped.
      2. Update the `build.yml` file:

         1. Do a search for **python-version: [** in the file.
         2. Replace all instances of the outdated version with the **highest** supported version number.
         3. Commit the change with this title::

                Bump Python version in build.yml.

      3. Update the `python-test.yml` file:

         1. Do a search for **python-version: [** in the file.
         2. Replace all instances of the outdated versions with the **lowest** and **highest** supported versions using only major and minor version numbers (for example: `["3.7", "3.10"]`).
         3. Commit the change with this title::

                Bump Python versions in python-test.yml.
            
      4. Update the `CHANGELOG.rst` file:

         1. Note the change to each of the files and referencing the related issue number in place of the underscores in the example::
            
            - Bump action versions in pages.yml to satisfy part of issue #___.
            - Bump action versions in build.yml to satisfy part of issue #___.
            - Bump action versions in python-test.yml to satisfy part of issue #___.


         2. Commit the change with this title::

                Update CHANGELOG.rst with bump to Python versions in workflow files.
            
      5. Do a pull request with this title, referencing the related issue number in place of the underscores in the example::

             Bump Python versions in workflow files to satisfy issue #___.

* **Notes:**

  * The above steps assume that the work is being done on GitHub. If the work is done locally, multiple files can be edited in one commit.
  * The `Actions <https://github.com/autokey/autokey/actions>`_ section of the AutoKey project is used to manage our `workflows <https://github.com/autokey/autokey/tree/master/.github/workflows>`_, which are scripts on the **master** branch that GitHub can run to automate tasks.
  * We use actions in our `workflows <https://github.com/autokey/autokey/tree/master/.github/workflows>`_ to automate tasks when specific conditions are met (think of it kind of like GitHub's version of AutoKey).

    * The `pages.yml <https://github.com/autokey/autokey/blob/master/.github/workflows/pages.yml>`_ file contains actions that create AutoKey's legacy documentation pages.
    * The `python-test.yml <https://github.com/autokey/autokey/blob/master/.github/workflows/python-test.yml>`_ file contains actions that run tests (like the ones that run whenever pull requests are made).
    * The `build.yml <https://github.com/autokey/autokey/blob/master/.github/workflows/build.yml>`_ file contains actions that run when AutoKey is built.
  * Some of the actions in those scripts are from the collection of GitHub-provided and user-provided actions in the `GitHub Marketplace <https://github.com/marketplace>`_ and others are from the `Python Package Index <https://pypi.org>`_.
  * The scripts also specify the Python versions used by the AutoKey project for development, tests, and support. 
  * The range of Python versions is determined by choosing the **lowest** supported version on python.org's `Status of Python Versions <https://devguide.python.org/versions>`_ page and the **highest** supported version in the most recent **Ubuntu** release in the **Available Images** section of the `GitHub Actions Runner Images <https://github.com/actions/runner-images#available-images>`_ page.
  * Action and Python versions should be checked and updated regularly.
  * When creating a new AutoKey release, the `workflow <https://github.com/autokey/autokey/tree/master/.github/workflows>`_ files will need to be copied over to the branch that will be overwriting the **master** branch as part of the release process. The `pages.yml <https://github.com/autokey/autokey/blob/master/.github/workflows/pages.yml>`_ file can be found **only** on the **master** branch and the most recent copy of the `build.yml <https://github.com/autokey/autokey/blob/master/.github/workflows/build.yml>`_ and `python-test.yml <https://github.com/autokey/autokey/blob/master/.github/workflows/python-test.yml>`_ files can be found on the **master** branch.
