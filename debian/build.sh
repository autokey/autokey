#!/bin/sh

[ -f debian/build_requirements.txt ] && \
  cat debian/build_requirements.txt | xargs sudo apt install -y

# create Gnome Shell extension pack
cd 'autokey-gnome-extension/46'
zip "../autokey-gnome-extension@autokey.shell-extension.zip" *
cd ../..

VERSION=$(git describe --tags --abbrev=0 --match "v*.*.*")
# Strip leading 'v' because that is invalid as a debian version number
DEBVERSION="${VERSION#?}"

export DEBEMAIL='dave@daveking.com'

uscan -dd
# Create fake changelog entry just to get the correct version number on the deb
#dch --newversion "$DEBVERSION" ""
dpkg-buildpackage -i --build=binary --unsigned-source

# # Update PPA. Requires more in-depth packaging.
# debuild -i -S
# dput "$PPA_Identifier" ../autokey_${VERSION}-1_source.changes


