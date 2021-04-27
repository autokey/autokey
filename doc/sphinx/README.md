# Autokey Documentation

Built using [sphinx]().

Uses the [sphinx autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) extension to automatically generate API documentation.

Uses the [sphinx epytext]() extension to convert older style epydoc documentation format to sphinx readable.

I also have it set to use [recommonmark]() in case any one wants to use markdown really badly.

The old wiki pages, while written in markdown are easily converted using the bash script provided, `pdmdtorst.sh` (PanDocMarkDownTORST). Run this in the base of the wiki repo and it will generate a `.rst` file for every `.md` file found.




## Local testing
You'll need the following python packages (and dependencies). From my command history getting it up and running;
- `pip install -U Sphinx`
- `pip install recommonmark`
- `pip install sphinx-rtd-theme`
- `pip install sphinx-epytext`
- `sphinx-build -a -E -b html . ./_build`

`-a` for write all files, `-E` for always read all files, `-b html` for output to be in html format.


## TODO
There is a plugin that supports versioned documentation, [sphinxcontrib-multiversion](https://github.com/Holzhaus/sphinx-multiversion) which seems to be decently well maintained.

There are some minor tweaks that need to be made to the source code to generate the final products;

In `scripting/__init__.py` you have to both;
- Remove the file's doc string
- Modify the clipboard imports so both the gtk and qt versions are imported;

```
--- a/lib/autokey/scripting/__init__.py
+++ b/lib/autokey/scripting/__init__.py
@@ -13,11 +13,7 @@
 # You should have received a copy of the GNU General Public License
 # along with this program. If not, see <http://www.gnu.org/licenses/>.

-"""
-This package contains the scripting API.

-This file centralises the public API classes for easier importing.
-"""

 import autokey.common

@@ -33,9 +29,9 @@ from .system import System
 from .window import Window

 # Platform abstraction
-if autokey.common.USING_QT:
-    from .clipboard_qt import QtClipboard as Clipboard
-    from .dialog_qt import QtDialog as Dialog
-else:
-    from .clipboard_gtk import GtkClipboard as Clipboard
-    from .dialog_gtk import GtkDialog as Dialog
+# if autokey.common.USING_QT:
+from .clipboard_qt import QtClipboard
+from .dialog_qt import QtDialog
+# else:
+from .clipboard_gtk import GtkClipboard
+from .dialog_gtk import GtkDialog
```

This can probably be solved in some way but I will leave that for later.

One quirk I noticed in the `keyboard` api page was that the enum for phrase send types (`SendMode`) did not respect the line formatting unless the were explicitly placed with `\\n`


