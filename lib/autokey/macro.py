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

    def process_expansion(self, expansion):
        parts = KEY_SPLIT_RE.split(expansion.string)

        for macro in self.macros:
            macro.process(parts)

        expansion.string = ''.join(parts)


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

    def _can_process(self, token):
        if KEY_SPLIT_RE.match(token):
            return token[1:-1].split(' ', 1)[0] == self.ID
        else:
            return False

    def _get_args(self, token):
        macro = extract_tag(token)
        macro_type, macro = macro.split(' ', 1)
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

    def process(self, parts):
        for i in range(len(parts)):
            if self._can_process(parts[i]):
                self.do_process(parts, i)

    @abstractmethod
    def do_process(self, parts, i):
        pass


class CursorMacro(AbstractMacro):

    ID = "cursor"
    TITLE = _("Position cursor")
    ARGS = []

    def do_process(self, parts, i):
        try:
            lefts = len(''.join(parts[i+1:]))
            parts.append(Key.LEFT * lefts)
            parts[i] = ''
        except IndexError:
            pass


class ScriptMacro(AbstractMacro):

    ID = "script"
    TITLE = _("Run script")
    ARGS = [("name", _("Name")),
            ("args", _("Arguments (comma separated)"))]

    def __init__(self, engine):
        self.engine = engine

    def do_process(self, parts, i):
        args = self._get_args(parts[i])
        self.engine.run_script_from_macro(args)
        parts[i] = self.engine._get_return_value()


class DateMacro(AbstractMacro):

    ID = "date"
    TITLE = _("Insert date")
    ARGS = [("format", _("Format"))]

    def do_process(self, parts, i):
        format_ = self._get_args(parts[i])["format"]
        date = datetime.datetime.now().strftime(format_)
        parts[i] = date


class FileContentsMacro(AbstractMacro):

    ID = "file"
    TITLE = _("Insert file contents")
    ARGS = [("name", _("File name"))]

    def do_process(self, parts, i):
        name = self._get_args(parts[i])["name"]

        with open(name, "r") as inputFile:
            parts[i] = inputFile.read()
