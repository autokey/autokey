# Tests for ConfigWindow._resolve_tree_path (issue #601).
#
# expanded_rows and last_open are positional GtkTreePath strings ("3:1:2")
# persisted across restarts, then resolved against a model that may have been
# rebuilt or reloaded since. Handing a stale one to select_path() has been
# observed to crash the process, so these cases are the guard against that.

import gettext

import pytest

gi = pytest.importorskip("gi", reason="GTK UI tests need PyGObject")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

# configwindow (via settingsdialog) uses the gettext _() builtin at import time,
# which is normally installed by the running application rather than by a test.
gettext.install("autokey")

from autokey.gtkui.configwindow import ConfigWindow  # noqa: E402


@pytest.fixture
def model():
    """A two-level store: row "0" has child "0:0"; row "1" is a leaf."""
    store = Gtk.TreeStore(str)
    parent = store.append(None, ["parent"])
    store.append(parent, ["child"])
    store.append(None, ["sibling"])
    return store


@pytest.mark.parametrize("path_string", ["0", "0:0", "1"])
def test_existing_paths_resolve_unchanged(model, path_string):
    resolved = ConfigWindow._resolve_tree_path(model, path_string)
    assert resolved is not None
    assert resolved.to_string() == path_string


@pytest.mark.parametrize("path_string, why", [
    ("9",     "top-level row index beyond the end of the model"),
    ("0:9",   "child index beyond the end of an existing parent"),
    ("0:0:0", "depth beyond what the model has"),
    ("2",     "the row a deleted folder used to occupy"),
])
def test_stale_paths_resolve_to_none(model, path_string, why):
    """
    These construct happily -- Gtk.TreePath.new_from_string does not validate
    against any model -- and only fail once handed to select_path(). That is the
    crash in #601.
    """
    assert ConfigWindow._resolve_tree_path(model, path_string) is None, why


@pytest.mark.parametrize("path_string", ["", None])
def test_empty_path_resolves_to_none(model, path_string):
    """
    Gtk.TreePath.new_from_string("") raises TypeError rather than returning None,
    so an `if p is not None` guard around it never gets the chance to run.
    """
    assert ConfigWindow._resolve_tree_path(model, path_string) is None


def test_malformed_path_resolves_to_none(model):
    assert ConfigWindow._resolve_tree_path(model, "not-a-path") is None


def test_missing_model_resolves_to_none():
    assert ConfigWindow._resolve_tree_path(None, "0") is None


def test_path_valid_before_rebuild_is_rejected_after(model):
    """The actual #601 sequence: remember a path, rebuild, then restore it."""
    remembered = "0:0"
    assert ConfigWindow._resolve_tree_path(model, remembered) is not None

    model.clear()                      # rebuild_tree() replaces the model wholesale
    model.append(None, ["only row"])

    assert ConfigWindow._resolve_tree_path(model, remembered) is None
