#
# This file and all modifications and additions to the pristine
# package are under the same license as the package itself.
#

#define python macros for openSUSE < 112
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

Name:           autokey
Version:        0.82.0
Release:        1
License:        GPLv3
Summary:        Desktop automation utility
Url:            http://autokey.googlecode.com
Group:          System/X11/Utilities
Source:         %{name}_%{version}.tar.gz
BuildRequires:  python-base
BuildRequires:  update-desktop-files
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
%if 0%{?suse_version} > 1110
# This works on newer version
# on older version it dies misserably if used
BuildArch:      noarch
%endif

%description
AutoKey is a desktop automation utility for Linux and X11. It allows the
automation of virtually any task by responding to typed abbreviations
and hotkeys. It offers a full-featured GUI that makes it highly
accessible for novices, as well as a scripting interface offering the
full flexibility and power of the Python language.

%package common
License:        GPLv3
Summary:        Desktop automation utility -- Common Files
Group:          System/X11/Utilities
Requires:       python-simplejson
Requires:       python-pyinotify
Requires:       python-xlib
Requires:       wmctrl
Recommends:       %{name}-gtk
%py_requires

%description common
AutoKey is a desktop automation utility for Linux and X11. It allows the
automation of virtually any task by responding to typed abbreviations
and hotkeys. It offers a full-featured GUI that makes it highly
accessible for novices, as well as a scripting interface offering the
full flexibility and power of the Python language.

%package gtk
License:        GPLv3
Summary:        Desktop automation utility -- GTK+ Interface
Group:          System/X11/Utilities
Requires:       %{name}-common = %{version}
Requires:       python-gtk
Requires:       python-gtksourceview
Requires:       python-notify
Requires:       zenity
%py_requires

%description gtk
AutoKey is a desktop automation utility for Linux and X11. It allows the
automation of virtually any task by responding to typed abbreviations
and hotkeys. It offers a full-featured GUI that makes it highly
accessible for novices, as well as a scripting interface offering the
full flexibility and power of the Python language.

%package qt
License:        GPLv3
Summary:        Desktop automation utility -- KDE Interface
Group:          System/X11/Utilities
Requires:       %{name}-common = %{version}
Requires:       python-kde4
Requires:       python-qt4
Requires:       python-qscintilla2
Requires:       python-notify
%py_requires

%description qt
AutoKey is a desktop automation utility for Linux and X11. It allows the
automation of virtually any task by responding to typed abbreviations
and hotkeys. It offers a full-featured GUI that makes it highly
accessible for novices, as well as a scripting interface offering the
full flexibility and power of the Python language.

%prep
%setup -n %{name}_%{version}
find src/lib -name "*.py" -exec sed -i '/^#!\/usr\/bin\/env python$/d' {} ";"

%build
%{__python} setup.py build

%install
%{__python} setup.py install --prefix=%{_prefix} --root=%{buildroot}
%suse_update_desktop_file autokey-gtk DesktopSettings

%files common
%defattr(-,root,root)
%doc ACKNOWLEDGMENTS README
%dir %{python_sitelib}/autokey
%{python_sitelib}/autokey/*.py*
%exclude %{python_sitelib}/autokey/gtkapp.py*
%{python_sitelib}/%{name}-%{version}-py%{py_ver}.egg-info
%{_datadir}/icons/hicolor/scalable/apps/autokey-status*.svg
%{_datadir}/icons/hicolor/scalable/apps/autokey.png
%{_datadir}/icons/Humanity/scalable/apps/*.svg
%{_datadir}/icons/ubuntu-mono-dark/scalable/apps/*.svg
%{_datadir}/icons/ubuntu-mono-light/scalable/apps/*.svg
%{_bindir}/autokey-run
%{_mandir}/man1/autokey-run.1*

%files gtk
%defattr(-,root,root)
%{_bindir}/autokey-gtk
%{python_sitelib}/autokey/gtkapp.py*
%{python_sitelib}/autokey/gtkui/
%{_datadir}/applications/autokey-gtk.desktop
%{_datadir}/icons/hicolor/scalable/apps/autokey.svg
%{_mandir}/man1/autokey-gtk.1*

%files qt
%defattr(-,root,root)
%{_bindir}/autokey-qt
%{python_sitelib}/autokey/qtapp.py*
%{python_sitelib}/autokey/qtui/
%{_datadir}/applications/autokey-qt.desktop
%{_datadir}/icons/hicolor/scalable/apps/autokey.png
%{_mandir}/man1/autokey-qt.1*

%post common
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun common
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans common
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%changelog


