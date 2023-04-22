## Running unit tests

The unit test suite has two additional requirements:

*  [Pytest](https://github.com/pytest-dev/pytest) - [PyPi](https://pypi.org/project/pytest/)
*  [PyHamcrest](https://github.com/hamcrest/PyHamcrest/) - [PyPi](https://pypi.org/project/PyHamcrest/)

Running the test suite is integrated into `setup.py`. The tests can be run by executing `python3 setup.py test` from the repository root directory.

## Trying out AutoKey with a clone
You can try out the code by cloning it and testing it locally on your machine without having to install it. This is a great way to help the developers when they've created new features or fixed issues and would like feedback from users. It's also a great way to test out your own code if you'd like to do some AutoKey developing of your own.

1. Open a clone's folder in a terminal window on your computer or, if you don't already have a clone, **first make sure that AutoKey is [installed](https://github.com/autokey/autokey/wiki/Installing) on your computer (from your distribution's package manager, etc.) so that you have all of its dependencies already**, and then pick one of these to get a clone:
   * **Clone a repository:**
     1. Open the repository's main GitHub page in your browser (note that this can be one of your repositories or a remote repository not owned by you).
     2. Click the **Code** button.
     3. Click the clipboard icon to the right of the HTTPS URL.
     4. Open a terminal window on your computer in the directory in which you'd like to create the clone's subdirectory.
     5. Enter this command, replacing the example URL with the fork's URL: `git clone https://github.com/foo/bar.git`
     6. Press the **Enter** key to create the clone in a new subdirectory named after the repository.
   * **Clone a repository branch:**
     1. Open the repository's main GitHub page in your browser (note that this can be one of your repositories or a remote repository not owned by you).
     2. Click the **Code** button.
     3. Click the clipboard icon to the right of the HTTPS URL.
     4. Open a terminal window on your computer in the directory in which you'd like to create the clone's subdirectory.
     5. Enter this command, replacing **mybranch** with the name of the branch you'd like to work on and replace the example URL with the fork's URL: `git clone --branch mybranch --single-branch https://github.com/foo/bar.git`
     6. Press the **Enter** key to create the clone in a new subdirectory named after the repository.
2. Update your clone so that you have the most current code from the repository by using this command inside of a terminal window in the clone's directory: `git fetch`
3. Change to the **/lib** directory: `cd lib`
4. Run AutoKey in either GTK or Qt mode by running its module as an executable:
   * GTK: `python3 -m autokey.gtkui`
   * Qt: `python3 -m autokey.qtui`
   *Note that command-line switches work when added to the end of either of those commands, so if, for example, you wanted to open the AutoKey main window on startup, you could add the **--configure** or **-c** command-line switch to the end of the command, like this: `python3 -m autokey.gtkui -c`*
5. When you're finished testing either of those clones, close AutoKey normally.
6. If you're finished with all of your testing and would like to get rid of the clone, delete the clone's directory. Otherwise, you can keep it and use these steps again for further testing another time.
