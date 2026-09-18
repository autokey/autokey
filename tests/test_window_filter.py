# Copyright (C) 2026 AutoKey contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import pytest
from hamcrest import *

from autokey.model.abstract_window_filter import AbstractWindowFilter
from autokey.sys_interface.abstract_interface import WindowInfo


class FilterItem(AbstractWindowFilter):
    """Minimal concrete item, to test the mixin without Folder/Phrase side effects."""

    def __init__(self, regex=None, recursive=False, inverted=False, parent=None):
        AbstractWindowFilter.__init__(self)
        self.parent = parent
        self.set_window_titles(regex)
        self.isRecursive = recursive
        self.isInverted = inverted


TERMINAL = WindowInfo("bjohas@host: ~", "gnome-terminal-server.Gnome-terminal")
FIREFOX = WindowInfo("Mozilla Firefox", "Navigator.Firefox")

# Filters are applied with re.match(), which anchors at the start of the string but
# does not require a full match, so a filter for the terminal has to start where its
# wm_class does. Note that TERMINAL's title names neither the class nor the app.
TERMINAL_RE = "gnome-terminal.*"


@pytest.mark.parametrize("inverted, window, expected", [
    # Plain include filter: unchanged behaviour.
    [False, FIREFOX, True],
    [False, TERMINAL, False],
    # Inverted: the same filter now means "everywhere but here".
    [True, FIREFOX, False],
    [True, TERMINAL, True],
])
def test_invert_flips_the_match(inverted, window, expected):
    item = FilterItem("Navigator.Firefox", inverted=inverted)
    assert_that(item._should_trigger_window_title(window), is_(expected))


def test_inverted_filter_excludes_on_class_match_alone():
    """
    The case a negative-lookahead regex cannot express.

    The regex is applied to wm_title and wm_class separately and the results OR'd,
    so a lookahead that rejects the class still matches the unrelated title and the
    item fires anyway. Inverting at the match site gives not(title or class), which
    excludes the window if EITHER property matches.

    Also pins the De Morgan slip: `not a or not b` would return True here.
    """
    window = WindowInfo("vim NOTES.md", "Gnome-terminal")

    assert_that(FilterItem("^Gnome-terminal$")._should_trigger_window_title(window), is_(True))
    assert_that(
        FilterItem("^Gnome-terminal$", inverted=True)._should_trigger_window_title(window),
        is_(False),
    )


def test_invert_without_a_regex_still_triggers_everywhere():
    """An item with no filter must not become an item that never fires."""
    item = FilterItem(None, inverted=True)
    assert_that(item.get_applicable_regex(), is_(none()))
    assert_that(item._should_trigger_window_title(TERMINAL), is_(True))


# --- inheritance ---------------------------------------------------------------

def test_child_inherits_parents_invert_flag_not_its_own():
    parent = FilterItem(TERMINAL_RE, recursive=True, inverted=True)
    child = FilterItem(None, inverted=False, parent=parent)

    assert_that(child.get_applicable_regex().pattern, is_(TERMINAL_RE))
    assert_that(child.get_applicable_filter_inverted(), is_(True))
    assert_that(child._should_trigger_window_title(TERMINAL), is_(False))
    assert_that(child._should_trigger_window_title(FIREFOX), is_(True))


def test_child_does_not_impose_its_own_invert_on_an_inherited_filter():
    parent = FilterItem("Navigator.Firefox", recursive=True, inverted=False)
    child = FilterItem(None, inverted=True, parent=parent)

    assert_that(child.get_applicable_filter_inverted(), is_(False))
    assert_that(child._should_trigger_window_title(FIREFOX), is_(True))


def test_non_recursive_parent_filter_is_not_inherited():
    parent = FilterItem("Gnome-terminal", recursive=False, inverted=True)
    child = FilterItem(None, parent=parent)

    assert_that(child.get_applicable_regex(), is_(none()))
    assert_that(child.get_applicable_filter_inverted(), is_(False))


def test_own_filter_wins_over_inherited_one():
    parent = FilterItem("Gnome-terminal", recursive=True, inverted=True)
    child = FilterItem("Navigator.Firefox", inverted=False, parent=parent)

    assert_that(child.get_applicable_regex().pattern, is_("Navigator.Firefox"))
    assert_that(child.get_applicable_filter_inverted(), is_(False))


def test_the_two_inheritance_walks_agree_on_the_winning_ancestor():
    """
    get_applicable_regex() and get_applicable_filter_inverted() are parallel walks.
    If they ever diverge, an item silently gets one ancestor's regex with another
    ancestor's invert flag.
    """
    grandparent = FilterItem("gp", recursive=True, inverted=True)
    parent = FilterItem(None, recursive=True, inverted=False, parent=grandparent)
    child = FilterItem(None, inverted=False, parent=parent)

    # The regex comes from the grandparent, so the flag must too.
    assert_that(child.get_applicable_regex().pattern, is_("gp"))
    assert_that(child.get_applicable_filter_inverted(), is_(True))

    # Now the parent supplies the regex, so the flag must come from the parent.
    parent.set_window_titles("p")
    parent.isInverted = False
    assert_that(child.get_applicable_regex().pattern, is_("p"))
    assert_that(child.get_applicable_filter_inverted(), is_(False))


# --- serialization -------------------------------------------------------------

def test_older_config_without_the_key_loads_without_raising():
    """
    A KeyError here is swallowed by the broad handler in model/common.py, which
    would silently load the rest of the item incompletely rather than fail loudly.
    """
    item = FilterItem()
    item.load_from_serialized({"regex": "Gnome-terminal", "isRecursive": True})

    assert_that(item.isInverted, is_(False))
    assert_that(item.isRecursive, is_(True))
    assert_that(item.windowInfoRegex.pattern, is_("Gnome-terminal"))


def test_pre_0_80_4_bare_string_form_still_loads():
    item = FilterItem()
    item.load_from_serialized("Gnome-terminal")

    assert_that(item.windowInfoRegex.pattern, is_("Gnome-terminal"))
    assert_that(item.isInverted, is_(False))


@pytest.mark.parametrize("inverted", [True, False])
def test_serialization_round_trip(inverted):
    source = FilterItem("Gnome-terminal", recursive=True, inverted=inverted)
    data = source.get_serializable()
    assert_that(data["isInverted"], is_(inverted))

    restored = FilterItem()
    restored.load_from_serialized(data)
    assert_that(restored.isInverted, is_(inverted))
    assert_that(restored.isRecursive, is_(True))


def test_an_item_without_a_regex_never_persists_a_stale_invert_flag():
    """
    Both UIs skip the filter dialog's save() when the filter is disabled and call
    set_window_titles(None) instead, leaving isInverted set on the live object.
    """
    item = FilterItem("Gnome-terminal", inverted=True)
    item.set_window_titles(None)

    assert_that(item.get_serializable()["isInverted"], is_(False))


def test_copy_window_filter_copies_the_flag():
    source = FilterItem("Gnome-terminal", recursive=True, inverted=True)
    target = FilterItem()
    target.copy_window_filter(source)

    assert_that(target.isInverted, is_(True))
    assert_that(target.isRecursive, is_(True))


def test_subclasses_that_skip_init_do_not_raise():
    """
    AbstractHotkey.__init__() does not call AbstractWindowFilter.__init__(), which is
    why GlobalHotkey assigns the filter attributes by hand. The class-level default
    keeps such subclasses working.
    """
    from autokey.configmanager.configmanager import GlobalHotkey

    hotkey = GlobalHotkey()
    assert_that(hotkey.isInverted, is_(False))
    assert_that(hotkey.get_applicable_filter_inverted(), is_(False))
    assert_that(hotkey._should_trigger_window_title(TERMINAL), is_(True))


# --- grab-site helper ----------------------------------------------------------

@pytest.mark.parametrize("inverted", [True, False])
def test_unknown_windows_never_attract_a_grab(inverted):
    """
    interface.py obtains WindowInfo with traverse=False, so window-manager frames
    report an empty title and class. For an inverted filter those must not count as
    "does not match, therefore grab" - that would claim the excluded app's subtree.
    """
    item = FilterItem("Gnome-terminal", inverted=inverted)
    assert_that(item._should_grab_on_window(WindowInfo("", "")), is_(False))


def test_known_windows_follow_the_trigger_decision():
    item = FilterItem(TERMINAL_RE, inverted=True)

    assert_that(item._should_grab_on_window(FIREFOX), is_(True))
    assert_that(item._should_grab_on_window(TERMINAL), is_(False))
