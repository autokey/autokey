from iomediator import KEY_SPLIT_RE, Key

class MacroManager:
    
    def __init__(self, engine):
        self.macros = []
        
        self.macros.append(ScriptMacro(engine))
        self.macros.append(CursorMacro())
        
    def process_expansion(self, expansion):
        parts = KEY_SPLIT_RE.split(expansion.string)
        
        for macro in self.macros:        
            macro.process(parts)
        
        expansion.string = ''.join(parts)
        

class AbstractMacro:

    def _can_process(self, token):
        if KEY_SPLIT_RE.match(token):
            return token[1:-1].split(' ', 1)[0] == self.ID
        else:
            return False
        
    def _get_args(self, token):
        l = token[:-1].split(' ')
        if len(l) > 1:
            return l[1:]
        else:
            return []
        

class CursorMacro(AbstractMacro):

    ID = "cursor"
    
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
    
    def __init__(self, engine):
        self.engine = engine
    
    def process(self, parts):
        for i in xrange(len(parts)):
            token = parts[i]
            if self._can_process(token):
                args = self._get_args(token)
                self.engine.run_script_from_macro(args)
                parts[i] = self.engine.get_return_value()
                
