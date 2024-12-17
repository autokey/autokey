## Running unit tests

The unit test suite has two additional requirements:

*  [Pytest](https://github.com/pytest-dev/pytest) - [PyPi](https://pypi.org/project/pytest/)
*  [PyHamcrest](https://github.com/hamcrest/PyHamcrest/) - [PyPi](https://pypi.org/project/PyHamcrest/)

Running the test suite is integrated into `setup.py`. The tests can be run by executing `python3 setup.py test` from the repository root directory.

## Trying out a clone of AutoKey
You can try out the code by cloning it and testing it locally on your machine without having to install it. This is a great way to help the developers when they've created new features or fixed issues and would like feedback from users. It's also a great way to test out your own code if you'd like to do some AutoKey developing of your own.

1. Prepare your system before cloning:
   1. **Important** - Make sure that AutoKey is or was [installed](https://github.com/autokey/autokey/wiki/Installing) on your computer (from your distribution's package manager, etc.) so that you'll already have all of its dependencies.
   2. **Optional** - Configure **git** on your system:
      * Configure your git username by replacing **John** with your username: `git config --global user.name "John"`
      * Configure your git user email by replacing John Doe's email address with yours: `git config --global user.email "john.doe@example.com"`
      * Configure your editor as **nano** instead of the default of **vim**: `git config --global core.editor "nano"`
      * Configure your pushes to tracking so that they'll go wherever they're being automatically tracked to go: `git config push.default tracking`
2. Clone the repository:
   1. Open a terminal window on your computer in the directory in which you'd like to create the clone's subdirectory.
   2. Clone the repository with this command: `git clone https://github.com/autokey/autokey.git`
3. Run the clone:
   * Run the clone manually:
     1. Change to the **autokey** directory that you just created: `cd autokey`
     2. Change to the **/lib** directory: `cd lib`
     3. Run the AutoKey module in either **GTK** or **Qt** mode:
        * AutoKey GTK: `python3 -m autokey.gtkui`
        * AutoKey Qt: `python3 -m autokey.qtui`
   * Run the clone from anywhere by replacing the example `~/Desktop/autokey` path with the path to your clone:
     * AutoKey GTK: `cd ~/Desktop/autokey; cd lib; python3 -m autokey.gtkui`
     * AutoKey Qt: `cd ~/Desktop/autokey; cd lib; python3 -m autokey.qtui`
	 * Note that command-line options (like `-c` can be added to the end of any of those AutoKey commands.
4. When you're finished testing either of those clones, close AutoKey normally.
5. If you're finished with all of your testing and would like to get rid of the clone, delete the clone's directory. Otherwise, you can keep it and use these steps again for further testing another time.
