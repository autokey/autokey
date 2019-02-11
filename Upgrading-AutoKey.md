# Upgrading AutoKey

If you have created your own phrases and scripts, you need to save them:
Make a full backup of $HOME/.config/autokey (including hidden files).
Then uninstall AutoKey.

If you are using Ubuntu 18.04 or a derivative, you can use our pre-built deb files.

All our current deb files are built for Ubuntu 18.04. If you are using a different distro, install using [pip](https://github.com/autokey/autokey/wiki/Installing#pip-installation).

AutoKey releases are available on our [Releases](https://github.com/autokey/autokey/releases/) page.

Select the one you want and then download the common and gtk and/or qt debs to a directory on your system

Change into that directory (in a terminal) then

To install it on a Debian-based system, *please* use the following:

    sudo dpkg --install autokey-common_VERSION_all.deb autokey-gtk_VERSION_all.deb

(substituting the version you downloaded for "VERSION".)

They need to be installed at the same time and dpkg will get it right while apt might not.

If you're using the QT front end, you can download and install that instead of (or in addition to) the GTK version.

### Note for users of 0.90.x and 0.91.x

These versions are over six years old and unmaintained, so please upgrade if at all possible.

In addition to many bug fixes, including getting mouse events to work again and much better support for multibyte character sets, our current version also adds Xautomation support which allows you to search the screen for an image and move the mouse cursor to it - making it possible to access all sorts of things that keyboard actions alone could not reach.

This version is based on Python3.x, so if you have any scripts which use Python syntax/features which changed from Python2.x, you will have to convert them. Most simple scripts should be unaffected by these changes. 
