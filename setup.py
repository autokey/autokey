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
      version="0.71.2",
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
      packages=["autokey", "autokey.gtkui", "autokey.qtui"],
      package_data={"autokey.qtui" : ["data/*"],
                    "autokey.gtkui" : ["data/*"]},
      data_files=[("/usr/share/pixmaps", ["config/akicon.png", "config/akicon-status.png"]),
                  ("/usr/share/applications", ["config/autokey-qt.desktop", "config/autokey-gtk.desktop"]),
                  ('share/man/man1/', ['doc/man/autokey-qt.1', 'doc/man/autokey-gtk.1'])],
      scripts=['autokey-qt', 'autokey-gtk']
      #packages=["plugin"]
      )
