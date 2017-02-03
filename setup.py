# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
import autokey.common as R

try:
    from setuptools import setup
except ImportError:
    print("Autokey needs setuptools in order to build. Install it with your package"
          "manager (python-setuptools) or via pip (pip install setuptools)")
    sys.exit(1)

if sys.version_info < (3,5,0):
    print("Autokey requires Python 3.5 or later. You are using %s " % (".".join(map(str, sys.version_info[:3]))))
    sys.exit(1)

setup(
    name='autokey',
    version=R.VERSION,
    description='AutoKey (Python 3)',
    author=R.AUTHOR,
    author_email=R.AUTHOR_EMAIL,
    maintainer=R.MAINTAINER,
    maintainer_email=R.MAINTAINER_EMAIL,
    url='https://github.com/autokey-py3/autokey',
    license='GPLv3',
    packages=['autokey', 'autokey.gtkui', 'autokey.qtui'],
    package_dir={'': 'lib'},
    package_data={'autokey.qtui': ['data/*'],
                  'autokey.gtkui': ['data/*']},
    data_files=[('share/icons/hicolor/scalable/apps',
                 ['config/autokey.svg',
                  'config/autokey.png',
                  'config/autokey-status.svg',
                  'config/autokey-status-dark.svg',
                  'config/autokey-status-error.svg']),
                ('share/icons/Humanity/scalable/apps',
                 ['config/Humanity/autokey-status.svg',
                  'config/Humanity/autokey-status-error.svg']),
                ('share/icons/ubuntu-mono-dark/apps/48',
                 ['config/ubuntu-mono-dark/autokey-status.svg',
                  'config/ubuntu-mono-dark/autokey-status-error.svg']),
                ('share/icons/ubuntu-mono-light/apps/48',
                 ['config/ubuntu-mono-light/autokey-status.svg',
                  'config/ubuntu-mono-light/autokey-status-error.svg']),
                ('share/applications',
                 ['config/autokey-qt.desktop',
                  'config/autokey-gtk.desktop']),
                ('share/man/man1/',
                 ['doc/man/autokey-qt.1',
                  'doc/man/autokey-gtk.1',
                  'doc/man/autokey-run.1']),
                ('share/kde4/apps/autokey',
                 ['config/autokeyui.rc'])
                ],
    entry_points = {
        'console_scripts': ['autokey-gtk=autokey.gtkui.__main__:main']
    },
    scripts=['autokey-qt', 'autokey-run', 'autokey-shell'],
    install_requires=['dbus-python', 'pyinotify', 'python3-xlib'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
    ],
)
