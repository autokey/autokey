import shutil
import subprocess
from pathlib import Path

import pytest

import autokey.i18n as i18n
import autokey.model.phrase

PO_DIR = Path(__file__).resolve().parent.parent / "po"
needs_msgfmt = pytest.mark.skipif(shutil.which("msgfmt") is None, reason="GNU gettext (msgfmt) is not installed")


@pytest.fixture
def spanish(tmp_path, monkeypatch):
    """Compile po/es_ES.po into a temporary locale directory and switch AutoKey to Spanish."""
    target = tmp_path / "es_ES" / "LC_MESSAGES"
    target.mkdir(parents=True)
    subprocess.run(["msgfmt", "--check", "-o", str(target / "autokey.mo"), str(PO_DIR / "es_ES.po")], check=True)
    monkeypatch.setenv("AUTOKEY_LOCALEDIR", str(tmp_path))
    i18n.set_language(["es_ES"])
    yield
    monkeypatch.undo()
    i18n.set_language()


def test_untranslated_text_is_returned_unchanged():
    i18n.set_language(["xx"])
    try:
        assert i18n._("Save changes?") == "Save changes?"
        assert i18n._("") == ""
    finally:
        i18n.set_language()


@needs_msgfmt
def test_spanish_catalog_translates_known_strings(spanish):
    assert i18n._("Save changes?") == "¿Guardar los cambios?"
    assert i18n._("Some text that is not in the catalog") == "Some text that is not in the catalog"
    assert i18n._("") == ""


@needs_msgfmt
def test_other_region_falls_back_to_the_catalog_of_the_same_language(spanish):
    i18n.set_language(["es_MX.UTF-8"])
    assert i18n.get_language() == "es_ES"
    assert i18n._("Save changes?") == "¿Guardar los cambios?"


@needs_msgfmt
def test_region_fallback_does_not_cross_languages(spanish):
    i18n.set_language(["pt_BR"])
    assert i18n.get_language() == ""
    assert i18n._("Save changes?") == "Save changes?"


@needs_msgfmt
def test_region_fallback_reads_the_environment(spanish, monkeypatch):
    monkeypatch.setenv("LANGUAGE", "es_AR:en")
    i18n.set_language()
    assert i18n.get_language() == "es_ES"


@needs_msgfmt
def test_spanish_catalog_keeps_format_placeholders(spanish):
    translated = i18n._("The script '{}' encountered an error").format("Foo")
    assert "Foo" in translated and translated != "The script 'Foo' encountered an error"


@needs_msgfmt
@pytest.mark.parametrize("po_file", sorted(PO_DIR.glob("*.po")), ids=lambda p: p.name)
def test_po_files_are_valid_and_complete_enough(po_file):
    """msgfmt --check validates placeholders and header; fuzzy entries would be silently ignored at runtime."""
    result = subprocess.run(
        ["msgfmt", "--check", "--statistics", "-o", "/dev/null", str(po_file)],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "fuzzy" not in result.stderr


def test_send_mode_keys_stay_english_identifiers():
    """The UIs translate these for display only and map the selection back by position, so the keys must not change."""
    assert set(autokey.model.phrase.SEND_MODES) == {
        "Keyboard", "Clipboard (Ctrl+V)", "Clipboard (Ctrl+Shift+V)", "Clipboard (Shift+Insert)", "Mouse Selection"}


def test_word_char_option_keys_stay_english_identifiers():
    qt_options = pytest.importorskip("autokey.qtui.dialogs.abbrsettings").WORD_CHAR_OPTIONS
    gtk_options = pytest.importorskip("autokey.gtkui.dialogs").WORD_CHAR_OPTIONS
    assert set(qt_options) == set(gtk_options) == {"All non-word", "Space and Enter", "Tab"}


@needs_msgfmt
def test_right_to_left_languages_are_detected(spanish, tmp_path, monkeypatch):
    assert not i18n.is_rtl()
    assert i18n.get_language() == "es_ES"
    target = tmp_path / "ar_SA" / "LC_MESSAGES"
    target.mkdir(parents=True)
    subprocess.run(["msgfmt", "-o", str(target / "autokey.mo"), str(PO_DIR / "ar_SA.po")], check=True)
    i18n.set_language(["ar_SA"])
    assert i18n.get_language() == "ar_SA"
    assert i18n.is_rtl()
