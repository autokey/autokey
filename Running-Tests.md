## Running unit tests

The unit test suite has two additional requirements:

*  [Pytest](https://github.com/pytest-dev/pytest) - [PyPi](https://pypi.org/project/pytest/)
*  [PyHamcrest](https://github.com/hamcrest/PyHamcrest/) - [PyPi](https://pypi.org/project/PyHamcrest/)

Running the test suite is integrated into `setup.py`. The tests can be run by executing `python3 setup.py test` from the repository root directory.

## Trying out a clone of AutoKey
You can try out the code by cloning it and testing it locally on your machine without having to install it. This is a great way to help the developers when they've created new features or fixed issues and would like feedback from users. It's also a great way to test out your own code if you'd like to do some AutoKey developing of your own.

1. Prepare your system before cloning:
   1. **Optional** - Configure Git on your system:
      * Configure your git username by replacing **John** with your username: `git config --global user.name "John"`
      * Configure your git user email by replacing John Doe's email address with yours: `git config --global user.email "john.doe@example.com"`
      * Configure your editor as **nano** instead of the default of **vim**: `git config --global core.editor "nano"`
      * Configure your pushes to tracking so that they'll go wherever they're being tracked to go automatically based on your clone command: `git config push.default tracking`
   2. **Important** - Make sure that AutoKey is or was [installed](https://github.com/autokey/autokey/wiki/Installing) on your computer (from your distribution's package manager, etc.) so that you'll already have all of its dependencies.
2. Pick one of these to get a clone:
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
3. Change to the **autokey** directory that you just created: `cd autokey`
4. Update your clone so that you have the most current code from the repository (must be done in each branch):
   * Live dangerously:
     1. Pull the changes (fetch and merge them) from the remote repository to the current branch in your local repository: `git pull`
   * Be more cautious:
     1. Fetch the latest meta-data from the remote repository to your local repository (your invisible .git folder), but don't merge the changes into your local branch (leave your files alone): `git fetch`
     2. Display the log of fetched changes to see what changed:
        * Use this command if you configured pushes to **tracking** in step 1 above: `git log ...@{u}`
        * Use this command if you didn't configure pushes to **tracking** in step 1 above: `git log HEAD..@{u}`
        * *Note: You'll be using the **less** program to view the logs. Navigate with the arrow keys and quit by pressing the **q** key.*
     3. Display what will be changed if you were to merge the fetched changes into your current branch (replace REPO with the repository name and BRANCH with the name of the branch: `git diff REPO/BRANCH`
     4. Merge the fetched changes into the current branch in your local repository: `git merge`
5. Change to the **/lib** directory: `cd lib`
6. Run AutoKey in either **GTK** or **Qt** mode by running its module as an isolated executable:
   * GTK: `python3 -Im autokey.gtkui`
   * Qt: `python3 -Im autokey.qtui`
   
     *Note that command-line switches work when added to the end of either of those commands, so if, for example, you wanted to open the AutoKey main window on startup, you could add the **--configure** or **-c** command-line switch to the end of the command, as in the `python3 -Im autokey.gtkui -c` command or the `python3 -Im autokey.qtui -c` command.*
7. When you're finished testing either of those clones, close AutoKey normally.
8. If you're finished with all of your testing and would like to get rid of the clone, delete the clone's directory. Otherwise, you can keep it and use these steps again for further testing another time.
