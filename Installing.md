# Contents 

[Installation Options](#installation-options)

* [Package Manager Installation](#package-manager-installation)

  * [Debian and Derivatives](#debian-and-derivatives)
  * [Arch](#arch)
  * [Gentoo](#gentoo)
  
* [`pip` Installation](#pip-installation)

[Running AutoKey](#running-autokey)

## Installation Options

There are two versions of the Python3-based AutoKey

* `autokey-gtk` - for systems using a GTK-based desktop environment such as GNOME, MATE, Ubuntu Unity, etc.
* `autokey-qt` - for systems using a Qt-based desktop environment such as KDE Plasma, Lumina, etc.

AutoKey can be most easily installed using one of these two methods:

* package manager
* [`pip`][pip]

**NOTE:** Remove existing AutoKey installation before attempting these steps.

### Removing Existing AutoKey

1. Quit Autokey - verify the AutoKey icon is not present in your system tray
1. Backup your `~/.config/autokey` directory if you wish to save existing scripts and phrases
1. Uninstall the existing AutoKey

## Package Manager Installation

### Debian and Derivatives

This section applies to Debian and derivatives such as Ubuntu and Mint. These steps assume that you have Python version 3.5 or higher.

If you don't know what a PPA is you can learn about them [here][ppa].

    $ sudo add-apt-repository ppa:troxor/autokey
    $ sudo apt update
    $ sudo apt install autokey-gtk
  
**Note:** As of 10/2017, the PPA only supports Ubuntu 16.04 and derivatives.
If you are using another release of Ubuntu, then install using [`pip` Installation](#pip-installation).

### Arch

The GTK front end is available in the Arch User Repository ([AUR][aur]). The qt front end is not available in the AUR.

### Gentoo

Install AutoKey using the [layman][layman] package manager.

    layman -a y2kbadbug
    emerge --sync
    emerge -av autokey-py3

## `pip` Installation

If you are using a distribution other than those listed above or if you want to install AutoKey from GitHub you can use this [`pip`][pip] installation method.

This assumes you have Python version 3.5 or higher installed.

If `git` is not already installed, [install git][installgit].

If the Python3 version of `pip` is not already installed, install `pip` using these [instructions][installpip].

The following Python3 dependencies _should_ be automatically installed by the `pip` install script listed below. If the install fails, look at your error messages - you might need to manually install one or more of the dependencies.

**Dependencies:**

`autokey-gtk` version

* GObject Introspection
* PyGTK
* GtkSourceView
* libappindicator
* libdbus-glib-1-dev

`autokey-qt` version

* PyQt4
* PyKDE4

_Both_ versions need

* dbus-python 
* pyinotify
* python-xlib

See [Installing Dependencies for Debian](#Installing-debian-dependencies)

Install AutoKey from the [AutoKey GitHub repository][autorepo] for your user only:

    $ pip3 install --user git+https://github.com/autokey/autokey
    
AutoKey will be located in your user directory: `~/.local/bin/autokey`
  
## Running AutoKey

In order to run AutoKey, the installation directory must be added to your PATH shell environment variable. If you installed AutoKey with a package manager this was probably done for you automatically. Note: the installation directory will vary based on which distribution you are using. For example, on Ubuntu 16.04 it is `/usr/bin/autokey`.

You can run AutoKey by using your distribution's application launcher. For example, on Ubuntu, just click on the super-key and type `autokey`. The main application window should open and you should see the AutoKey "A" icon in your taskbar. You can right-click on the "A" icon to see some menu choices and to quit AutoKey.

If you installed AutoKey using `pip` or if the installation directory was not added to your `PATH`, you can set this temporarily (will revert at next login):

    $ PATH="$HOME/.local/bin:$PATH"

Or you can add it permanently by following these [directions][path].

Either way, once `$HOME/.local/bin` as used by the pip3 installation method (or whichever installation directory was used) is in your `PATH` you can run AutoKey by executing the applicable command for the version you wish to run:

    $ autokey-gtk
    $ autokey-qt
    
#Installing-debian-dependencies

(Under construction)

`apt install gir1.2-appindicator3-0.1`

November 2011
Original author, Keith W. Daniels
Edited by Joseph Pollock, troxor, and ersanchez

[aur]: https://aur.archlinux.org/packages/autokey-py3
[autorepo]: https://github.com/autokey/autokey
[installgit]: https://git-scm.com/download/linux
[installpip]: https://packaging.python.org/install_requirements_linux/#installing-pip-setuptools-wheel-with-linux-package-managers
[layman]: https://github.com/y2kbadbug/gentoo-overlay/tree/master/app-misc/autokey-py3
[path]: http://stackoverflow.com/questions/14637979/how-to-permanently-set-path-on-linux
[pip]: https://en.wikipedia.org/wiki/Pip_(package_manager)
[ppa]: https://askubuntu.com/a/4990
