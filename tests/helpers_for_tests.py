# Copyright (C) 2021 BlueDrink9

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

import os
from shutil import copy

def get_autokey_test_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)))

dummy_config_path =  get_autokey_test_dir() + "/dummy_files/dummy_config.json"

def make_dummy_config(tmp_path):
    config = tmp_path / "autokey.json"
    copy(dummy_config_path, config)
    return config

