# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import typing

qt_version = ...  # type: typing.List[str]
rcc_version = ...  # type: int
qt_resource_data = ...  # type: bytes
qt_resource_name = ...  # type: bytes
qt_resource_struct = ...  # type: bytes

def qCleanupResources() -> None: ...
def qInitResources() -> None: ...
