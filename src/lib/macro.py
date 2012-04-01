from iomediator import KEY_SPLIT_RE, Key
import common

if common.USING_QT:
    from PyKDE4.kdecore import ki18n
    from PyKDE4.kdeui import KMenu, KAction
    from PyQt4.QtCore import SIGNAL
    _ = ki18n

    class MacroAction(KAction):

        def __init__(self, menu, macro, callback):
            KAction.__init__(self, macro.TITLE.toString(), menu)
            self.macro = macro
            self.callback = callback
            self.connect(self, SIGNAL("triggered()"), self.on_triggered)

        def on_triggered(self):
            self.callback(self.macro)

else:
    from gi.repository import Gtk

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

    def get_token(self):
        ret = "<%s" % self.ID
        
        if len(self.ARGS) == 0:
            ret += ">"
        else:
            for k, v in self.ARGS:
                ret += " "
                ret += k
                ret += "="
            ret += ">"
        
        return ret
            
    def _can_process(self, token):
        if KEY_SPLIT_RE.match(token):
            return token[1:-1].split(' ', 1)[0] == self.ID
        else:
            return False
        
    def _get_args(self, token):
        l = token[:-1].split(' ')
        ret = {}
                
        if len(l) > 1:
            for arg in l[1:]:
                key, val = arg.split('=', 1)
                ret[key] = val

        for k, v in self.ARGS:
            if k not in ret:
                raise Exception("Missing mandatory argument '%s' for macro '%s'" % (k, self.ID))
        
        return ret
        
    def process(self, parts):
        for i in xrange(len(parts)):
            if self._can_process(parts[i]):
                self.do_process(parts, i)
    

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
        parts[i] = self.engine.get_return_value()


class DateMacro(AbstractMacro):

    ID = "date"
    TITLE = _("Insert date")
    ARGS = [("format", _("Format"))]
    
    def do_process(self, parts, i):
        format = self._get_args(parts[i])["format"]
        date = datetime.datetime.now().strftime(format)
        parts[i] = date


class FileContentsMacro(AbstractMacro):

    ID = "file"
    TITLE = _("Insert file contents")
    ARGS = [("name", _("File name"))]
    
    def do_process(self, parts, i):
        name = self._get_args(parts[i])["name"]
        
        with open(name, "r") as inputFile:
            parts[i] = inputFile.read()
    
