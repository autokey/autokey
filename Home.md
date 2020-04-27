In a nutshell, Autokey is a little GUI to run Python-3 scripts and text expansion, especially focusing on MACRO and keypress functionality.

AutoKey is not meant to be used as a general Python IDE, so it lacks debugger support and a lot more.
If you wish, you can use your favourite Python IDE to edit your AutoKey scripts.

To see, if your Distribution packages AutoKey, please see [this page](https://github.com/autokey/autokey/wiki/Current-Linux-distributions-shipping-AutoKey).

Refer to [Installing AutoKey](https://github.com/autokey/autokey/wiki/Installing) for instructions to install AutoKey. If you want to build your own Packages for installation using your package manager, see the [Packaging](https://github.com/autokey/autokey/wiki/Packaging) page.

AutoKey can be used for simple text expansion, i.e. replacing an abbreviation text with a static replacement. Within AutoKey, these replacement texts are called “Phrases”. It can also react to keyboard shortcuts e.g. `[Ctrl]+[Alt]+F8`, for Phrase expansion.
For increased flexibility, you can use [Macros](https://github.com/autokey/autokey/wiki/Dynamic-Phrases,-Using-Macros-as-placeholders-in-Phrases) within your Phrases to dynamically alter the typed content. See the [Beginner’s Guide](https://github.com/autokey/autokey/wiki/Beginners-Guide) for a more in-depth glossary and overview of the basics.

If the simple Phrase expansion does not fit your needs, you can unleash the full power of the Python programming language and write Scripts in Python 3 to automate your tasks. AutoKey Scripts can be bound to abbreviations and hotkeys, just like Phrases and execute your commands. AutoKey provides an API to interact with the system, like clicking with the mouse or typing text using the keyboard. You can see the (currently slightly outdated, but still functional) API reference [here](https://autokey.github.io/). If you’d like to see the API in action by seeing some examples, see [API-Examples](https://github.com/autokey/autokey/wiki/API-Examples).

Shown below is a screenshot of the main window (version 0.95.10), currently editing a Script:
[[/images/AutoKey_Scripting.png|Opened main window showing a Script that is used to close The Gimp, automatically discarding the "You have unsaved changes" dialogue window.]]