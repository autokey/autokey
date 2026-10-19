"""
Localisation support shared by the GTK, Qt and headless front ends.

User visible strings are wrapped in ``_()``. Translations live in gettext catalogs (``po/*.po`` in the source tree,
compiled to ``autokey/locale/<language>/LC_MESSAGES/autokey.mo`` at build time). The language is chosen from the usual
environment variables (LANGUAGE, LC_ALL, LC_MESSAGES, LANG). If there is no catalog for the exact region, a catalog for
the same language and another region is used. English is the source language, so a missing catalog or missing
translation falls back to the English text.

The environment variable AUTOKEY_LOCALEDIR can point at an alternative catalog directory.
"""

import gettext
import locale
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

DOMAIN = "autokey"

# Languages written right to left. The user interfaces mirror their layout when one of these is active.
RTL_LANGUAGES = frozenset({"ar", "fa", "he", "ur"})

_translation = gettext.NullTranslations()
_locale_dir = None  # type: Optional[str]
_language = ""


def _candidate_locale_dirs() -> List[Path]:
    candidates = []
    override = os.environ.get("AUTOKEY_LOCALEDIR")
    if override:
        candidates.append(Path(override))
    candidates.append(Path(__file__).resolve().parent / "locale")
    candidates.append(Path(sys.prefix) / "share" / "locale")
    candidates.append(Path("/usr/share/locale"))
    return candidates


def _requested_languages() -> List[str]:
    """The language list gettext would take from the environment (LANGUAGE, LC_ALL, LC_MESSAGES, LANG)."""
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable)
        if value:
            return value.split(":")
    return []


def _installed_locales() -> List[str]:
    """The names of all the compiled catalogs, e.g. ["es_ES", "zh_CN"]."""
    names = []  # type: List[str]
    for directory in _candidate_locale_dirs():
        if directory.is_dir():
            names.extend(sorted(p.name for p in directory.iterdir()
                                if (p / "LC_MESSAGES" / (DOMAIN + ".mo")).is_file()))
    return names


def _with_regional_fallbacks(languages: Optional[List[str]]) -> List[str]:
    """
    After each requested language, add the installed catalogs for the same language code but another region. A user of
    es_MX then gets the es_ES catalog if there is no es_MX or es catalog. The exact request always comes first.
    """
    if languages is None:
        languages = _requested_languages()
    installed = _installed_locales()
    expanded = []  # type: List[str]
    for requested in languages:
        expanded.append(requested)
        code = re.split(r"[_.@-]", requested)[0]
        if code and code != "C":
            expanded.extend(name for name in installed if name.split("_")[0] == code and name not in expanded)
    return expanded


def find_locale_dir(languages: Optional[List[str]] = None) -> Optional[str]:
    """Return the first catalog directory that has a catalog for the requested (or environment) languages."""
    languages = _with_regional_fallbacks(languages)
    for directory in _candidate_locale_dirs():
        if gettext.find(DOMAIN, str(directory), languages):
            return str(directory)
    return None


def set_language(languages: Optional[List[str]] = None) -> None:
    """
    Load the catalog for the given language codes, e.g. ["es_MX", "es"]. With None, the language is taken from the
    environment. If there is no catalog for the requested region, a catalog for the same language and another region is
    used. Falls back to untranslated English.
    """
    global _translation, _locale_dir, _language
    languages = _with_regional_fallbacks(languages)
    _locale_dir = find_locale_dir(languages)
    _language = ""
    if _locale_dir:
        _translation = gettext.translation(DOMAIN, _locale_dir, languages, fallback=True)
        _language = _translation.info().get("language", "")
        # GtkBuilder translates Glade strings through the C library, so bind the domain there as well.
        try:
            locale.bindtextdomain(DOMAIN, _locale_dir)
            locale.textdomain(DOMAIN)
        except (AttributeError, OSError):
            pass
    else:
        _translation = gettext.NullTranslations()


def get_locale_dir() -> Optional[str]:
    return _locale_dir


def get_language() -> str:
    """The language code of the loaded catalog, e.g. "es" or "zh_CN". Empty if running untranslated (English)."""
    return _language


def is_rtl() -> bool:
    """True if the loaded translation is for a right to left language such as Arabic."""
    return _language.replace("-", "_").split("_")[0] in RTL_LANGUAGES


def _(message: str) -> str:
    """Translate message into the current language."""
    if not message:
        return message
    return _translation.gettext(message)


def N_(message: str) -> str:
    """Mark message for extraction without translating it now. Translate later with _()."""
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    return _translation.ngettext(singular, plural, n)


set_language()
