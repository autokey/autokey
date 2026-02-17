%{?python_enable_dependency_generator}
Name:		autokey
Version:	0.97.1
Release:	2%{?dist}
Summary:	Desktop automation utility


License:	GPLv3
URL:		https://github.com/dlk3/autokey-wayland
Source0:	https://github.com/dlk3/autokey-wayland/archive/v%{version}.tar.gz
Source1:	10-autokey.rules
Source2:	autokey-gnome-extension@autokey.shell-extension.zip

BuildArch:	noarch
BuildRequires:	python3-devel,python3-xlib,python3-inotify,python3-dbus,python3-qt5-devel,python3-pip,python3-setuptools


%description
AutoKey is a desktop automation utility for Linux and X11. It allows
the automation of virtually any task by responding to typed abbreviations
and hot keys. It offers a full-featured GUI that makes it highly
accessible for novices, as well as a scripting interface offering
the full flexibility and power of the Python language.

%package common
Summary:	Desktop automation utility - common data
Requires:	gnome-extensions-app
Requires:	python3-dbus
Requires:	python3-evdev
Requires:	python3-pyudev
Requires:	wmctrl
Requires:	ImageMagick
Requires:	xautomation
Provides:	autokey = %{version}-%{release}
%description common
This package contains the common data shared between the various front ends.

%post common
#  Change group ownership on /dev/uinput to permit non-root write access
if [ -e /dev/uinput ]; then
    cp /usr/share/autokey/uinput-udev-rule/* '/etc/udev/rules.d/'
    /usr/bin/udevadm control --reload
    /usr/bin/udevadm trigger --sysname-match='/devices/virtual/misc/uinput'
fi

if [ "$USER" = "root" ] && [ "$(logname)" != "root" ]; then
    #  Add the user to the "input" group membership
    usermod -a -G "input" "$(logname)"
    #  If Gnome is present, install the Gnome Shell extension
    gnome-extensions &>/dev/null
    if [ $? -ne 127 ]; then
        su -c 'gnome-extensions install --force /usr/share/autokey/gnome-shell-extension/autokey-gnome-extension@autokey.shell-extension.zip' $(logname)
    fi
else
    echo "*******************************************************************************"
    echo "*  If you plan to run AutoKey on a Wayland desktop, please enter the          *"
    echo "*  following commands to configure your userid to run AutoKey:                *"
    echo "*                                                                             *"
    echo "sudo usermod -a -G input \$(id -u -n)"
    echo "gnome-extension install --force /usr/share/autokey/gnome-shell-extension/autokey-gnome-extension@autokey.shell-extension.zip"
    echo "*                                                                             *"
    echo "*  You will need to log off and log back on so that these changes take        *"
    echo "*  effect before trying to run AutoKey.                                       *"
    echo "*******************************************************************************"
fi

%preun common
case "$1" in
    0)
        if [ "$(logname)" != "root" ]; then
            #  Remove the user from the "input" group membership
            usermod -r -G "input" "$(logname)"
            #  If Gnome is present, remove the Gnome Shell extension
            gnome-extensions &>/dev/null
            if [ $? -ne 127 ]; then
                su -c 'gnome-extensions uninstall autokey-gnome-extension@autokey' $(logname)
                rm -fr "/home/$(logname)/.local/share/gnome-shell/extensions/autokey-gnome-extension@autokey"
            fi
        fi

        #  Revert /dev/uinput to the default premissions
        if [ -e /dev/uinput ]; then
            rm -f '/etc/udev/rules.d/10-autokey.rules'
            /usr/bin/udevadm control --reload
            /usr/bin/udevadm trigger --sysname-match='/devices/virtual/misc/uinput'
        fi
    ;;
esac
exit 0

%package gtk
Summary:	AutoKey GTK+ front end
Requires:	gtksourceview3
Requires:	libappindicator-gtk3
Requires:	python3-gobject
Requires:	zenity
Requires:	autokey-common = %{version}-%{release}
Provides:	autokey = %{version}-%{release}
%description gtk
This package contains the GTK+ front end for autokey

%post gtk
update-alternatives --install /usr/bin/autokey autokey \
  /usr/bin/autokey-gtk 50 \
  --slave /usr/share/man/man1/autokey.1.gz autokey.1.gz  \
  /usr/share/man/man1/autokey-gtk.1.gz

%preun gtk
case "$1" in
    0)
        update-alternatives --remove autokey /usr/bin/autokey-gtk
    ;;
esac
exit 0

%package qt
Summary:	AutoKey QT front end
Requires:	python3-qscintilla-qt5
Requires:	python3-qt5
Requires:	autokey-common = %{version}-%{release}
Provides:	autokey = %{version}-%{release}
%description qt
This package contains the QT front end for autokey

%post qt
update-alternatives --install /usr/bin/autokey autokey \
  /usr/bin/autokey-qt 60 \
  --slave /usr/share/man/man1/autokey.1.gz autokey.1.gz  \
  /usr/share/man/man1/autokey-qt.1.gz

%preun qt
case "$1" in
    0)
        update-alternatives --remove autokey /usr/bin/autokey-qt
    ;;
esac
exit 0

%prep
%setup -q -n %{name}-%{version}
cp %{SOURCE1} 10-autokey.rules
cp %{SOURCE2} autokey-gnome-extension/autokey-gnome-extension@autokey.shell-extension.zip


%build
%{__python3} setup.py build

%install
rm -rf %{buildroot}
%{__python3} setup.py install -O1 --skip-build --root %{buildroot} --prefix %{_prefix}

# remove shebang from python libraries
for lib in $(find %{buildroot}%{python3_sitelib}/autokey/ -name "*.py"); do
 sed '/\/usr\/bin\/env/d' $lib > $lib.new &&
 touch -r $lib $lib.new &&
 mv $lib.new $lib
done

# Put udev rules and gnome-autokey-extension file into place in BUILDROOT
install -m 644 -D --target-dir=%{buildroot}%{_datadir}/autokey/uinput-udev-rule 10-autokey.rules
install -m 644 -D --target-dir=%{buildroot}%{_datadir}/autokey/gnome-shell-extension autokey-gnome-extension/autokey-gnome-extension@autokey.shell-extension.zip

# ensure pkg_resources is able to find the required python packages
# sed -i 's/python3-xlib/python-xlib/' %{buildroot}%{python3_sitelib}/%{name}-%{version}-py%{python3_version}.egg-info/requires.txt

%files common
%doc ACKNOWLEDGMENTS README.md CHANGELOG.md
%{python3_sitelib}/*
%exclude %{python3_sitelib}/autokey/gtkapp.py*
%exclude %{python3_sitelib}/autokey/gtkui/*
%exclude %{python3_sitelib}/autokey/qtapp.py*
%exclude %{python3_sitelib}/autokey/qtui/*
%{_datadir}/autokey
%{_datadir}/icons/*
%{_bindir}/autokey-headless
%{_bindir}/autokey-run
%{_bindir}/autokey-shell
%{_mandir}/man1/autokey-run.1*

%files gtk
%{_bindir}/autokey-gtk
%{python3_sitelib}/autokey/gtkapp.py*
%{python3_sitelib}/autokey/gtkui/*
%{_datadir}/applications/autokey-gtk.desktop
%{_mandir}/man1/autokey-gtk.1*

%files qt
%{_bindir}/autokey-qt
%{python3_sitelib}/autokey/qtapp.py*
%{python3_sitelib}/autokey/qtui/*
%{_datadir}/applications/autokey-qt.desktop
%{_mandir}/man1/autokey-qt.1*

%changelog
* Sun Feb 8 2026 David King <dave@daveking.com> - 0.97.1-1
- Updated installation process

* Mon Feb 2 2026 David King <dave@daveking.com> - 0.97.1-0
- Bug fixes
- Support for more than one keyboard and mouse

* Fri Dec 20 2024 David King <dave@daveking.com> - 0.97.0-0
- Beta test release with support for the Wayland desktop environment

* Mon Jan 22 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.96.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Fri Jan 19 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.96.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Wed Jul 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.96.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Fri Jun 16 2023 Python Maint <python-maint@redhat.com> - 0.96.0-2
- Rebuilt for Python 3.12

* Sat Apr 29 2023 Jonathan Wright <jonathan@almalinux.org> - 0.96.0-1
- Update to 0.96.0 rhbz#1771109

* Wed Jan 18 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.10-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Wed Jul 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.10-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Mon Jun 13 2022 Python Maint <python-maint@redhat.com> - 0.95.10-8
- Rebuilt for Python 3.11

* Wed Jan 19 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.10-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Wed Jul 21 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.10-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Fri Jun 04 2021 Python Maint <python-maint@redhat.com> - 0.95.10-5
- Rebuilt for Python 3.10

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.10-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Jul 27 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.10-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 0.95.10-2
- Rebuilt for Python 3.9

* Fri Feb 21 2020 Raghu Udiyar <raghusiddarth@gmail.com> - 0.95.10-1
- Update to latest bugfix 0.95.10
- Remove python3-qscintilla as its no longer built
- Add gtksourceview3 dependency explicitly

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.7-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 0.95.7-5
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 0.95.7-4
- Rebuilt for Python 3.8

* Wed Jul 24 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Sun May 12 2019 Raghu Udiyar <raghusiddarth@gmail.com> - 0.95.7-1
- Update to latest bugfix 0.95.7

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.95.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Thu Dec 27 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.95.4-2
- Enable python dependency generator

* Mon Dec 10 2018 Raghu Udiyar <raghusiddarth@gmail.com> - 0.95.4-1
- Fix missing qsci dependency for QT

* Mon Dec 10 2018 Raghu Udiyar <raghusiddarth@gmail.com> - 0.95.4
- Update to latest bugfix 0.95.4 to fix (#1646812)
- Remove qt5 requires (#1607903)

* Sun Dec 09 2018 Miro Hrončok <mhroncok@redhat.com> - 0.95.2-2
- Remove unused Python 2 pygtksourceview dependency

* Mon Jul 23 2018 Raghu Udiyar <raghusiddarth@gmail.com> - 0.95.2-1
- Update to latest 0.95.2 release (#1596426)

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.94.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 0.94.0-2
- Rebuilt for Python 3.7

* Tue May 01 2018 Raghu Udiyar <raghusiddarth@gmail.com> - 0.94.0-1
- Update to latest 0.94.0 and use python3 (#1567688)

* Wed Apr 04 2018 Kalev Lember <klember@redhat.com> - 0.90.4-14
- Add missing dependencies for autokey-gtk (#1520592)

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.90.4-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Sun Jan 07 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.90.4-12
- Remove obsolete scriptlets

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.90.4-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.90.4-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.90.4-9
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.90.4-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.90.4-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.90.4-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild


* Mon Sep 16 2013 Raghu Udiyar <raghusiddarth@gmail.com> - 0.90.4-5
- Updated pygtksourceview dependency to gtksourceview3

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.90.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.90.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.90.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu May 17 2012 Raghu Udiyar <raghusiddarth@gmail.com> 0.90.4-1
- Update to upstream 0.90-4 release
- Qt interface is back with major updates to both frontends
- Back to the old split package structure

* Tue Jan 10 2012 Matěj Cepl <mcepl@redhat.com> 0.81.4-1
- Upgrade to the latest upstream package.

* Tue Nov 22 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.81.0-2
- Add autokey-run files to the package

* Tue Nov 22 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.81.0-1
- Update to upstream 0.81.0 release
- Changelog : http://code.google.com/p/autokey/source/browse/trunk/debian/changelog?r=408

* Wed Oct 26 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.80.3-1
- Update to upstream 0.80.3 release
- Changelog : http://code.google.com/p/autokey/source/browse/trunk/debian/changelog?spec=svn379&r=379

* Sat Oct 8 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.80.2-1
- Update to upstream 0.80.2 release
- Qt interface deprecated and removed
- Change package structure and remove qt subpackage/files
- Updated application icon
- Full changelog : http://code.google.com/p/autokey/source/browse/trunk/debian/changelog?spec=svn376&r=376

* Thu Jul 21 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.3-4
- Update to upstream 0.71.3-2 release
- Source tarball now extracts to "autokey-version" instead of "build" directory
- The README file now explicitly mentions the licence
- Drop defattr from the spec since recent RPM makes it redundant

* Fri Jul 15 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.3-3
- Add build requirement for desktop-file-utils
- Require pygtksourceview for gtk frontend
- Require qscintilla-python for qt frontend

* Wed May 25 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.3-2
- Improve spec readability

* Tue Apr 19 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.3-1
- Update to upstream 0.71.3 release

* Sun Mar 13 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.2-6
- Add desktop-file-validate

* Sun Mar 06 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.2-5
- Remove Python-xlib dependency
- Add doc/scripting to docs

* Fri Mar 04 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.2-4
- Remove deprecated daemon, see : http://code.google.com/p/autokey/issues/detail?id=106

* Mon Feb 28 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.2-3
- Add script to remove shebang from python libraries
- Remove default start from initscript
- Add patch to use lockfile in initscript

* Wed Feb 02 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.2-2
- Add postun scriptlet to handle upgrades
- Set autokey service to start only in runlevel 5

* Sun Jan 30 2011 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.2-1
- Update to upstream 0.71.2 release
- Add COPYING file to docs
- Update init script to match upstream

* Sat Dec 18 2010 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.1-1
- Update to upstream 0.71.1 release

* Fri Oct 01 2010 Raghu Udiyar <raghusiddarth@gmail.com> 0.71.0-1
- Initial version of the package
