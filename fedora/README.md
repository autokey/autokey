#  Building AutoKey for Fedora

## The autokey.spec file

This is used with the rpmbuild utility to generate AutoKey installation RPMs for Fedora.

I started with the spec file that is used for the official Fedora 40 build of AutoKey 0.96.0 and modified it to build the version of AutoKey with Wayland support from the "develop" branch.

## The mkpackage script file

This is a proof-of-concept script that manually builds installation RPMs for AutoKey on Fedora using the above autokey.spec and makes them available for installation from [Fedora COPR](https://docs.pagure.org/copr.copr/user_documentation.html).

This script is meant to be run on a local workstation, out of the source directory where it resides.  It gathers up the source code needed to build AutoKey and ships it off to the Fedora COPR build system where RPM packages are built and made available in the COPR repository.

As of this writing my COPR project builds RPMs for Fedora 40, 41, and rawhide.

## Installing the AutoKey packages from the Fedora COPR repository

To install the AutoKey packages from my Fedora COPR project, first enable the project's repository on your workstation:

```sudo dnf install dnf-plugins-core```
```sudo dnf copr enable dlk/autokey```

If you already have AutoKey 0.96.0 installed, just do an upgrade:

```sudo dnf upgrade```

If you don't already have AutoKey installed, do this instead:

```sudo dnf install autokey-gtk```

Alternately, if you prefer Qt-style user interfaces, you can install the ```autokey-qt``` package instead.

## The user configuration script

There are two manual steps that need to be done to make AutoKey work for each user under Wayland.  I have created a script called ```autokey-user-config``` which performs these steps.  Run it under your regular userid after the dnf installation described above is complete and you have logged off and back on.  The dnf installation process above will remind you to do this same thing as well.

This is a one-time only action, only required the first time you install a version of AutoKey that supports Wayland.