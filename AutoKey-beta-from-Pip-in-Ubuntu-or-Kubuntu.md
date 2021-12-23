## Use the AutoKey beta with Pip in Ubuntu or Kubuntu

### Table of Contents
* [Install AutoKey](#install-autokey)
* [Install Pip](#install-pip)
* [Install AutoKey beta](#install-autokey-beta)
* [Run AutoKey beta](#run-autokey-beta)
* [Optional: Add AutoKey beta to your path permanently so you can run it from anywhere without specirying a path](#optional-add-autokey-beta-to-your-path-permanently-so-you-can-run-it-from-anywhere-without-specifying-a-path)
* [Optional: Add AutoKey beta to your path temporarily so you can run it from anywhere without specifying a path](#optional-add-autokey-beta-to-your-path-temporarily-so-you-can-run-it-from-anywhere-without-specifying-a-path)
* [Upgrade AutoKey beta to the latest version](#upgrade-autokey-beta-to-the-latest-version)
* [Uninstall AutoKey beta](#uninstall-autokey-beta)
* [Having trouble installing the beta?](#having-trouble-installing-autokey-beta)

### Install AutoKey
The beta can coexist with your regular installation of AutoKey. In fact, adding the beta to a machine that already has AutoKey installed on it is a way to make sure the beta has all of its needed dependencies.

If you don't already have AutoKey installed:
1. Install the GTK version by typing this command in a terminal window in any directory:\
```sudo apt install autokey-gtk```
2. Install the Qt version by typing this command in a terminal window in any directory:\
```sudo apt install autokey-qt```

### Install Pip
1. Install Pip by typing this command in a terminal window in any directory:\
```sudo apt install python3-pip```

### Install AutoKey beta
1. Install both versions of the AutoKey beta at once by typing this command in a terminal window in any directory:\
```pip install --user --pre autokey```\
    _Note that you'll get a warning about the scripts not being on your PATH. This is because the beta doesn't affect your system settings._

### Run AutoKey beta
Since the beta doesn't create shortcuts that are automatically installed for you, you'll need to decide how you'd like to launch it. You can run it in a variety of ways.

Pick one of these:
* Run AutoKey beta from its directory:
  1. Change to the .local/bin directory:\
```cd ~/.local/bin```
  2. Choose one of these commands to launch AutoKey:
     * Launch AutoKey GTK without opening the main window:\
```./autokey-gtk```
     * Launch AutoKey GTK with the main window open:\
```./autokey-gtk -c```
     * Launch AutoKey Qt without opening the main window:\
```./autokey-qt```
     * Launch AutoKey Qt with the main window open:\
```./autokey-qt -c```
* Run AutoKey beta from any directory:
  1. Open a terminal window in any directory.
  2. Choose one of these commands to launch AutoKey:
     * Launch AutoKey GTK without opening the main window:\
```~/.local/bin/autokey-gtk```
     * launch AutoKey GTK with the main window open:\
```~/.local/bin/autokey-gtk -c```
     * Launch AutoKey Qt without opening the main window:\
```~/.local/bin/autokey-qt```
     * launch AutoKey Qt with the main window open:\
```~/.local/bin/autokey-qt -c```
* Run AutoKey from a shortcut:
  1. Create a shortcut on your desktop, in your menu, on your taskbar, in your panel, etc.
  2. Pick any of these:
     * Use this command in a shortcut to launch AutoKey GTK with the main window closed:\
```~/.local/bin/autokey-gtk```
     * Use this command in a shortcut to launch AutoKey GTK with the main window open:\
```~/.local/bin/autokey-gtk -c```
     * Use this command in a shortcut to launch AutoKey Qt with the main window closed:\
```~/.local/bin/autokey-qt```
     * Use this command in a shortcut to launch AutoKey Qt with the main window open:\
```~/.local/bin/autokey-qt -c```

### Optional: Add AutoKey beta to your path permanently so you can run it from anywhere without specifying a path
🟥 **Important:** _This is not recommended because of security reasons and to prevent possible conflicts, but it can be done and if you've researched it, are aware of the possible risks, and are comfortable with it, it's an option._

Add AutoKey to your path permanently so you can run it from anywhere without having to specify a path. This adds the ```.local/bin``` directory to your path:
1. Open your ```~/.bashrc``` file in a text editor.
2. Add this line to the bottom of the file:\
```export PATH="$HOME/.local/bin:$PATH"```
3. Save the file.
4. Close the file.

### Optional: Add AutoKey beta to your path temporarily so you can run it from anywhere without specifying a path
🟥 **Important:** _This is not recommended because of security reasons and to prevent possible conflicts, but it can be done and if you've researched it, are aware of the possible risks, and are comfortable with it, it's an option._

Add AutoKey to your path so you can run it from anywhere without having to specify a path. This temporarily adds the ```.local/bin``` directory to your path and reverts at the next log-in:
1. Type this command into a terminal windiw in any directory and press the Enter key:\
```export PATH="$HOME/.local/bin:$PATH"```

### Upgrade AutoKey beta to the latest version
1. Check if your version of the AutoKey beta is up-to-date:
 1. Type one of these commands into a terminal window in any directory to check which version of the beta you are currently running:\
```~/.local/bin/autokey-gtk --version```\
or:\
```~/.local/bin/autokey-qt --version```
 2. Visit the [https://github.com/autokey/autokey/releases/](https://github.com/autokey/autokey/releases/) page to see the current beta version.
2. If the latest release version is higher than your installed copy, type this command into a terminal window in any directory to upgrade AutoKey:\
```pip install --user --pre --upgrade autokey```

If you'd like to be notified of beta releases automatically, choose **Notifications** from the **Settings** menu after clicking on your avatar in your GitHub account and customize those settings.

### Uninstall AutoKey beta
1. Type this command into a terminal window in any directory to uninstall AutoKey:\
```pip uninstall autokey```
2. You may need to clean up any residual files that are left behind in the autokey directory:\
```rm ~/.local/bin/autokey*```
3. If you've created any shortcuts in your menu, on your desktop, tasbar, panel, etc., you'll want to remove those as well.

### Having trouble installing AutoKey beta?
* Get information on Pip dependencies, etc., here: [https://github.com/autokey/autokey/wiki/Installing#pip-installation](https://github.com/autokey/autokey/wiki/Installing#pip-installation)
* See the Pip man page here: [http://manpages.ubuntu.com/manpages/bionic/man1/pip.1.html](http://manpages.ubuntu.com/manpages/bionic/man1/pip.1.html)
