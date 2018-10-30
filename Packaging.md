# PyPI:

    % git checkout v0.95.4
    Note: checking out 'v0.95.4'.
    ...
    HEAD is now at c260a41 Release v0.95.4

    % python3 setup.py sdist bdist_wheel

    % twine upload --verbose --repository-url https://upload.pypi.org/legacy/ dist/*
    Enter your username: <your pypi username>
    Enter your password: 
    Uploading distributions to https://upload.pypi.org/legacy/
    Uploading autokey-0.95.4-py3-none-any.whl
    ...
    Uploading autokey-0.95.4.tar.gz
    ...




# Ubuntu:

http://packaging.ubuntu.com/html/packaging-new-software.html

Install Prerequisites:

    # Packaging dependencies
    sudo apt install build-essential debhelper dpkg-dev devscripts git

    # Build dependencies
    sudo apt install python3-all python3-setuptools

Build package from a tag

    export VERSION=v0.94.0
    git clone https://github.com/autokey/autokey
    cd autokey
    uscan -dd
    git checkout $VERSION
    dpkg-buildpackage -b

Updating PPA with latest version (for maintainers)

    # change things with either
    dch
    # or
    vim debian/changelog

    git commit; git push

    # tag release in github

    git checkout $VERSION

    # Build the package with Debian utils
    uscan -dd
    debuild -S
    dput ppa:troxor/autokey-testing ../autokey_${VERSION}-1_source.changes
    # test it then go live if it works
    rm ../autokey_${VERSION}-1_source.ppa.upload
    dput ppa:troxor/autokey-testing ../autokey_${VERSION}-1_source.changes

# Fedora:

FIXME