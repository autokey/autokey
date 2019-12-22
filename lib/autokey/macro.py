import datetime
from abc import abstractmethod
import shlex
import re

from autokey.iomediator.constants import KEY_SPLIT_RE
from autokey.iomediator.key import Key
from autokey import common

def form_macro_split_re():
    # Lookbehind to check if next character was escaped.
    # Only handles a single escaping.
    notEscd=r'(?<!\\)'
    # re = "(?<!\\\\)(<.*(?=(?<!\\\\))>)"
    # re = escd+"<"+''+"[^<>]+"+escd+r">\+?"
    # re = escd+"<"+''+r".*?=[^\\]>"
    # Surround in a capture group so that the contents of the match is also
    # returned when splitting.
    # re = "(?<!\\\\)(<.*(?=(?<!\\\\))>\\+?)"
    re = "(?<!\\\\)(<.*(?=(?<!\\\\)>)>)"
    # notEscd=''
    re = notEscd + "(<.*(?=" + notEscd + ">)>)"
    re = notEscd + "(<[^"+notEscd+">]+>)"
    re = notEscd + "(<.*(?=>)"+notEscd+">)"
    re = notEscd + "(<[^>]*"+notEscd+">)"
    # re = "(?<=[^\\\\]<.*?=[^\\\\]>)"
    print('re', re)
    return re
MACRO_SPLIT_RE = re.compile(form_macro_split_re())
#     return re.split(r'(?<!\\)' + splitchar, string)
# KEY_SPLIT_RE = re.compile("(<[^<>]+>\+?)")


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


# def split_except_escaped(splitchar, string):
#     return re.split(r'(?<!\\)' + splitchar, string)

# def split_except_escaped(string, delimiter):
#     if len(delimiter) != 1:
#         raise ValueError('Invalid delimiter: ' + delimiter)
#     ln = len(string)
#     i = 0
#     j = 0
#     while j < ln:
#         if string[j] == '\\':
#             if j + 1 >= ln:
#                 yield string[i:j]
#                 return
#             j += 1
#         elif string[j] == delimiter:
#             yield string[i:j]
#             i = j + 1
#         j += 1
#     yield string[i:j]

# Taken from
# https://rosettacode.org/wiki/Tokenize_a_string_with_escaping#Python
def split_except_escaped(a, separator = ' ', escape = '\\'):
    '''
        >>> print(token_with_escape('one^|uno||three^^^^|four^^^|^cuatro|'))
        ['one|uno', '', 'three^^', 'four^|cuatro', '']
    '''
    result = []
    token = ''
    state = 0
    for c in a:
        if state == 0:
            if c == escape:
                state = 1
            elif c == separator:
                result.append(token)
                token = ''
            else:
                token += c
        elif state == 1:
            token += c
            state = 0
    result.append(token)
    return result

# Escape any escaped angle brackets
def encode_escaped_brackets(s):
    # If you need a literal '\' at the end of the macro args... IDK. Add a
    # space before the >?
    # If you need a literal \>, just add an extra \.
    # s.replace("\\\\", chr(27)) # ASCII Escape
    # Use arbitrary nonprinting ascii to represent escaped char.
    # Easier than having to parse escape chars...
    s = s.replace("\\<", chr(0x1e))  # Record seperator
    s = s.replace("\\>", chr(0x1f))  # unit seperator
    # s.replace(chr(27), "\\")
    return s


def decode_escaped_brackets(s):
    s = s.replace(chr(0x1e), '<')  # Record seperator
    s = s.replace(chr(0x1f), '>')  # unit seperator
    return s

def sections_decode_escaped_brackets(sections):
    for i, s in enumerate(sections):
        sections[i] = decode_escaped_brackets(s)


# This must be passed a string containing only one macro.
def extract_tag(s):
    print(s)
    if not isinstance(s, str):
        raise TypeError
    extracted = [split_except_escaped(p, r'>')[0]
                 for p in split_except_escaped(s, r'<') if '>' in p]
    extracted = [p.split('>')[0]
                 for p in s.split('<') if '>' in p]
    print('extracted tag', (extracted))
    if len(extracted) == 0:
        return s
    else:
        return ''.join(extracted)

# Adapted from
#http://stackoverflow.com/questions/4284991/parsing-nested-parentheses-in-python-grab-content-by-level
def parse_nested_brackets(string, brackets=('<','>')):
    """Generate parenthesized contents in string as pairs (level, contents)."""
    stack = []
    for i, c in enumerate(string):
        if c == brackets[0]:
            # If escaped
            if i==0 or (i > 0 and string[i-1] != '\\'):
                stack.append(i)
        elif c == brackets[1] and stack:
            # If escaped
            if i==0 or (i > 0 and string[i-1] != '\\'):
                start = stack.pop()
                yield (len(stack), string[start: i + 1])



def split_phase_macros(content):
    notEscd=r'(?<!\\)'
    rx=notEscd + '<'
    sections = re.split(rx, content)
    print(sections)
    # while re.match(rx, content):

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

    def expand_macro(self, string):
        sections = [string]
        for macroClass in self.macros:
            sections = macroClass.process(sections)
        return ''.join(sections)

    # Split expansion.string, expand and process its macros, then
    # replace with the results.
    def process_expansion_macros(self, content):
        # Split into sections with <> macros in them.
        # Using the Key split regex works for now.
        print('content', content)
        print('re', form_macro_split_re())

        content = encode_escaped_brackets(content)
        content_sections = MACRO_SPLIT_RE.split(content)
        print('sections', content_sections)

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

    def _extract_macro(self, section):
        content = extract_tag(section)
        content = decode_escaped_brackets(content)
        # type is space-separated from rest of macro.
        # Cursor macros have no space.
        if ' ' in content:
            macro_type, macro = content.split(' ', 1)
        else:
            macro_type, macro = (content, '')
        return macro_type, macro


    def process(self, sections):
        for i, section in enumerate(sections):
            # if MACRO_SPLIT_RE.match(section):
            if KEY_SPLIT_RE.match(section):
                macro_type, macro = self._extract_macro(sections[i])
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
        macro_type, macro = self._extract_macro(sections[i])
        args = self._get_args(macro)
        self.engine.run_script_from_macro(args)
        return self.engine._get_return_value()


class DateMacro(AbstractMacro):

    ID = "date"
    TITLE = _("Insert date")
    ARGS = [("format", _("Format"))]

    def do_process(self, sections, i):
        macro_type, macro = self._extract_macro(sections[i])
        print('date macro', macro)
        format_ = self._get_args(macro)["format"]
        date = datetime.datetime.now()
        date = date.strftime(format_)
        sections[i] = date
        return sections


class FileContentsMacro(AbstractMacro):

    ID = "file"
    TITLE = _("Insert file contents")
    ARGS = [("name", _("File name"))]

    def do_process(self, sections, i):
        macro_type, macro = self._extract_macro(sections[i])
        name = self._get_args(macro)["name"]

        with open(name, "r") as inputFile:
            sections[i] = inputFile.read()

        return sections
