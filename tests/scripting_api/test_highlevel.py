# Copyright (C) 2026 AutoKey contributors

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

import struct

import pytest
from hamcrest import *

from autokey.scripting.highlevel import get_png_dim


def write_png_header(path, width, height):
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\r"
        + b"IHDR"
        + struct.pack("!II", width, height)
        + b"\x08\x02\x00\x00\x00"
    )


def test_get_png_dim_reads_png_dimensions(tmp_path):
    png_file = tmp_path / "image.png"
    write_png_header(png_file, 640, 480)

    assert_that(get_png_dim(str(png_file)), is_(equal_to((640, 480))))


def test_get_png_dim_rejects_non_png_file(tmp_path):
    text_file = tmp_path / "not-image.txt"
    text_file.write_text("not a png")

    with pytest.raises(Exception, match="not PNG"):
        get_png_dim(str(text_file))
