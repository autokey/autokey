# Ubuntu:

Install Prerequisites:

    apt-get install build-essential debhelper dpkg-dev

Build package from a tag

    git clone https://github.com/autokey/autokey
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
    rm ../autokey_0.93.10-1_source.ppa.upload
    dput ppa:troxor/autokey-testing ../autokey_0.93.10-1_source.changes