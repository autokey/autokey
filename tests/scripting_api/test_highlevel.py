import importlib.util
from pathlib import Path

import pytest


HIGHLEVEL_PATH = (
    Path(__file__).resolve().parents[2] / "lib" / "autokey" / "scripting" / "highlevel.py"
)
HIGHLEVEL_SPEC = importlib.util.spec_from_file_location("highlevel", HIGHLEVEL_PATH)
highlevel = importlib.util.module_from_spec(HIGHLEVEL_SPEC)
HIGHLEVEL_SPEC.loader.exec_module(highlevel)


def test_get_png_dim_reads_png_header(tmp_path):
    png_file = tmp_path / "pattern.png"
    png_file.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\r"
        b"IHDR"
        b"\x00\x00\x00\x10"
        b"\x00\x00\x00\x20"
    )

    assert highlevel.get_png_dim(str(png_file)) == (16, 32)


def test_get_png_dim_rejects_non_png(tmp_path):
    text_file = tmp_path / "pattern.txt"
    text_file.write_text("not a png", encoding="utf-8")

    with pytest.raises(Exception, match="not PNG"):
        highlevel.get_png_dim(str(text_file))
