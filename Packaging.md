This page explains how to package AutoKey.

These instructions assume that you use a git checkout of the AutoKey repository and your current working directory is at the repository top level. If you use a Source code archive (for example a ZIP archive download from the front page or from the individual release pages), as provided by GitHub, skip the parts that involve calling `git` in the instructions below.

# PyPI (for maintainers):

    % git checkout v0.95.7
    Note: checking out 'v0.95.7'.
    [snip git output]
    HEAD is now at dc5bc5f Release v0.95.7

    % python3 setup.py sdist bdist_wheel

    % twine upload --verbose --repository-url https://upload.pypi.org/legacy/ dist/*
    Enter your username: <your pypi username>
    Enter your password: <your pypi password>
    Uploading distributions to https://upload.pypi.org/legacy/
    Uploading autokey-0.95.7-py3-none-any.whl
    ...
    Uploading autokey-0.95.7.tar.gz
    ...


# Debian, Ubuntu and derivates:

http://packaging.ubuntu.com/html/packaging-new-software.html
## Building Debian packages locally

### Install Prerequisites (needed only once):

    # Packaging dependencies
    sudo apt install build-essential debhelper dpkg-dev devscripts git

    # Build dependencies
    sudo apt install python3-all python3-setuptools
    # Optional, but recommended. If you want to build an optimized Qt GUI build.
    sudo apt install pyqt5-dev-tools

### Build the packages from a tag

    VERSION=v0.95.7
    uscan -dd
    git checkout $VERSION
    dpkg-buildpackage -b

Running the last command will build the packages (and some auxiliary files) in _the parent directory_.
Also note that `dpkg-buildpackage` will want to GPG-sign the package using the credentials of the person who authored the last changelog entry. Because you (hopefully ;) ) don’t posses the maintainer’s private key, this signing will fail with an error message. This is harmless. If the failed signing is the only error message produced, the built packages are fully operational and can be installed using `dpkg`.

## Updating PPA with latest version (for maintainers)

    git checkout $VERSION

    # Build the package with Debian utils
    uscan -dd
    debuild -S
    dput <your PPA identifier> ../autokey_${VERSION}-1_source.changes
    # test it then go live if it works
    rm ../autokey_${VERSION}-1_source.ppa.upload
    dput <your PPA identifier> ../autokey_${VERSION}-1_source.changes

# Preparing a new release (for maintainers)
Before publishing a new release do:
- Draft a new Release on the GitHub page. You can use this unpublished draft to draft the new changelog of the to-be released verion
- Update version string in [`lib/autokey/common.py`](https://github.com/autokey/autokey/blob/master/lib/autokey/common.py)
- Update the [CHANGELOG.rst](https://github.com/autokey/autokey/blob/master/CHANGELOG.rst)
- Update the [Debian changelog](https://github.com/autokey/autokey/blob/master/debian/changelog)

To update the debian changelog, use the `dch` command line tool. Alternatively, use your favourite text editor. Beware that the debian changelog is VERY format sensitive. Even slightest deviations from the specifications (like indention with 3 instead of 2 whitespace characters) will cause the Packaging process to FAIL. You don’t want to publish a release which can’t be packaged automatically.

When finished, do:

    git add lib/autokey/common.py CHANGELOG.rst debian/changelog
    git commit
    # Provide a nice commit message, like `Release v.0.95.7`
    # DO NOT PUSH. First, verify that the Debian packaging works.
    # If not, fix the `debian/changelog` and merge the changelog fix into the last commit
    # Use git commit --amend to do so.
    git push 

When the changes are pushed, edit the release draft on the GitHub release page. Add the appropriate version tag to the last commit and Publish the release.
