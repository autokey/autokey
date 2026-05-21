# Copyright (C) 2026

import base64

import pytest

from autokey.scripting.highlevel import get_png_dim


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO3ZswAAAABJRU5ErkJggg=="
)


def test_get_png_dim_reads_png_dimensions(tmp_path):
    png_path = tmp_path / "image.png"
    png_path.write_bytes(PNG_1X1)

    assert get_png_dim(str(png_path)) == (1, 1)


def test_get_png_dim_rejects_non_png(tmp_path):
    text_path = tmp_path / "note.txt"
    text_path.write_text("not a png", encoding="utf-8")

    with pytest.raises(Exception, match="not PNG"):
        get_png_dim(str(text_path))
