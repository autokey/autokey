# Ubuntu:

    apt-get install build-essential debhelper dpkg-dev
    git clone https://github.com/autokey-py3/autokey
    cd autokey
    uscan -dd
    git checkout v0.93.10
    dpkg-buildpackage -b

Updating PPA with latest version

    # change things...
    dch / vim debian/changelog
    git commit,push
    # tag release in github
    git checkout v0.93.10 or git fetch/rebase
    uscan -dd
    debuild -S
    dput ppa:troxor/autokey-testing ../autokey_0.93.10-1_source.changes
    # test it then go live if it works
    dput ppa:troxor/autokey-testing ../autokey_0.93.10-1_source.changes