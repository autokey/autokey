# Ubuntu:

    apt-get install build-essential debhelper dpkg-dev
    git clone https://github.com/autokey-py3/autokey
    cd autokey
    uscan -dd
    git checkout v0.97.3  # or latest release 
    dpkg-buildpackage -b


    dch
    push
    tag
    uscan
    debuild -S
    dput