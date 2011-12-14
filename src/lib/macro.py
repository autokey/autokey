from iomediator import KEY_SPLIT_RE, Key
import gtk

class MacroManager:
    
    def __init__(self, engine):
        self.macros = []
        
        self.macros.append(ScriptMacro(engine))
        self.macros.append(CursorMacro())
        
    def get_menu(self, callback):
        menu = gtk.Menu()
        
        for macro in self.macros:
            menuItem = gtk.MenuItem(macro.TITLE)
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
        return "<%s>" % self.ID

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
    

class CursorMacro(AbstractMacro):

    ID = "cursor"
    TITLE = _("Position cursor")
    ARGS = []
    
    def process(self, parts):
        for i in xrange(len(parts)):
            token = parts[i]
            if self._can_process(token):
                try:
                    lefts = len(''.join(parts[i+1:]))
                    parts.append(Key.LEFT * lefts)
                    parts[i] = ''
                    break # Only process the first occurrence
                except IndexError:
                    pass
                        
    
class ScriptMacro(AbstractMacro):

    ID = "script"
    TITLE = _("Run script")
    ARGS = [("name", _("Name")),
            ("args", _("Arguments (comma separated)"))]
    
    def __init__(self, engine):
        self.engine = engine
    
    def process(self, parts):
        for i in xrange(len(parts)):
            token = parts[i]
            if self._can_process(token):
                args = self._get_args(token)
                self.engine.run_script_from_macro(args)
                parts[i] = self.engine.get_return_value()


                
