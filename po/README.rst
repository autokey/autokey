Translations
============

AutoKey uses GNU gettext. The same catalog serves the GTK front end, the Qt front end and the shared code, so each
language is a single ``po/<language>.po`` file. English is the source language and needs no catalog.

Using a translation
-------------------

The language is picked from the usual environment variables (``LANGUAGE``, ``LC_ALL``, ``LC_MESSAGES``, ``LANG``).
Anything that is missing from a catalog is shown in English.

``setup.py`` compiles the ``.po`` files with ``msgfmt`` (package ``gettext``) into
``lib/autokey/locale/<language>/LC_MESSAGES/autokey.mo`` and ships them with the package. To try a translation from a
source checkout, compile it yourself and start AutoKey with the language set::

    mkdir -p lib/autokey/locale/es/LC_MESSAGES
    msgfmt -o lib/autokey/locale/es/LC_MESSAGES/autokey.mo po/es.po
    LANGUAGE=es ./autokey-gtk

Set ``AUTOKEY_LOCALEDIR`` to use a catalog directory somewhere else.

Adding or updating a language
-----------------------------

1. Run ``python3 po/update_pot.py`` after changing any user visible text. This rewrites ``po/autokey.pot``. Add
   ``--merge`` to also bring the existing ``po/*.po`` files up to date.
2. For a new language, copy the template with ``msginit --locale=<language> --input=po/autokey.pot
   --output=po/<language>.po`` and translate the ``msgstr`` entries.
3. Check the file with ``msgfmt --check --statistics -o /dev/null po/<language>.po``. Entries marked ``fuzzy`` are
   ignored at runtime, so review and unmark them.

Notes for translators
---------------------

* ``&`` (Qt) and ``_`` (GTK) in front of a letter mark the keyboard mnemonic of a menu item or button. Keep one in the
  translation, preferably on a letter that is not used by another item in the same menu.
* Keep placeholders such as ``%s``, ``%d``, ``{}`` and ``{name}`` exactly as written. Their order may change when
  they are named.
* Strings that are only English identifiers in the code, for example the send mode names, are translated for display
  only. Nothing is saved in the translated form.

Notes for developers
--------------------

* Wrap user visible text in ``_()`` (``from autokey.i18n import _``). Use ``N_()`` to mark a string that is translated
  later. Do not translate log messages.
* Write whole sentences with named placeholders instead of joining fragments, so translators can reorder them.
* Never compare the text shown in a widget to find out what the user chose. Use the index or item data. Combo boxes
  that show translated names keep a list of the original keys next to them.
* The strings in the Qt Designer ``.ui`` files and the GTK Glade ``.xml`` files are extracted automatically. The Qt
  ones are translated at run time by ``autokey.qtui.common.GettextTranslator``.
