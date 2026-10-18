# Regression tests for issue #1185: editing an existing abbreviation and
# clicking OK without pressing Enter first silently discards the edit.
#
# GTK's CellRendererText fires "editing-canceled" (not "edited") whenever the
# embedded GtkEntry loses focus without the user pressing Enter -- clicking OK
# directly is exactly this case. "editing-canceled" carries no text of its
# own, so on_cell_editing_cancelled() previously fell back to whatever the
# model already held (the value before this edit started), discarding
# whatever the user had just typed. The fix keeps a reference to the live
# GtkEntry from "editing-started" and reads its current text instead.

import gettext

import pytest

gi = pytest.importorskip("gi", reason="GTK UI tests need PyGObject")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

gettext.install("autokey")

from autokey.gtkui.dialogs import AbbrSettingsDialog  # noqa: E402


class _StubAbbrSettingsDialog:
    """
    A minimal stand-in carrying just the state these handlers touch, so they
    can be exercised without constructing the full Gtk.Builder-loaded dialog.
    """

    on_cell_editing_started = AbbrSettingsDialog.on_cell_editing_started
    on_cell_editing_cancelled = AbbrSettingsDialog.on_cell_editing_cancelled
    on_cell_modified = AbbrSettingsDialog.on_cell_modified
    on_removeButton_clicked = AbbrSettingsDialog.on_removeButton_clicked
    _update_ok_button = AbbrSettingsDialog._update_ok_button

    def __init__(self, initial_rows):
        store = Gtk.ListStore(str)
        for row in initial_rows:
            store.append((row,))
        self.abbrList = Gtk.TreeView(model=store)
        self.abbrList.get_selection().select_path(Gtk.TreePath.new_first())
        self.removeButton = Gtk.Button()
        self._current_editor = None
        self._ok_button_enabled = True

    def set_response_sensitive(self, response_id, sensitive):
        pass

    def current_value(self):
        model, curIter = self.abbrList.get_selection().get_selected()
        return model.get_value(curIter, 0)


def test_editing_started_stores_the_live_editable():
    dialog = _StubAbbrSettingsDialog(["abc"])
    entry = Gtk.Entry()

    dialog.on_cell_editing_started(None, entry, "0")

    assert dialog._current_editor is entry


def test_editing_cancelled_saves_live_text_not_the_old_model_value():
    """
    The exact scenario from #1185: an existing abbreviation is being edited,
    and OK is clicked before Enter, so GTK cancels the edit instead of
    committing it.
    """
    dialog = _StubAbbrSettingsDialog(["original"])
    entry = Gtk.Entry()
    entry.set_text("edited but not confirmed")
    dialog.on_cell_editing_started(None, entry, "0")

    dialog.on_cell_editing_cancelled(None)

    assert dialog.current_value() == "edited but not confirmed"


def test_editing_cancelled_without_a_live_editor_falls_back_to_the_model_value():
    """Defensive: if editing-started never fired, don't blank the row."""
    dialog = _StubAbbrSettingsDialog(["original"])

    dialog.on_cell_editing_cancelled(None)

    assert dialog.current_value() == "original"


def test_cell_modified_clears_the_stored_editor():
    """
    A real Enter-commit ("edited") must not leave a stale editor reference
    behind for some later, unrelated cancel to pick up.
    """
    dialog = _StubAbbrSettingsDialog(["original"])
    entry = Gtk.Entry()
    dialog.on_cell_editing_started(None, entry, "0")

    dialog.on_cell_modified(None, "0", "confirmed via enter")

    assert dialog._current_editor is None
    assert dialog.current_value() == "confirmed via enter"


def test_cancelling_a_newly_added_blank_row_still_removes_it():
    """
    on_cell_modified() only removes the row when BOTH the old and new text
    are empty -- the fresh, never-typed-in row case. That pre-existing
    behaviour must survive editing-canceled now trusting the live editor's
    text instead of always falling back to the model's (also blank) value.
    """
    dialog = _StubAbbrSettingsDialog([""])
    entry = Gtk.Entry()
    dialog.on_cell_editing_started(None, entry, "0")

    dialog.on_cell_editing_cancelled(None)

    model = dialog.abbrList.get_model()
    assert model.get_iter_first() is None


def test_clearing_an_existing_abbreviations_text_leaves_an_empty_row():
    """
    Clearing existing (non-empty) text and cancelling is not the blank-row
    case above -- oldText is non-empty, so on_cell_modified's removal
    condition (both old and new empty) does not apply and the row's value
    is simply set to the empty string. This is pre-existing, unrelated
    behaviour; it must keep working unchanged.
    """
    dialog = _StubAbbrSettingsDialog(["original"])
    entry = Gtk.Entry()
    entry.set_text("original")
    dialog.on_cell_editing_started(None, entry, "0")
    entry.set_text("")

    dialog.on_cell_editing_cancelled(None)

    assert dialog.current_value() == ""
