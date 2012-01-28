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

setup(
      name="autokey",
      version="0.81.4",
      author="Chris Dekter",
      author_email="cdekter@gmail.com",
      url="http://autokey.googlecode.com/",
      license="GPL v3",
      description="Desktop automation utility",
      long_description="""AutoKey is a desktop automation utility for Linux and X11. It allows
the automation of virtually any task by responding to typed abbreviations and hotkeys. It 
offers a full-featured GUI that makes it highly accessible for novices, as well as a scripting 
interface offering the full flexibility and power of the Python language.""",
      #py_modules=["autokey", "configurationmanager", "expansionservice", "interface",
      #            "iomediator", "phrase", "phrasemenu", "ui"],
      package_dir={"autokey": "src/lib"},
      packages=["autokey", "autokey.gtkui"],
      package_data={"autokey.gtkui" : ["data/*"]},
      data_files=[("/usr/share/icons/hicolor/scalable/apps", ["config/autokey.png", "config/autokey-status.svg", "config/autokey-status-dark.svg", "config/autokey-status-error.svg"]),
                ("/usr/share/icons/Humanity/scalable/apps", ["config/Humanity/autokey-status.svg", "config/Humanity/autokey-status-error.svg"]),
                ("/usr/share/icons/ubuntu-mono-dark/scalable/apps", ["config/ubuntu-mono-dark/autokey-status.svg", "config/ubuntu-mono-dark/autokey-status-error.svg"]),
                ("/usr/share/icons/ubuntu-mono-light/scalable/apps", ["config/ubuntu-mono-light/autokey-status.svg", "config/ubuntu-mono-light/autokey-status-error.svg"]),
                  ("/usr/share/applications", ["config/autokey-gtk.desktop"]),
                  ('share/man/man1/', ['doc/man/autokey-gtk.1', 'doc/man/autokey-run.1'])],
      scripts=['autokey-gtk', 'autokey-run']
      #packages=["plugin"]
      )
