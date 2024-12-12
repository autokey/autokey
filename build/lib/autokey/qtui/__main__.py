# Copyright (C) 2011 Chris Dekter
# Copyright (C) 2018 Thomas Hess
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
import faulthandler

faulthandler.enable()

from PyQt5 import QtCore
from autokey.qtapp import Application

QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_X11InitThreads)

# remove WINDOWID environment variable so that zenity is not tied to the window from which it was launched.
try:
    del os.environ['WINDOWID']
except KeyError:
    pass

if __name__ == '__main__':
    # When invoked by the setup.py generated launcher, __name__ is set to "autokey.qtui.__main__", so
    # this is only executed if invoked directly from the source directory as "python3 -m [lib.]autokey.qtui"
    # The setup.py launcher directly calls Application() after importing
    Application()
