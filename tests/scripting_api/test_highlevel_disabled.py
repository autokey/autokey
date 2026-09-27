# Regression tests for issue #1001: the `highlevel` scripting API
# (visgrep/click_on_pat/move_to_pat, backed by xautomation and ImageMagick)
# cannot work under Wayland, since XWayland only exposes individual client
# windows, not a capturable root of the whole compositor scene. Previously
# these functions stayed fully callable under Wayland and failed deep
# inside a missing command-line tool instead of with a clear message.
#
# highlevel_disabled.py stands in for `highlevel` on Wayland (wired up in
# scripting/__init__.py); these tests check its own behavior directly.
import pytest

import autokey.scripting.highlevel as highlevel
import autokey.scripting.highlevel_disabled as highlevel_disabled


@pytest.mark.parametrize("name, args", [
    ("visgrep", ("scr.png", "pat.png")),
    ("mouse_move", (1, 2)),
    ("mouse_rmove", (1, 2)),
    ("mouse_click", (1,)),
    ("mouse_pos", ()),
    ("click_on_pat", ("pat.png",)),
    ("move_to_pat", ("pat.png",)),
    ("acknowledge_gnome_notification", ()),
])
def test_disabled_functions_raise_a_clear_error(name, args):
    func = getattr(highlevel_disabled, name)
    with pytest.raises(RuntimeError, match="not available under Wayland"):
        func(*args)


def test_disabled_functions_error_names_the_call():
    with pytest.raises(RuntimeError, match=r"visgrep\(\)"):
        highlevel_disabled.visgrep("scr.png", "pat.png")


def test_constants_match_the_real_module():
    """Harmless, don't-depend-on-X11 values -- no reason to disable these."""
    assert highlevel_disabled.LEFT == highlevel.LEFT
    assert highlevel_disabled.MIDDLE == highlevel.MIDDLE
    assert highlevel_disabled.RIGHT == highlevel.RIGHT
    assert highlevel_disabled.PatternNotFound is highlevel.PatternNotFound


def test_get_png_dim_still_works(tmp_path):
    """Pure file-reading helper, no X11 dependency -- stays functional."""
    import struct
    png_path = tmp_path / "test.png"
    # Minimal valid PNG header: signature + IHDR chunk with width=10, height=20.
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack("!II", 10, 20) + b"\x08\x02\x00\x00\x00"
    chunk = struct.pack("!I", len(ihdr_data)) + b"IHDR" + ihdr_data + b"\x00\x00\x00\x00"
    png_path.write_bytes(signature + chunk)

    assert highlevel_disabled.get_png_dim(str(png_path)) == (10, 20)
