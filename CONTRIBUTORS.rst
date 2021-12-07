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
