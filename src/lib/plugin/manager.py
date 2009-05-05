import re
from plugins import *

TOKEN_RE = re.compile("(\$\(.*?\))", re.UNICODE)

class PluginManager:
    
    def __init__(self):
        self.plugins = {}
        self.actionMap = {}
        
        for className in PLUGINS:
            instance = eval(className)()
            self.plugins[instance.get_id()] = instance
            self.actionMap[instance.get_action()] = instance.get_id()
    
    def get_action_list(self):
        """
        Gets a list of strings, each describing the action of a plugin e.g. "Current Date/Time".
        """
        return self.actionMap.keys()
    
    def get_token(self, action, parentWindow):
        pluginId = self.actionMap[action]
        return self.plugins[pluginId].get_token(parentWindow)
        
    def process_expansion(self, expansion, buffer):
        """
        Tokenise the given expansion, and dispatch the tokens to the relevant plugins for replacement.
        Then return the finalised expansion.
        """
        tokens = TOKEN_RE.split(expansion.string)
        finalString = []
        
        for token in tokens:
            if TOKEN_RE.match(token):
                # Identify plugin
                pluginId = token.split(' ', 1)[0][2:]
                try:
                    finalString.append(self.plugins[pluginId].get_string(token, buffer))
                    expansion.backspaces += self.plugins[pluginId].get_backspace_count() 
                except Exception, e:
                    raise PluginError(str(e))
            else:
                finalString.append(token)
                
        expansion.string = ''.join(finalString)
        
        
class PluginError(Exception):
    pass