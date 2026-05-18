import importlib.util
import struct
from pathlib import Path

import pytest


def _load_highlevel_module():
    repo_root = Path(__file__).parents[2]
    module_path = repo_root / "lib" / "autokey" / "scripting" / "highlevel.py"
    spec = importlib.util.spec_from_file_location("highlevel", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


get_png_dim = _load_highlevel_module().get_png_dim


def test_get_png_dim_returns_png_dimensions(tmp_path):
    png_path = tmp_path / "image.png"
    png_path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + (13).to_bytes(4, "big")
        + b"IHDR"
        + struct.pack("!II", 123, 456)
    )

    assert get_png_dim(str(png_path)) == (123, 456)


def test_get_png_dim_rejects_non_png(tmp_path):
    not_png_path = tmp_path / "image.txt"
    not_png_path.write_text("not a png")

    with pytest.raises(Exception, match="not PNG"):
        get_png_dim(str(not_png_path))
