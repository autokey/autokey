import importlib.util
import struct
from pathlib import Path

import pytest


HIGHLEVEL_PATH = Path(__file__).parents[2] / "lib" / "autokey" / "scripting" / "highlevel.py"
spec = importlib.util.spec_from_file_location("highlevel", HIGHLEVEL_PATH)
highlevel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(highlevel)


def test_get_png_dim_returns_dimensions(tmp_path):
    png_file = tmp_path / "sample.png"
    png_file.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + struct.pack("!I", 13)
        + b"IHDR"
        + struct.pack("!II", 640, 480)
    )

    assert highlevel.get_png_dim(str(png_file)) == (640, 480)


def test_get_png_dim_rejects_non_png(tmp_path):
    text_file = tmp_path / "sample.txt"
    text_file.write_text("not a png")

    with pytest.raises(Exception, match="not PNG"):
        highlevel.get_png_dim(str(text_file))
