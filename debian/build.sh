#!/bin/sh

[ -f debian/build_requirements.txt ] && \
  cat debian/build_requirements.txt | xargs sudo apt-get install -y

VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); from lib.autokey.common import VERSION; print(VERSION)")

if [ -z "$VERSION" ]; then
    echo "FATAL: Could not extract VERSION from lib/autokey/common.py" >&2
    exit 1
fi

# Strip leading 'v' if present, safe no-op when absent
DEBVERSION="${VERSION#v}"
uscan -dd
# Create fake changelog entry just to get the correct version number on the deb
dch --newversion "$DEBVERSION-1" "Local build for testing"
dpkg-buildpackage -i --build=binary --unsigned-source

# # Update PPA. Requires more in-depth packaging.
# debuild -i -S
# dput "$PPA_Identifier" ../autokey_${VERSION}-1_source.changes


