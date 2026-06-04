import importlib.util
import pathlib

import pytest


def load_highlevel_module():
    module_path = pathlib.Path(__file__).parents[1] / "lib" / "autokey" / "scripting" / "highlevel.py"
    spec = importlib.util.spec_from_file_location("highlevel", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_png_dim_reads_png_size(tmp_path):
    png_path = tmp_path / "pattern.png"
    png_path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x10"
        b"\x00\x00\x00 "
    )

    assert load_highlevel_module().get_png_dim(str(png_path)) == (16, 32)


def test_get_png_dim_rejects_non_png(tmp_path):
    text_path = tmp_path / "pattern.txt"
    text_path.write_text("not a png")

    with pytest.raises(Exception, match="not PNG"):
        load_highlevel_module().get_png_dim(str(text_path))
