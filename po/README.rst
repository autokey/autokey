Translations
============

AutoKey uses GNU gettext. One catalog serves the GTK front end, the Qt front end and the shared code. Each language
has one file: ``po/<language>_<REGION>.po``. English is the source language. English does not need a catalog.

Terms
-----

language code
    A two-letter lowercase code. Examples: ``es`` (Spanish), ``ja`` (Japanese).

region code
    A two-letter uppercase code. Examples: ``ES`` (Spain), ``JP`` (Japan).

locale name
    The language code, an underscore and the region code. Examples: ``es_ES``, ``ja_JP``.

template
    The file ``po/autokey.pot``. It lists all the English strings. It has no translations.

catalog source
    A ``.po`` file. A translator edits this file.

compiled catalog
    A ``.mo`` file. AutoKey reads this file at run time. The build makes it from the catalog source.

Current catalogs
----------------

========== ===================== ==============
File       Language              Direction
========== ===================== ==============
es_ES.po   Spanish (Spain)       Left to right
ja_JP.po   Japanese (Japan)      Left to right
zh_CN.po   Chinese (Simplified)  Left to right
ar_SA.po   Arabic (Saudi Arabia) Right to left
========== ===================== ==============

File names
----------

Each catalog file name is a locale name. Use this format: ``<language>_<REGION>.po``.

The locale name is also the name of the folder that holds the compiled catalog:
``lib/autokey/locale/<locale name>/LC_MESSAGES/autokey.mo``. The build makes this folder from the file name. Do not
rename the folder by hand.

The ``Language:`` line in the header of the catalog source must be the same as the locale name.

Choosing the language in AutoKey
--------------------------------

Do these steps to choose the language of the AutoKey windows.

1. Open the settings dialog: **Edit** > **Preferences** (GTK) or **Settings** > **Configure AutoKey** (Qt).
2. On the general settings page, open the **Language** list.
3. Select a language. The list shows the name of each language in that language.
4. Click **OK** or **Save**.
5. Restart AutoKey. The new language applies after the restart.

The list has these choices:

* **System default**: AutoKey uses the language of the system. This is the default choice.
* **English**: AutoKey shows English. It ignores the language of the system.
* One choice for each compiled catalog in the package.

AutoKey saves the choice in the ``language`` setting in ``~/.config/autokey/autokey.json``. The value is a locale name,
for example ``ja_JP``. The value ``en`` is English. An empty value is "System default".

If the saved language has no catalog, AutoKey uses the language of the system. This can occur after you remove a
catalog.

How AutoKey selects a language
------------------------------

AutoKey first uses the language that you chose in the settings dialog. If you did not choose one, or if you chose
"System default", AutoKey reads these environment variables. It uses the first one that has a value:

1. ``LANGUAGE``
2. ``LC_ALL``
3. ``LC_MESSAGES``
4. ``LANG``

``LANGUAGE`` can hold a list of locale names. Put a colon between the names. Example: ``LANGUAGE=ja_JP:es_ES``. AutoKey
uses the first name in the list that has a catalog.

A locale name can have a character set after the region. Example: ``es_ES.UTF-8``. AutoKey ignores the character set.

AutoKey looks for a catalog in this order:

1. The folder that matches the full locale name.
2. The folder that matches the language code only.
3. A folder for the same language code and a different region.

For example, the name ``es_MX`` gives these searches:

1. ``es_MX``
2. ``es``
3. ``es_ES`` (or any other ``es_<REGION>`` catalog)

Step 3 lets a user of a region that has no catalog read the language of another region. A user of ``es_MX`` reads the
``es_ES`` catalog. A user of ``zh_TW`` reads the ``zh_CN`` catalog. If two catalogs match, AutoKey uses the first one in
alphabetical order.

AutoKey never uses a catalog of a different language. A user of ``pt_BR`` sees English because there is no ``pt``
catalog.

If AutoKey finds no catalog, it shows English. If a catalog does not have a translation for a string, AutoKey shows the
English text for that string.

To see which language AutoKey loaded, call ``autokey.i18n.get_language()``. It returns the locale name of the loaded
catalog. It returns an empty string when AutoKey shows English.

Right-to-left languages
-----------------------

AutoKey mirrors the layout of the windows when the language code is ``ar``, ``fa``, ``he`` or ``ur``. The region code
does not change this behavior.

Using a translation from a source checkout
------------------------------------------

An installed AutoKey package has the compiled catalogs. A source checkout does not. Do these steps to test a
translation from a source checkout.

1. Install the ``gettext`` package. It supplies ``msgfmt``.
2. Make the folder for the compiled catalog::

       mkdir -p lib/autokey/locale/es_ES/LC_MESSAGES

3. Compile the catalog::

       msgfmt -o lib/autokey/locale/es_ES/LC_MESSAGES/autokey.mo po/es_ES.po

4. Start AutoKey with the language set::

       LANGUAGE=es_ES ./autokey-gtk

To use a catalog folder in a different location, set ``AUTOKEY_LOCALEDIR`` to that folder.

The command ``python3 setup.py build`` compiles all the catalogs. If ``msgfmt`` is not installed, the build shows a
warning and continues. The package then has no translations.

Updating a language
-------------------

Do these steps after the English text in the code changes.

1. Install the ``gettext`` package.
2. Update the template and all the catalogs::

       python3 po/update_pot.py --merge

3. Open the catalog source in a text editor or a ``.po`` editor.
4. Translate each entry that has an empty ``msgstr``.
5. Review each entry that has the ``fuzzy`` flag. Correct the translation. Then remove the flag.
6. Check the file::

       msgfmt --check --statistics -o /dev/null po/<locale name>.po

   The command must show no errors. The statistics line shows how many entries are not translated.

**Warning:** AutoKey ignores a ``fuzzy`` entry at run time. Remove the flag when the translation is correct.

To update the template only, and not the catalogs, run ``python3 po/update_pot.py`` without ``--merge``.

Adding a language
-----------------

1. Install the ``gettext`` package.
2. Update the template::

       python3 po/update_pot.py

3. Make the catalog source from the template. Use the locale name of the new language::

       msginit --locale=<locale name> --input=po/autokey.pot --output=po/<locale name>.po

   Example: ``msginit --locale=de_DE --input=po/autokey.pot --output=po/de_DE.po``

4. Open the new file. Make sure that the ``Language:`` line is the locale name.
5. Translate each ``msgstr`` entry.
6. Check the file::

       msgfmt --check --statistics -o /dev/null po/<locale name>.po

7. Test the catalog. Use the steps in "Using a translation from a source checkout".
8. Add a row for the new language to the table "Current catalogs" in this file.
9. Add the name of the language, written in that language, to ``LANGUAGE_NAMES`` in ``lib/autokey/i18n.py``. The
   language list in the settings dialog shows this name. Without it, the list shows the locale name.
10. If the language is written from right to left, make sure that its language code is in ``RTL_LANGUAGES`` in
   ``lib/autokey/i18n.py``.

The build finds the new file by itself. Do not change ``setup.py``.

Rules for translators
---------------------

* ``&`` (Qt) and ``_`` (GTK) before a letter mark the keyboard shortcut of a menu item or a button. Keep one mark in
  the translation. Put it on a letter that no other item in the same menu uses.
* Keep placeholders exactly as they are in the English text. Placeholders are ``%s``, ``%d``, ``{}`` and ``{name}``.
  You can change the order of placeholders that have a name.
* Some English words are identifiers in the code. An example is the name of a send mode. AutoKey translates these
  words for display only. AutoKey does not save the translated word.

Rules for developers
--------------------

* Put user-visible text in ``_()``. Use this import: ``from autokey.i18n import _``.
* Use ``N_()`` to mark a string that AutoKey translates later.
* Do not translate log messages.
* Write complete sentences with named placeholders. Do not join text fragments. A translator must be able to change the
  word order.
* Do not compare the text shown in a widget to find out what the user selected. Use the index or the item data. A
  combo box that shows translated names keeps a list of the original keys.
* The text in the Qt Designer ``.ui`` files and in the GTK Glade ``.xml`` files is extracted automatically.
  ``autokey.qtui.common.GettextTranslator`` translates the Qt text at run time.
* After you change user-visible text, run ``python3 po/update_pot.py`` and commit the changed ``po/autokey.pot``.
