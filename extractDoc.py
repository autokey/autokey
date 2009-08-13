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

import sys, inspect
sys.path.append("./src/lib")
import scripting


if __name__ == "__main__":
    
    outFile = open("src/lib/ui/data/api.txt", "w")
    
    for name, attrib in inspect.getmembers(scripting):
        
        if inspect.isclass(attrib) and not name.startswith("_"):
            for name, attrib in inspect.getmembers(attrib):
                if inspect.ismethod(attrib) and not name.startswith("_"):
                    doc = attrib.__doc__
                    lines = doc.split('\n')
                    apiLine = lines[3].strip()
                    docLine = lines[1].strip()
                    outFile.write(apiLine[9:-1] + " " + docLine +  '\n')
            
    outFile.close()