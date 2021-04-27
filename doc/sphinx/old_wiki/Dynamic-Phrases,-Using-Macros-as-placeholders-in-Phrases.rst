Phrases can be made dynamic by including one or more macros. A macro
looks like an XML/HTML ``<tag>``, it consists of a special keyword and
space separated arguments in the ``key=value`` form, enclosed in angle
brackets (``<`` and ``>``). Whenever a Phrase is expanded, all included
macros are executed. Then the macro tags are replaced with their
execution results. When the replacement is finished, the result gets
pasted or typed (depending on the phrase setting).

In versions older than ``0.96.0``, the interface and implementation is a
bit brittle: - Argument values can’t contain spaces - ``<>`` angle
brackets in argument values interfere with the parser, and can’t be
escaped

In ``0.96.0``, arguments can be quoted if they contain spaces, and angle
brackets can be escaped with a single ``\``. Only ``\`` before an angle
bracket counts as an escape character. To form a literal ``\>``, just
add a single extra slash before the ``\>``. To add a literal ``\``
anywhere else, just add as normal for a string.

Macros cannot have a ``\`` right before the final ``>``. If you need
this, quote the argument containing the ``\``, or add a space after it.

Example of a quoted and escaped macro:
``<script name=system args="xclip \> ~/sorted_clip.txt">``

Other notes:

-  All arguments are required for a particular macro type, even if you
   don’t want to use them (like providing arguments to executed scripts)
-  Macros cannot be nested within one another (e.g., a ``date`` macro
   cannot use a ``file`` macro to provide the format).

Available Macros
================

Currently, there are four macros available: \* ``Position cursor``:
``<cursor>`` positions the text cursor at the indicated text position.
There may be only one ``<cursor>`` macro in a phrase, either directly or
indirectly. \* ``Insert date``: ``<date>`` inserts the current date. The
format parameter takes a formatting string, allowing precise control
over the resulting string. \* ``Insert file contents``: ``<file>`` takes
a file name as a parameter and reads the file content from the disk.
Beware that the whole content is read into the system memory at once and
is then typed or pasted. Don’t use it with too large files, or
experience application- or system lock-ups or long expansion times. \*
``Run script``: ``<script>``\ executes any AutoKey script. Scripts
executed from Phrases should never use the ``keyboard`` directly,
instead return their replacement text using the
``engine.set_return_value(str)``\ function. \* (As of ``0.96.0``)
``Run system command``: ``<system>`` takes a string as a parameter and
replaces the macro with stdout of that string run as a system command.

Macro templates are available and can be inserted into a currently
edited phrase using the menu bar: \* Qt GUI: ``Tools`` menu →
``Insert Macro`` → Choose one from the list \* GTK GUI: ``Edit`` menu →
``Insert Macro`` → Choose one from the list

Position cursor
---------------

The ``<cursor>`` macro does not take any extra arguments. When present
in a phrase, the text cursor will be placed at the position indicated by
the macro position. The example phrase with content
``my<cursor> phrase`` will be expanded to ``my| phrase``, where ``|``
indicates the text cursor position. Because there is only one text
cursor in the currently active text editor, there can be only one
``<cursor>`` macro in the phrase. Trying to use more than one
``<cursor>`` macro in a single phrase will result in a wrongly
positioned cursor.

Insert date
-----------

The ``<date format=formatting_string>`` macro is replaced with the
current date. The format string is evaluated by the Python3
``datetime.datetime.strftime()`` function, thus must be a valid Python
date formatting string. The exact and up to date documentation for the
supported format codes can be found
`here <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`__.
The supported format codes may depend on the Python version used to run
AutoKey. The Python API is stable, but new format codes might get
available, as new Python versions get released.

Insert file contents
--------------------

The ``<file name=path_to_file>`` reads a file from disk and inserts the
file content into the phrase. The ``name`` parameter takes an absolute
file path. The full file content is read into the system memory and then
placed into the phrase, so restrict yourself to small text files. When
using a 1MB large file, autokey will need about one million key strokes
to type the content. Typically, text editors dislike raw binary data, so
only use text files.

This can be used to include another Phrase by specifying its full file
path and treating it like an ordinary file.

Run script
----------

The ``<script name=script_name args=comma_separated_argument_string>``
macro allows to use AutoKey Python scripts for Phrase content
generation. This macro will execute the specified script during the
macro processing step, before the phrase is pasted. The ``<script>``
macro token will be replaced with the script return value, which can be
set using the ``engine.set_return_value(str)`` function. You should set
the return value to a Python ``str`` string only. If there is an error,
the macro will be replaced with that instead.

As of ``0.96.0``, Scripts outside of autokey can be executed by passing
their absolute path (including ``~``, which is expanded to ``$HOME``) to
``name=`` instead of a description.

Currently, the ``args`` argument expects a string containing comma
separated values (CSV). The data is split at the ``,`` signs and is
available as a list containing strings using the
``engine.get_macro_arguments()`` function. If there is no comma in the
input data, the resulting list will contain a single item. Currently,
the ``args`` argument is required. So if you don’t need it, just feed in
some dummy value. This behaviour might be improved in the future.

Running a Script using the ``script`` macro poses some limitations: -
The ``keyboard`` built-in cannot be used. It is available and can in
theory be used to type, but actually using it *will* break the Phrase
processing. - Because all scripts are executed even *before* the trigger
abbreviation is removed and the whole phrase is pasted/typed in one go,
scripts can’t be used to type *anywhere* in the phrase text. - Simple
rule: Do nothing that alters the current system GUI state. - Do not use
``keyboard`` to type/send keys. - Do not use ``mouse`` to do mouse
clicks anywhere. - Do not use ``system.exec_command`` to execute GUI
manipulation/automation tools, like ``xdotool``.

You may use the script to alter background system state, like starting
or stopping system services, but simply restricting yourself to reading
data in will yield the best results.

Run system command
------------------

As of ``0.96.0``: ``<system command='echo test'>`` is replaced in the
phrase with the output of ``echo test`` - i.e., test.
