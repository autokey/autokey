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

from distutils.core import setup

long_description = ''
try:
    with open('README.rst') as f:
        long_description = f.read()
except OSError: pass

setup(
      name="autokey-py3",
      version="0.90.4",
      author="Chris Dekter",
      author_email="cdekter@gmail.com",
      maintainer='GuoCi',
      maintainer_email='guociz@gmail.com',
      url='https://github.com/guoci/autokey-py3',
      # url="http://autokey.googlecode.com/",
      license="GPL v3",
      description="Python 3 port of AutoKey",
      long_description=long_description,
      #py_modules=["autokey", "configurationmanager", "expansionservice", "interface",
      #            "iomediator", "phrase", "phrasemenu", "ui"],
      package_dir={"autokey": "src/lib"},
      packages=["autokey", "autokey.gtkui", "autokey.qtui"],
      package_data={"autokey.qtui" : ["data/*"],
                    "autokey.gtkui" : ["data/*"]},
      data_files=[("share/icons/hicolor/scalable/apps", ["config/autokey.svg", "config/autokey.png", "config/autokey-status.svg", "config/autokey-status-dark.svg", "config/autokey-status-error.svg"]),
                ("share/icons/Humanity/scalable/apps", ["config/Humanity/autokey-status.svg", "config/Humanity/autokey-status-error.svg"]),
                ("share/icons/ubuntu-mono-dark/apps/48", ["config/ubuntu-mono-dark/autokey-status.svg", "config/ubuntu-mono-dark/autokey-status-error.svg"]),
                ("share/icons/ubuntu-mono-light/apps/48", ["config/ubuntu-mono-light/autokey-status.svg", "config/ubuntu-mono-light/autokey-status-error.svg"]),
                  ("share/applications", ["config/autokey-qt.desktop", "config/autokey-gtk.desktop"]),
                  ('share/man/man1/', ['doc/man/autokey-qt.1', 'doc/man/autokey-gtk.1', 'doc/man/autokey-run.1']),
                  ('share/kde4/apps/autokey' , ['config/autokeyui.rc'])],
      scripts=['autokey-qt', 'autokey-gtk', 'autokey-run'],
      classifiers = [
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3',
      ],
      #packages=["plugin"]
      )
