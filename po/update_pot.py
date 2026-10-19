#!/usr/bin/env python3
"""
Regenerate po/autokey.pot from the AutoKey sources, and optionally merge the result into the existing po/*.po files.

Three kinds of source are scanned:

* Python files, for strings wrapped in _() / ngettext() / N_(). (xgettext)
* GTK Glade XML files, for properties marked translatable="yes". (xgettext)
* Qt Designer .ui files, for user-visible text, tooltips, titles, etc. Qt strings are looked up in the same gettext
  catalog at runtime, see autokey.qtui.common.GettextTranslator. (extracted by this script)

Usage:  python3 po/update_pot.py [--merge]

Requires the GNU gettext tools (xgettext, msgcat, msgmerge) to be installed.
"""

import argparse
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PO_DIR = ROOT / "po"
POT_FILE = PO_DIR / "autokey.pot"
LIB = ROOT / "lib" / "autokey"
GLADE_DIR = LIB / "gtkui" / "data"
QT_UI_DIR = LIB / "qtui" / "resources" / "ui"

# Qt Designer properties and attributes that hold text shown to the user. Shortcuts, number display formats and
# anything marked notr="true" are deliberately left alone.
QT_TRANSLATABLE_PROPERTIES = {
    "text", "title", "toolTip", "whatsThis", "windowTitle", "tipText", "placeholderText", "suffix", "statusTip",
}


def read_version() -> str:
    match = re.search(r"""^VERSION\s*=\s*["'](.*)["']""", (LIB / "common.py").read_text(), re.M)
    return match.group(1) if match else ""


def run(*command):
    subprocess.run([str(c) for c in command], check=True, cwd=str(ROOT))


def po_quote(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
    return '"' + escaped + '"'


def extract_qt_ui_strings(output: Path):
    """Write a .po fragment holding every translatable string in the Qt Designer .ui files."""
    entries = {}  # msgid -> [source file names], in first-seen order
    for ui_file in sorted(QT_UI_DIR.glob("*.ui")):
        relative = ui_file.relative_to(ROOT)
        tree = ET.parse(str(ui_file))
        parents = {child: parent for parent in tree.iter() for child in parent}
        for string in tree.iter("string"):
            parent = parents[string]
            if string.get("notr") == "true" or not (string.text or "").strip():
                continue
            if parent.tag in ("property", "attribute") and parent.get("name") in QT_TRANSLATABLE_PROPERTIES:
                files = entries.setdefault(string.text, [])
                if str(relative) not in files:
                    files.append(str(relative))
    with open(str(output), "w", encoding="utf-8") as fragment:
        fragment.write('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n')
        for msgid, files in entries.items():
            fragment.write("#: {}\n".format(" ".join(files)))
            fragment.write("msgid {}\nmsgstr \"\"\n\n".format(po_quote(msgid)))


def python_sources():
    return sorted(str(p.relative_to(ROOT)) for p in LIB.rglob("*.py") if "locale" not in p.relative_to(LIB).parts)


def glade_sources():
    # menus.xml is a GtkUIManager description without any user-visible text, and is not a Glade file.
    return sorted(str(p.relative_to(ROOT)) for p in GLADE_DIR.glob("*.xml") if "<interface>" in p.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--merge", action="store_true", help="also merge the new template into po/*.po")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        python_pot, glade_pot, qt_po = tmp / "python.pot", tmp / "glade.pot", tmp / "qt.po"
        common = ["--from-code=UTF-8", "--sort-by-file", "--add-comments=TRANSLATORS:", "--no-location"]
        run("xgettext", "--language=Python", "--keyword=_", "--keyword=N_", "--keyword=ngettext:1,2",
            "--output", python_pot, *common, *python_sources())
        run("xgettext", "--language=Glade", "--output", glade_pot, *common, *glade_sources())
        extract_qt_ui_strings(qt_po)
        run("msgcat", "--use-first", "--sort-by-file", "--output-file", POT_FILE, python_pot, glade_pot, qt_po)

    # Replace the generic header xgettext/msgcat produced with a project specific one.
    text = POT_FILE.read_text(encoding="utf-8")
    header_end = text.index("\n\n")
    header = (
        'msgid ""\n'
        'msgstr ""\n'
        '"Project-Id-Version: AutoKey {version}\\n"\n'
        '"Report-Msgid-Bugs-To: https://github.com/autokey/autokey/issues\\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"'
    ).format(version=read_version())
    POT_FILE.write_text("# AutoKey translation template.\n" + header + text[header_end:], encoding="utf-8")
    print("Wrote", POT_FILE.relative_to(ROOT))

    if args.merge:
        for po_file in sorted(PO_DIR.glob("*.po")):
            run("msgmerge", "--update", "--backup=none", "--no-fuzzy-matching", po_file, POT_FILE)
            print("Merged into", po_file.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
