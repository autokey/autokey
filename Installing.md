# Contents 

* [Installation Options](#installation-options)

* [Package Manager Installation](#package-manager-installation)

  * [Debian and Derivatives](#debian-and-derivatives)
  * [Arch](#arch-linux)
  * [Gentoo](#gentoo-linux)
  
* [`pip` Installation](#pip-installation)

* [Zero Installation Method](#zero-installation-method)

  * [Zero-installation Notes](#zero-installation-method-notes)

* [Dependencies](#Dependencies)

* [Running AutoKey](#running-autokey)

# Installation Options

There are two versions of the Python3-based AutoKey

* `autokey-gtk` - for systems using a GTK-based desktop environment such as GNOME, MATE, Ubuntu Unity, etc.
* `autokey-qt` - for systems using a Qt-based desktop environment such as KDE Plasma, Lumina, etc.

AutoKey can be most easily installed using one of these two methods:

* package manager
* [`pip`][pip]

**NOTE:** Remove existing AutoKey installation before attempting these steps.

## Removing Existing AutoKey

1. Quit Autokey - verify the AutoKey icon is not present in your system tray
1. Backup your `~/.config/autokey` directory if you wish to save existing scripts and phrases. These files are not touched normally, but upgrading AutoKey may alter the script or phrase configuration in non-backwards-compatible ways, thus may make reverting to the previous installation impossible.
1. Uninstall the existing AutoKey

# Package Manager Installation

## Debian and Derivatives

This section applies to Debian and derivatives such as Ubuntu and Mint. These steps assume that you have Python version 3.7 or higher.

AutoKey releases can be downloaded from [releases](https://github.com/autokey/autokey/releases/) page.

Either use the supplied Debian packages attached to the GitHub release, or build your own Debian packages.

Using the pre-built packages:\
Chose the GUI you want and then download the `autokey-common_${VERSION}_all.deb` package plus the chosen frontend package (`autokey-gtk_${VERSION}_all.deb` or `autokey-qt_${VERSION}_all.deb`) to a directory on your system.

Building your own packages is described on [this](https://github.com/autokey/autokey/wiki/Packaging) page.

After you obtained the Debian packages, open a terminal at the directory containing the packages and use the following commands to install the packages:

    VERSION="0.95.10"    # substitute with the version you downloaded
    sudo dpkg --install autokey-common_${VERSION}_all.deb autokey-gtk_${VERSION}_all.deb
    sudo apt --fix-broken install

In the case of `dpkg` complaining about missing dependencies, it is crucial to run `sudo apt --fix-broken install` afterwards. This will make sure that all dependencies are correctly installed. In case this does not fix the dependencies, please open an issue on the GitHub issue tracker.

For reference, missing dependencies manifest in error messages similar to:

    dpkg: dependency problems prevent configuration of autokey-common:
      autokey-common depends on python3-pyinotify; however:
      Package python3-pyinotify is not installed.

Both the `-common` and GUI package need to be installed at the same time and `dpkg` will get it right while `apt` might not.
If you prefer to use the QT front end, you can download and install that instead of (or in addition to) the GTK GUI.
The second command will install all the dependencies from the official repositories.

Since AutoKey is a Python3 application, it is largely independent of particular distribution releases and should work on most relatively fresh distributions. It is fine, as long as apt can resolve the dependencies.

## Arch Linux

Up to date packages for both the [GTK](https://aur.archlinux.org/packages/autokey-gtk) and [Qt](https://aur.archlinux.org/packages/autokey-qt) versions are available in the Arch User Repository.

If you wish to manually install AutoKey, use the dependencies specified in the AUR as a reference, for what has to be installed.

Errors with QT plugins may be solved by updating the QT plugin path. `export QT_PLUGIN_PATH=/usr/lib/qt/plugins`

## Gentoo Linux

This section is incomplete. Gentoo users are encouraged to update it.

2024-01-05: Update for GTK, autokey 0.96
(Can't say much about dependencies for QT, but the last 5 will be needed too probably.)

Going for a venv installation as it seems:
* easier to maintian longterm
* you can't screw up your python profile for this user also which might be important if the python version in gentoo changes
* avoid bugs in new python versions like https://github.com/autokey/autokey/issues/916
* It's much easier to create a new venv if needed ;).

1) Dependencies. Create a set in /etc/portage/sets/autokey-gtk.set:
* dev-cpp/gtksourceviewmm (for x11-libs/gtksourceview < 4)
* dev-libs/dbus-glib
* dev-libs/gobject-introspection
* dev-libs/libappindicator
* gnome-extra/zenity
* dev-python/dbus-python
* dev-python/pip
* media-gfx/imagemagick
* x11-misc/xautomation
* x11-misc/wmctrl
* dev-python/virtualenv

pyinotify and python-xlib should be installed by autokey automatically in venv. 

2) Install/update the above set: emerge --ask @autokey-gtk.set

3) Run as user:
* path_venv="/this/is/the/path/to/your/venv" (p. e. ~/autokey)`
* python -m venv "${path_venv}"
* virtualenv "${path_venv}" --system-site-packages
* . "${path_venv}/bin/activate"
* pip install autokey
* cd "${path_venv}/bin"
* ./autokey-gtk


# `pip` Installation

If you are using a distribution other than those listed above or if you want to install AutoKey from GitHub you can use this [`pip`][pip] installation method.

`pip3 install autokey`

Or to install a beta release: `pip3 install --pre autokey`

Step-by-step instructions for installing the beta from pip in Ubuntu or Kubuntu can be found [here](https://github.com/autokey/autokey/wiki/AutoKey-beta-from-pip-in-Ubuntu-or-Kubuntu).

This assumes you have Python version 3.7 or higher installed.

If `git` is not already installed, optionally [install git][installgit] to directly install from GitHub. Alternatively, you can perform the install from a snapshot archive, generated by GitHub. You can download such a ZIP archive containing the source code from the [GitHub release page](https://github.com/autokey/autokey/releases). Click on a release, then download one of the `Source code` archives and unpack it.

If the Python3 version of `pip` is not already installed, install `pip` using these [instructions][installpip].

The following Python3 dependencies need to be installed. If the install fails, look at your error messages - you might need to manually install one or more of the dependencies. Many dependencies are not specified in `setup.py`, so are not installed automatically.

Installing the dependencies from PyPI may be tricky and break your system in unexpected ways, so prefer to install the dependencies from your Distribution’s package manager whenever possible. For example, installing `dbus-python` from PyPI will _shadow_ your local `dbus-python` installation (even if installed later by your package manager), _including any plugins present in the system installation_. This may break software relying on the presence of those plugins, for example the HPLIP software.

## Zero-installation Method

AutoKey can be used directly from a cloned repository as long as you have all of its dependencies already on your system. This can be useful for trying out a new version without removing a current installation.

1. Open a terminal window.
2. Pick one of these actions to install all or most of AutoKey's dependencies if AutoKey isn't already installed on your system:
   * Install the [dependencies](#dependencies) for AutoKey manually.
   * Install AutoKey [from your package manager](#package-manager-installation).
3. Pick one of these commands to install the Python **packaging** module if it isn't already on your system:
   * Install it with **apt**:
     ```bash
     sudo apt install python3-packaging
     ```
   * Install it with **pip**:
     ```bash
     pip3 install packaging
     ```
4. Pick one of these commands to clone AutoKey:
   * Clone **a branch** (example: `develop`):
     ```bash
     git clone --branch develop --single-branch https://github.com/autokey/autokey.git
     ```
   * Clone **the repository**:
     ```bash
     git clone https://github.com/autokey/autokey.git
     ```
5. Open the `autokey` directory you just created:
   ```bash
   cd autokey
	 ```
6. Open the `lib` sub-directory:
   ```bash
   cd lib
   ```
7. Pick one of these commands to start the Autokey daemon:
   * Run the **GTK UI**:
     ```bash
     python3 -m autokey.gtkui
     ```
   * Run the **Qt UI**:
     ```bash
     python3 -m autokey.qtui
     ```
8. When you're finished, close AutoKey normally and close the terminal window.
9. Delete the cloned `autokey` directory if you will no longer need it.

### Zero-installation Method Notes

  * The **GTK UI** is likely to work best with Gnome. The **Qt UI** is likely to work best with KDE, but also works when configuring AutoKey using the scripting API.
  * Command-line switches are accepted with either of those commands just as they are in a regular installation. For example:
    * Run the GTK UI with its main window open on startup:
      ```bash
      python3 -m autokey.gtkui -c
      ```
    * Run the Qt UI in isolated mode with its main window open on startup:
      ```bash
      python3 -Im autokey.qtui -c
      ```

## Dependencies

AutoKey depends on (regardless of the used GUI):

Python 3.7

  * [dbus-python](https://www.freedesktop.org/wiki/Software/DBusBindings/#python) \[[PyPI](https://pypi.org/project/dbus-python/)\] - Install from your distribution’s repository. because installing from PyPI may break your system. Additionally, installing from PyPi requires a C compiler and the dbus C header files, because it will compile the C libraries locally at installation time. Spare your time and install dbus-python from your distribution’s repository instead.
  * [packaging](https://github.com/pypa/packaging) \[[PyPI](https://pypi.org/project/packaging/)\] - Install with pip or install the `python3-packaging` package from your distribution's repository instead. This package is needed when working with cloned copies of AutoKey.
  * [pyinotify](https://github.com/seb-m/pyinotify) \[[PyPI](https://pypi.org/project/pyinotify/)\]
  * [python-xlib](https://github.com/python-xlib/python-xlib) \[[PyPI](https://pypi.org/project/python-xlib/)\]
  * [wmctrl](http://tripie.sweb.cz/utils/wmctrl/) (CLI tool) - used for window manipulation functions available in the Scripting API.

The GTK GUI additionally depends on these packages:

|Package | Homepage | [PyPI (Python Package Index)](https://pypi.org/project/PyGObject/) link | Extra notes |
|---|---|---|---|
| GObject Introspection | https://gi.readthedocs.io/en/latest/index.html | https://pypi.org/project/PyGObject/ |
| GTK (≥ 3.0) |  | Not available | Loaded at runtime from system-provided C libraries by `GObjectIntrospection` |
| GtkSourceView | https://wiki.gnome.org/Projects/GtkSourceView | Not available | Loaded at runtime from system-provided C libraries by `GObjectIntrospection` |
| libappindicator |  | Not available | Loaded at runtime from system-provided C libraries by `GObjectIntrospection` |
| libdbus-1-dev |  |  |  |
| libdbus-glib-1-dev |  |  |  |
| `zenity` CLI tool | https://wiki.gnome.org/Projects/Zenity | Not available | this is used for the dialogue windows available in the Scripting API |

The Qt5-based GUI additionally depends on:

|Package | Homepage | [PyPI (Python Package Index)](https://pypi.org/project/PyGObject/) link| Extra notes |
|---|---|---|---|
| PyQt5 | https://www.riverbankcomputing.com/software/pyqt/intro | https://pypi.org/project/PyQt5/ | Prefer installing from your distribution. Check, if your installation source provides the _full_ PyQt5 package. Some sources, notably the Ubuntu repository have split PyQt5 up into multiple modules. If so, you need the following additional modules.|
| PyQt5 SVG module, if not bundled with the base installation |  | included in PyQt5 from PyPi | If you installed from the Ubuntu repositories, you additionally need `python3-pyqt5.qtsvg` |
| PyQt5-QScintilla2 module, if not bundled with the base installation |  | included in PyQt5 from PyPi | If you installed from the Ubuntu repositories, you additionally need `python3-pyqt5.qsci`. Arch-based distros may need `qscintilla-qt5` and `python-qscintilla-qt5` instead. |
| `kdialog` CLI tool | https://github.com/KDE/kdialog | Not available | this is used for the dialogue windows available in the Scripting API |
| `pyrcc5` CLI tool | | not available | Installation-time/build-time only optional, but recommended dependency. |

### Installing Dependencies for Debian

    # Needed for both GUIs:
    sudo apt install python3-dbus python3-packaging python3-pyinotify python3-xlib wmctrl
    # Needed for autokey-gtk:
    sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gtksource-3.0 gir1.2-appindicator3-0.1 gir1.2-glib-2.0 gir1.2-notify-0.7 zenity
    # Needed for autokey-qt:
    sudo apt install python3-pyqt5 python3-pyqt5.qsci python3-pyqt5.qtsvg kdialog
    # Recommended installation-time/build-time dependency, if installing using pip3 or prior to self-building Debian packages
    sudo apt install pyqt5-dev-tools

### Installing Dependencies for Arch Linux
The AUR package lists all packages needed with their respective Arch-specific names:
https://aur.archlinux.org/packages/autokey-common/

### Installing Dependencies from PyPI
TODO.

(Check out the PyPI links from the tables above.)

### Installing AutoKey
Install AutoKey from the [AutoKey GitHub repository][autorepo] for your user only:

    # Install git master. Should be stable and include additional bug fixes. If in doubt, use a specific release instead
    $ pip3 install --user git+https://github.com/autokey/autokey
    # Install a specific release: Replace the version with the latest release.
    $ pip3 install --user https://github.com/autokey/autokey/archive/v0.95.10.zip
    # Or install from a local copy (git checkout or extracted release ZIP archive):
    $ pip3 install --user /replace/with/path/to/extracted/autokey/release
    
AutoKey will be located in your user directory: `~/.local/bin/autokey`

If you run pip3 as root and omit the `--user` switch, AutoKey will be installed globally.

For versions > 0.96, you can install the Pypi dependencies for either of the UIs by specifying `[UI]` after the install name or URL (where "`UI`" is "`GTK`" or "`QT`". For example: `$ pip3 install --user ./autokey'[QT]'`
  
## Running AutoKey

In order to run AutoKey, the installation directory must be added to your PATH shell environment variable. If you installed AutoKey with a package manager or via pip3 as root, the launcher is placed in your PATH automatically. Note: the installation directory will vary based on which distribution you are using. For example, on Ubuntu 16.04 it is `/usr/bin/autokey`.

You can run AutoKey by using your distribution's application launcher. For example, on Ubuntu, just click on the super-key and type `autokey`. You should see the AutoKey _`A`_ icon in your taskbar. You can right-click on the "A" icon to see some menu choices and to quit AutoKey.

If you installed AutoKey using `pip` with the `--user` flag or if the installation directory was not added to your `PATH`, you can set this temporarily (will revert at next login):

    $ PATH="$HOME/.local/bin:$PATH"

Or you can add it permanently by following these [directions][path].

Either way, once `$HOME/.local/bin` as used by the pip3 installation method (or whichever installation directory was used) is in your `PATH` you can run AutoKey by executing the applicable command for the version you wish to run:

    $ autokey-gtk
    $ autokey-qt



November 2011
Original author, Keith W. Daniels
Edited by Joseph Pollock, troxor, ersanchez and Thomas Hess

[aur-gtk]: https://aur.archlinux.org/packages/autokey-gtk/
[aur-qt]: https://aur.archlinux.org/packages/autokey-qt/
[autorepo]: https://github.com/autokey/autokey
[installgit]: https://git-scm.com/download/linux
[installpip]: https://packaging.python.org/install_requirements_linux/#installing-pip-setuptools-wheel-with-linux-package-managers
[path]: http://stackoverflow.com/questions/14637979/how-to-permanently-set-path-on-linux
[pip]: https://en.wikipedia.org/wiki/Pip_(package_manager)
[ppa]: https://askubuntu.com/a/4990
