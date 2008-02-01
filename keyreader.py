#!/usr/bin/python

# $Id$

# keyreader.py -- populate abbreviations from file

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

import ConfigParser, os

user_folder = os.path.expanduser('~')
def get_abbr(file = user_folder + '/.abbr.ini'):
    parser = ConfigParser.ConfigParser()
    parser.readfp(open(file))
    return dict(parser.items('abbr'))
