"""
Stand-in for `highlevel` on Wayland.

`highlevel`'s functions all wrap xautomation's png2pat/visgrep/xte or
ImageMagick's xwd/convert, which need a capturable X11 root window. Under
Wayland, XWayland only gives individual client windows, not the whole
compositor scene, so none of it can work there (see issue #1001). A
PIL+OpenCV replacement that works on both X11 and Wayland is planned for
AutoKey 0.98.0; until then this module is swapped in for `highlevel` on
Wayland sessions (see scripting/__init__.py) so a script calling one of
these functions gets a clear, immediate error instead of a confusing
failure deep inside a missing command-line tool. Kept alongside the real
module rather than removing it, so X11 sessions are unaffected and this
stand-in can simply be dropped once the replacement lands.
"""
from autokey.scripting.highlevel import LEFT, MIDDLE, RIGHT, PatternNotFound  # noqa: F401

_MESSAGE = (
    "highlevel.{name}() is not available under Wayland: it depends on "
    "X11-only tools (xautomation, ImageMagick) that cannot see window "
    "content under Wayland. It still works under X11. A Wayland-compatible "
    "replacement is planned for a future AutoKey release."
)


def _disabled(name):
    def raise_disabled(*_args, **_kwargs):
        raise RuntimeError(_MESSAGE.format(name=name))
    raise_disabled.__name__ = name
    return raise_disabled


visgrep = _disabled("visgrep")
get_png_dim = _disabled("get_png_dim")
mouse_move = _disabled("mouse_move")
mouse_rmove = _disabled("mouse_rmove")
mouse_click = _disabled("mouse_click")
mouse_pos = _disabled("mouse_pos")
click_on_pat = _disabled("click_on_pat")
move_to_pat = _disabled("move_to_pat")
acknowledge_gnome_notification = _disabled("acknowledge_gnome_notification")
