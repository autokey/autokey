## Use the AutoKey beta with Pip in Ubuntu or Kubuntu

### Table of Contents
* [Remove the current version of AutoKey](#remove-the-current-version-of-autokey)
* [Install Pip](#install-pip)
* [Install AutoKey beta](#install-autokey-beta)
* [Run AutoKey beta](#run-autokey-beta)
  * [Run AutoKey beta from its directory](#run-autokey-beta-from-its-directory)
  * [Run AutoKey beta from any directory](#run-autokey-beta-from-any-directory)
  * [Make a shortcut](#make-a-shortcut)
  * [Add AutoKey beta to your path permanently so you can run it from anywhere without specirying a path](#add-autokey-beta-to-your-path-permanently-so-you-can-run-it-from-anywhere-without-specifying-a-path)
  * [Add AutoKey beta to your path temporarily so you can run it from anywhere without specifying a path](#add-autokey-beta-to-your-path-temporarily-so-you-can-run-it-from-anywhere-without-specifying-a-path)
* [Upgrade AutoKey beta to the latest version](#upgrade-autokey-beta-to-the-latest-version)
* [Uninstall AutoKey beta](#uninstall-autokey-beta)
* [Having trouble?](#having-trouble)

### Remove the current version of AutoKey
1. Quit AutoKey.
2. Verify that the AutoKey icon is not present in your system tray.
3. Type this command into a terminal window to check if the autokey process is still running: ```pgrep -c autokey```
4. If you get any number other than a zero in response to the previous command, type ```pkill autokey``` into a terminal window and return to step 3. Otherwise, go to the next step.
5. 🟥 **Important:** Back up your ```~/.config/autokey``` directory if you wish to save existing scripts and phrases. These files aren't normally touched, but upgrading AutoKey may alter the configuration in non-backwards-compatible ways,making it impossible for you to revert to the previous installation.
6. Type this command into  a terminal window in any directory to uninstall the existing copy of AutoKey and remove its dependencies: ```sudo apt-get autoremove autokey```
7. Type this command into a terminal window in any directory to remove the residual **AutoKey auytokey-common** configuration files: ```sudo apt-get remove --purge autokey```

### Install Pip
1. Type this command into a terminal window in any directory to install Pip: ```sudo apt install python3-pip```

### Install AutoKey beta
1. Type this command into the terminal window in any directory to use Pip to install AutoKey beta and ignore the warning about the **autokey-gtk** and **autokey-qt** scripts not being on your PATH: ```pip install --user --pre autokey```

### Run AutoKey beta
You can run AutoKey beta in a variaty of ways. Pick one of these:

#### Run AutoKey beta from its directory
1. Change to the .local/bin directory: ```cd ~/.local/bin```
2. Choose one of these commands to launch AutoKey
 * Launch AutoKey GTK without opening the main window: ```./autokey-gtk```
 * Launch AutoKey GTK with the main window open: ```./autokey-gtk -c```
 * Launch AutoKey Qt without opening the main window: ```./autokey-qt```
 * Launch AutoKey Qt with the main window open: ```./autokey-qt -c```

#### Run AutoKey beta from any directory
Run AutoKey from any directory by providing its full path:
1. Open a terminal window in any directory.
2. Choose one of these commands to launch AutoKey:
 * Launch AutoKey GTK without opening the main window: ```bash ~/.local/bin/autokey-gtk```
 * launch AutoKey GTK with the main window open: ```bash ~/.local/bin/autokey-gtk -c```
 * Launch AutoKey Qt without opening the main window: ```bash ~/.local/bin/autokey-qt```
 * launch AutoKey Qt with the main window open: ```bash ~/.local/bin/autokey-qt -c```

#### Make a shortcut
You can use the full path to AutoKey in the command for a shortcut on your desktop, in your menu, on your taskbar, in your panel, etc.
1. Pick any of these:
 * Use this command in a shortcut to launch AutoKey GTK with the main window closed: ```~/.local/bin/autokey-gtk```
 * Use this command in a shortcut to launch AutoKey GTK with the main window open: ```~/.local/bin/autokey-gtk -c```
 * Use this command in a shortcut to launch AutoKey Qt with the main window closed: ```~/.local/bin/autokey-qt```
 * Use this command in a shortcut to launch AutoKey Qt with the main window open: ```~/.local/bin/autokey-qt -c```

#### Add AutoKey beta to your path permanently so you can run it from anywhere without specifying a path
🟥 **Important:** _This is not recommended because of security reasons and to prevent possible conflicts, but it can be done and if you've researched it, are aware of the possible risks, and are comfortable with it, it's an option._

You can add AutoKey to your path permanently so you can run it from anywhere without having to specify a path. This adds the .local/bin directory to your path:
1. Open your ```~/.bashrc``` file in a text editor.
2. Add this line to the bottom of the file: ```export PATH="$HOME/.local/bin:$PATH"```
3. Save the file.
4. Close the file.

#### Add AutoKey beta to your path temporarily so you can run it from anywhere without specifying a path
🟥 **Important:** _This is not recommended because of security reasons and to prevent possible conflicts, but it can be done and if you've researched it, are aware of the possible risks, and are comfortable with it, it's an option._

You can add AutoKey to your path so you can run it from anywhere without having to specify a path. This temporarily adds the ```.local/bin``` directory to your path and reverts at the next log-in:
1. Type this command into a terminal windiw in any directory and press the Enter key: ```export PATH="$HOME/.local/bin:$PATH"```

### Upgrade AutoKey beta to the latest version
1. Check if your version of the AutoKey beta is up-to-date:
 1. Type one of these commands into a terminal window in any directory to check which version of the beta you are currently running: ```~/.local/bin/autokey-gtk --version``` or ```~/.local/bin/autokey-qt --version```
 2. Visit the [https://github.com/autokey/autokey/releases/](https://github.com/autokey/autokey/releases/) page to see the current beta version.
2. If the latest release version is higher than your installed copy, type this command into a terminal window in any directory to upgrade AutoKey: ```pip install --user --pre --upgrade autokey```

If you'd like to be notified of beta releases automatically, choose **Notifications** from the **Settings** menu after clicking on your avatar in your GitHub account and customize those settings.

### Uninstall AutoKey beta
1. Type this command into a terminal window in any directory to uninstall AutoKey: ```pip uninstall autokey```
2. You may need to clean up any residual files that are left behind in the autokey directory: ```rm ~/.local/bin/autokey*```
3. If you've created any shortcuts in your menu, on your desktop, tasbar, panel, etc., you'll want to remove those as well.

### Having trouble?
* Get information on Pip dependencies, etc., here: [https://github.com/autokey/autokey/wiki/Installing#pip-installation](https://github.com/autokey/autokey/wiki/Installing#pip-installation)
* See the Pip man page here: [http://manpages.ubuntu.com/manpages/bionic/man1/pip.1.html](http://manpages.ubuntu.com/manpages/bionic/man1/pip.1.html)
* If you can't run the Qt version of AutoKey, please use the GTK version and consider contributing your information to AutoKey issue [#414](https://github.com/autokey/autokey/issues/414).
