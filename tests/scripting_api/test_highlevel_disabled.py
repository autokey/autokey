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
    ("get_png_dim", ("scr.png",)),
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
    """Plain int/exception-type values, kept so `except PatternNotFound` and
    button-constant references in existing scripts still import cleanly --
    not calls, so there's nothing to disable."""
    assert highlevel_disabled.LEFT == highlevel.LEFT
    assert highlevel_disabled.MIDDLE == highlevel.MIDDLE
    assert highlevel_disabled.RIGHT == highlevel.RIGHT
    assert highlevel_disabled.PatternNotFound is highlevel.PatternNotFound
