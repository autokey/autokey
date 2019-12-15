import datetime
from abc import abstractmethod
import shlex

from autokey.iomediator.constants import KEY_SPLIT_RE
from autokey.iomediator.key import Key
from autokey import common

if common.USING_QT:
    from PyQt5.QtWidgets import QAction

    def _(text: str, args: tuple=None):
        """localisation function, currently returns the identity. If args are given, those are used to format
        text using the old-style % formatting."""
        if args:
            text = text % args
        return text

    class MacroAction(QAction):

        def __init__(self, menu, macro, callback):
            super(MacroAction, self).__init__(macro.TITLE, menu)
            self.macro = macro
            self.callback = callback
            self.triggered.connect(self.on_triggered)

        def on_triggered(self):
            self.callback(self.macro)

else:
    from gi.repository import Gtk


def extract_tag(s):
    if not isinstance(s, str):
        raise TypeError
    extracted = [p.split('>')[0] for p in s.split('<') if '>' in p]
    if len(extracted) == 0:
        return s
    else:
        return ''.join(extracted)

def split_key_val(s):
    # Split as if a shell argument.
    # Splits at spaces, but preserves spaces within quotes.
    pairs = shlex.split(s)
    return dict(pair.split('=', 1) for pair in pairs)

class MacroManager:

    def __init__(self, engine):
        self.macros = []

        self.macros.append(ScriptMacro(engine))
        self.macros.append(DateMacro())
        self.macros.append(FileContentsMacro())
        self.macros.append(CursorMacro())

    def get_menu(self, callback, menu=None):
        if common.USING_QT:
            for macro in self.macros:
                menu.addAction(MacroAction(menu, macro, callback))

        else:
            menu = Gtk.Menu()

            for macro in self.macros:
                menuItem = Gtk.MenuItem(macro.TITLE)
                menuItem.connect("activate", callback, macro)
                menu.append(menuItem)

            menu.show_all()

        return menu

    # Split expansion.string, expand and process its macros, then
    # replace with the results.
    def process_expansion_macros(self, content):
        # Split into sections with <> macros in them.
        # Using the Key split regex works for now.
        content_sections = KEY_SPLIT_RE.split(content)

        for macroClass in self.macros:
            content_sections = macroClass.process(content_sections)

        return ''.join(content_sections)


class AbstractMacro:

    @property
    @abstractmethod
    def ID(self):
        pass
    @property
    @abstractmethod
    def TITLE(self):
        pass
    @property
    @abstractmethod
    def ARGS(self):
        pass

    def get_token(self):
        ret = "<%s" % self.ID
        # TODO: v not used in initial implementation? This results in something like "<%s a= b= c=>"
        ret += "".join((" " + k + "=" for k, v in self.ARGS))
        ret += ">"
        return ret

    def _get_args(self, macro):
        args = split_key_val(macro)
        expected_args = [arg[0] for arg in self.ARGS]
        expected_argnum = len(self.ARGS)

        for arg in expected_args:
            if arg not in args:
                raise ValueError("Missing mandatory argument '{}' for macro '{}'".format(arg, self.ID))
        for arg in args:
            if arg not in expected_args:
                raise ValueError("Unexpected argument '{}' for macro '{}'".format(k, self.ID))
        return args

        return ret

    def _extract_macro(section):
        content = extract_tag(section)
        # type is space-separated from rest of macro.
        macro_type, macro = content.split(' ', 1)
        return macro_type, macro


    def process(self, sections):
        for i, section in enumerate(sections):
            if KEY_SPLIT_RE.match(section):
                macro_type, macro = _extract_macro(sections[i])
                if macro_type == self.ID:
        # parts and i are required for cursor macros.
                    sections = self.do_process(sections, i)
        return sections

    @abstractmethod
    def do_process(self, sections, i):
        """ Returns updated sections """
        # parts and i are required for cursor macros.
        return sections


class CursorMacro(AbstractMacro):

    ID = "cursor"
    TITLE = _("Position cursor")
    ARGS = []

    def do_process(self, sections, i):
        try:
            lefts = len(''.join(sections[i+1:]))
            sections.append(Key.LEFT * lefts)
            sections[i] = ''
        except IndexError:
            pass
        return sections


class ScriptMacro(AbstractMacro):

    ID = "script"
    TITLE = _("Run script")
    ARGS = [("name", _("Name")),
            ("args", _("Arguments (comma separated)"))]

    def __init__(self, engine):
        self.engine = engine

    def do_process(self, sections, i):
        macro_type, macro = _extract_macro(sections[i])
        args = self._get_args(macro)
        self.engine.run_script_from_macro(args)
        return self.engine._get_return_value()


class DateMacro(AbstractMacro):

    ID = "date"
    TITLE = _("Insert date")
    ARGS = [("format", _("Format"))]

    def do_process(self, sections, i):
        macro_type, macro = _extract_macro(sections[i])
        format_ = self._get_args(macro)["format"]
        date = datetime.datetime.now().strftime(format_)
        sections[i] = date
        return sections


class FileContentsMacro(AbstractMacro):

    ID = "file"
    TITLE = _("Insert file contents")
    ARGS = [("name", _("File name"))]

    def do_process(self, sections, i):
        macro_type, macro = _extract_macro(sections[i])
        name = self._get_args(macro)["name"]

        with open(name, "r") as inputFile:
            sections[i] = inputFile.read()
        return sections
