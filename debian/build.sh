#!/bin/sh

[ -f debian/build_requirements.txt ] && \
  cat debian/build_requirements.txt | xargs sudo apt-get install -y

VERSION=$(python3 -c "from lib.autokey.common import VERSION; print(VERSION)" 2>/dev/null)
# Strip leading 'v' because that is invalid as a debian version number
DEBVERSION="${VERSION#?}"
uscan -dd
# Create fake changelog entry just to get the correct version number on the deb
dch --newversion "$DEBVERSION" ""
dpkg-buildpackage -i --build=binary --unsigned-source

# # Update PPA. Requires more in-depth packaging.
# debuild -i -S
# dput "$PPA_Identifier" ../autokey_${VERSION}-1_source.changes


