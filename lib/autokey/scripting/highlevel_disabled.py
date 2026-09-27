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

"""
Stand-in for `highlevel` on Wayland.

`highlevel`'s image-matching functions (visgrep, click_on_pat, move_to_pat)
wrap xautomation's png2pat/visgrep/xte and ImageMagick's xwd/convert, all of
which need a capturable X11 root window. Under Wayland, XWayland only gives
individual client windows, not the whole compositor scene, so none of this
can work there (see issue #1001). A PIL+OpenCV replacement that works on
both X11 and Wayland is planned for AutoKey 0.98.0; until then this module
is swapped in for `highlevel` on Wayland sessions (see scripting/__init__.py)
so a script calling one of these functions gets a clear, immediate error
instead of a confusing failure deep inside a missing command-line tool.
Kept alongside the real module rather than removing it, so X11 sessions are
unaffected and this stand-in can simply be dropped once the replacement
lands.
"""
from autokey.scripting.highlevel import LEFT, MIDDLE, RIGHT, PatternNotFound, get_png_dim  # noqa: F401

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
mouse_move = _disabled("mouse_move")
mouse_rmove = _disabled("mouse_rmove")
mouse_click = _disabled("mouse_click")
mouse_pos = _disabled("mouse_pos")
click_on_pat = _disabled("click_on_pat")
move_to_pat = _disabled("move_to_pat")
acknowledge_gnome_notification = _disabled("acknowledge_gnome_notification")
