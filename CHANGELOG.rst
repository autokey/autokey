 =========
 Changelog
 =========
 
 Version Develop
 ============================
 
 PR #1076 Changes
 ----------------
 
 - Fixed the Python syntax errors that threw the exceptions that prevented the develop branch from running.  This includes fixing the three regex syntax errors mentioned in `#1075 <https://github.c[...]
 - Modified the error messages that display when AutoKey under Wayland cannot find a keyboard/mouse device to monitor.
 - Modified AutoKey under Wayland to support more than one keyboard and one mouse at a time.
 - Modified AutoKey under Wayland to support the "hot-plugging" of USB and Bluetooth keyboard/mouse devices.
 - Modified debug logging and error messages to provide additional useful information when problems occur.
 - Added a module that validates the run-time environment as AutoKey is starting up on a Wayland system.
 - Created the postinstall and preremove scripts that are needed for the Debian/Ubuntu and Fedora installation packages, DEBs and RPMs.
 - Adjusted the ``pip-requirements.txt`` file to account for missing dependencies.
 - Created a ``rpm-requirements.txt`` file for use on Fedora, which has different pre-install dependencies and package names from Debian/Ubuntu systems.  This is equivalent to the ``apt-requirement[...]
 - Implemented fixes for issues `#961 <https://github.com/autokey/autokey/issues/961>`__, `#1000 <https://github.com/autokey/autokey/issues/1000>`__, `#1052 <https://github.com/autokey/autokey/issu[...]
 - Added a new option to AutoKey that controls the "grabkey" messages that are sent to the log when debugging is enabled on an X11 system, i.e., when the ``-v`` or ``-l`` options are used.
 - Updated Debian build scripts.
  
 Important misc changes
 ----------------------
 - Bump action versions in pages.yml to satisfy part of issue #963.
 - Bump action versions in build.yml to satisfy part of issue #963.
 - Bump action versions in python-test.yml to satisfy part of issue #963.
 - Bump Python version in build.yml to satisfy part of issue #964.
 - Bump Python versions in python-test.yml to satisfy part of issue #964.
 - Bump Python versions in setup.cfg to satisfy issue #969.
 - Bump Python versions in setup.py to satisfy issue #970.
 - Bump to all GitHub-supported Python versions to satisfy issue #986.
 - Add `pyasyncore` dependency to `setup.py` for use in Python 3.12 to satisfy issues #946 and #964.
 - Add `libcairo2` dependency to apt-requirements.txt to satisfy runtime requirement.
 - Change all instances of **sudo apt** to **sudo apt-get**.
 - Update badges, formatting, wording, links, and information in the **README.rst** file.
 - Various updates to the **README.rst** file to satisfy issue #681.
 - Various updates to the **README.rst** file to satisfy #pullrequestreview-1336342159.
 - Update action versions in build.yaml to latest.
 - Update Qt/GTK "Run" button in interface to run on F5
 - Update two links in the **README.rst** file.
 - Updated `extractDoc.py`
 - Updated Qt autocomplete api.txt file (last updated in 2019)
 - Fix, update, and add content to the man pages.
 - Fix Qt reference and update the wording in reference to KDE and Qt in the **autokey-qt.1** man page.
 - Update the date and remove excess wording in the **autokey-gtk.1** and **autokey-qt.1** man pages.
 - Update the date in the **autokey-run.1** man page.
 - Add the "Environment" section to the .gitignore file.
 - Update the help menu, deprecating one entry, adding several entries, updating existing wording, and sorting the entries.
 - Update the logger by removing an unneeded space and making the **cutelog** reference match the new command-line switch for it in the help menu.
 - Remove special handling of ignoreCase and matchCase options in abbreviation settings dialogs, allowing phrases to trigger on any input case while matching input case in the output (see #588).
 - Update the GTK and Qt man pages.
 - Update date, formatting, and NAME section in the GTK and Qt man pages.
 - Fix typo: Replace all occurrences of "they key" with "the key" in the AutoKey documentation.
 - Bump the AutoKey version to 0.96.1 in the **autokey.spec** file to satisfy part of issue #227.
 - Fix erroneous `window.close` in place of `window.resize_move` in documentation
 - Adds GNOME Window Extension for interacting with Windows on x11/wayland
 - Fix typos in mouse documentation (**window** --> **screen**).
 - Bump AutoKey version to **0.97.0~beta0** in `debian/changelog`, `fedora/autokey.spec`, and `lib/autokey/common.py`.
 - Bump the VERSION to **0.97.0-beta.0** in `lib/autokey/common.py` for compliance with `PEP 440`_.
 
 
 Features
 ---------
 Create a GUI-free headless entrypoint to autokey, which can be run without GUI libraries and controlled purely via scripting API
 Added Gtk autocomplete for both scripts and phrases
 
 
 Allows the distinction between left and right modifier keys for ``[Key.CONTROL, Key.ALT, Key.SUPER, Key.SHIFT, Key.HYPER, Key.META]``.
 
 At this time you cannot "mix and match", IE if you have a ``Key.CONTROL`` and ``Key.ALT`` as the hotkeys it will check for;
 ``Key.LEFTCONTROL, Key.LEFTALT``
 and
 ``Key.RIGHTCONTROL, Key.RIGHTALT``
 
 But not for;
 ``Key.LEFTCONTROL, Key.RIGHTALT``
 ``Key.RIGHTCONTROL, Key.RIGHTALT``
 
 This is considered a breaking change, prior it would, in effect, check for all of those scenarios. 
 
 Currently the left/right modifiers GUI option is only accessible via the GTK interface, but they should be respected if you manually update your config files.
 
 Bug fixes
 ---------
 
 - Fix crash in qt macro recording window.
 - Fix fake keyboard events not being emitted in a timely manner in some cases
 - Upgrade the **develop** branch to satisfy issue #773.
 - Fix selection when cloning a phrase or script
 
 Other changes
 -------------
 - Rename the bug.yaml file to bug.yml.
 - Update the contents of the `bug.yml` file to make it identical with its counterpart on the **master** branch.
 - Add the `config.yml` file to the `/.github/ISSUE_TEMPLATE` directory to match `its counterpart`_ on the **master** branch.
 - Use raw-string format in `window.py` to handle invalid escape sequences.
 - Bump GitHub Action and Python versions.
 - Update white-space in `setup.cfg` for readability and consistency with other lines.
 - Update indentation in the **pytest** section of `setup.cfg` for readability and syntax-correctness.
 - Remove white-space from **addopts** lines in `setup.cfg` for readability.
 - Use distinct comment types in `setup.cfg` for maintainability.
 - Adjust blank lines in `tests/test_interface.py` for readability.
 - Mark the **test_application_runs_without_errors** function as being expected to fail under Wayland.
 - Sort some of the `setup.cfg` sections for readability and maintainability.
 - Clean up local test-build version and entries.
 - Update `setup.cfg` comments (fix typo, succinctness, punctuation).
 - Add Wayland-related test-handling to `test_interface.py`.
 - Handle Window import error on scripting tests in `lib/autokey/scripting/__init__.py`.
 - Clean up and expand test and IDE exclusions in the `.gitignore` file.
 - Enable **coverage** tests.
 - Add measurement and timeout and blame settings to `setup.cfg` for more robust testing.
 - Sort the packages in `apt-requirements.txt` alphabetically for easier comparison on changes.
 - Pin **PyGObject** version in `setup.cfg` to ensure cross-version harmony.
 - Update the dependencies in the `apt-requirements.txt` file.
 - Fix typos and formatting and wording in the ``_README.txt`` file.
 - Cherry-pick the the `bug.yml` file from **master** to get the update that added a referral question to the issue-report form.
 
 .. _its counterpart: https://github.com/autokey/autokey/blob/master/.github/ISSUE_TEMPLATE/config.yml
 .. _PEP 440: https://peps.python.org/pep-0440/
 
 Version 0.96.0-beta.9
 ============================
 
 Bug fixes
 ---------
 
 - Fix qt crashing when changing a hotkey
 
 Version 0.96.0-beta.8
 ============================
 
 Bug fixes
 ---------
 
 - Fix installation not copying predefined user files (fix #578)
 
 Version 0.96.0-beta.5
 ============================
 
 Bug fixes
 ---------
 - Fix clear button not unsetting hotkeys
 
 Version 0.96.0-beta.4
 ============================
 
 - Fix updating of sidecar files
 
 Version 0.96.0-beta.3
 ============================
 
 - Build debs and update pypi on new releases
 - Add `set_clipboard_image` methods for both Gtk and Qt. Takes a file path to an image to load into the clipboard.
 
 Version 0.96.0-beta.2
 ============================
 
 - Fix issue with pip installation reporting a missing module
 
 Version 0.96.0-beta.1
 ============================
 
 Important misc changes
 ----------------------
 
 - Script and phrase metadata are no longer stored as hidden dotfiles. Existing scripts should be automatically converted, but if switch back to versions prior to this one, you will need to copy o[...]
