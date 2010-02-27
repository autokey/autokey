# -*- coding: utf-8 -*-

# Copyright (C) 2008 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from distutils.core import setup

setup(
      name="autokey",
      version="0.61.3", 
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
      packages=["autokey", "autokey.ui"],
      package_data={"autokey.ui" : ["data/gui.xml", "data/api.txt"]},
      data_files=[("/usr/share/pixmaps", ["config/akicon.png"]),
                  ("/usr/share/applications", ["config/autokey.desktop"])],
      scripts=['autokey']
      #packages=["plugin"]
      )
