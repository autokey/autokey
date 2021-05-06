#!/bin/sh

[ -f debian/build_requirements.txt ] && \
  cat debian/build_requirements.txt | xargs sudo apt install -y

VERSION=$(git describe --tags --abbrev=0 --match "v*.*.*")
uscan -dd
# Create fake changelog entry just to get the correct version number on the deb
dch --newversion "$VERSION" ""
dpkg-buildpackage -i --build=binary --unsigned-source

# # Update PPA. Requires more in-depth packaging.
# debuild -i -S
# dput "$PPA_Identifier" ../autokey_${VERSION}-1_source.changes


