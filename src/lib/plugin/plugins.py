import datetime, gtk, subprocess

PLUGINS = ["CursorPositionPlugin", "CurrentDatePlugin", "ExecCommandPlugin", "InsertPreviousWordPlugin"]

CURSOR_POSITION_TOKEN = "$(cursor )"

class AbstractPlugin:
    
    def _parse_arguments(self, token):
        result = {}
        token = token.encode("utf-8")
        argPart = token.split(' ', 1)[1][:-1]
        args = argPart.split('&')
        
        for arg in args:
            key, value = arg.split('=', 1)
            result[key] = value
            
        return result
    
    def _build_token(self, id, arguments):
        result = []
        result.append("$(")
        result.append(id)
        result.append(' ')

        for key, value in arguments.iteritems():
            result.append(key)
            result.append('=')
            result.append(value)
            result.append('&')
        
        if len(arguments) > 0:
            result = result[:-1]
        result.append(")")
        return ''.join(result)
    
    def get_backspace_count(self):
        return 0
        
class InsertPreviousWordPlugin(AbstractPlugin):
    
    def __init__(self):
        self.__backspaceCount = 0
    
    def get_id(self):
        return "sub"
    
    def get_action(self):
        return "Substitute preceding word"
    
    def get_token(self, parentWindow):
        return self._build_token(self.get_id(), {})
    
    def get_string(self, token, buffer):
        partBefore, _, _ = buffer.rpartition('~')
        if len(partBefore) > 0:
            lastLine = partBefore.splitlines()[-1]
            lastWord = lastLine.split()[-1]
            self.__backspaceCount = len(lastWord) + 1
            return lastWord
        else:
            return ''
        
    def get_backspace_count(self):
        returnValue = self.__backspaceCount
        self.__backspaceCount = 0
        return returnValue

class CursorPositionPlugin(AbstractPlugin):
    
    def get_id(self):
        return "cursor"
    
    def get_action(self):
        return "Position the cursor"
    
    def get_token(self, parentWindow):
        return CURSOR_POSITION_TOKEN
    
    def get_string(self, token, buffer):
        return CURSOR_POSITION_TOKEN
    
    
class CurrentDatePlugin(AbstractPlugin):
    
    DATETIME_FORMATS = ["%A %d %B", "%d/%m/%Y", "%d/%m/%Y %I:%M:%S %p", "%H:%M:%S"]
    
    def get_id(self):
        return "datetime"
    
    def get_action(self):
        return "Current Date/Time"
    
    def get_token(self, parentWindow):
        dateMap = {}
        now = datetime.datetime.now()
        
        for format in self.DATETIME_FORMATS:
            dateMap[now.strftime(format)] = format
        
        dlg = _FormatChoiceDialog(parentWindow, dateMap.keys())
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            format = dlg.get_choice()
            dateFormat = dateMap[format]
            args = {}
            args["format"] = dateFormat
            dlg.destroy()
            return self._build_token(self.get_id(), args)
        else:
            dlg.destroy()
            return None 
    
    def get_string(self, token, buffer):
        args = self._parse_arguments(token)
        now = datetime.datetime.now()
        return now.strftime(args["format"])
    
    
class _FormatChoiceDialog(gtk.Dialog):
    
    def __init__(self, parent, choices):
        """
        @param parent: parent window of the dialog
        """
        gtk.Dialog.__init__(self, "Choose a format", parent, gtk.DIALOG_MODAL,
                             (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.combo = gtk.combo_box_new_text()
        for choice in choices:
            self.combo.append_text(choice)
        self.combo.set_active(0)
        
        self.vbox.pack_start(gtk.Label("Select a date/time format"), padding=5)
        self.vbox.pack_start(self.combo, padding=5)
        self.show_all()
        
    def get_choice(self):
        return self.combo.get_active_text()


class ExecCommandPlugin(AbstractPlugin):
    
    def get_id(self):
        return "exec"
    
    def get_action(self):
        return "Run shell command"
    
    def get_token(self, parentWindow):
        args = {}
        dlg = _ConfigureCommandDialog(parentWindow)
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            args["command"] = dlg.get_command()
            args["output"] = dlg.get_output()
            dlg.destroy()
            return self._build_token(self.get_id(), args)
        else:
            dlg.destroy()
            return None        
    
    def get_string(self, token, buffer):
        args = self._parse_arguments(token)
        pipe = subprocess.Popen(args["command"], shell=True, bufsize=-1, stdout=subprocess.PIPE).stdout

        if args["output"] == "true":
            result = pipe.read()
            return result.strip()
        else:
            return ""
        
        
class _ConfigureCommandDialog(gtk.Dialog):
    
    def __init__(self, parent):
        """
        @param parent: parent window of the dialog
        """
        gtk.Dialog.__init__(self, "Enter a command", parent, gtk.DIALOG_MODAL,
                             (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        
        self.command = gtk.Entry()
        self.ignoreOutput = gtk.CheckButton("Ignore command output")
        
        self.vbox.pack_start(gtk.Label("Enter a command to be executed"), padding=5)
        self.vbox.pack_start(self.command, padding=5)
        self.vbox.pack_start(self.ignoreOutput, padding=5)
        self.show_all()
        
    def get_command(self):
        return self.command.get_text()
    
    def get_output(self):
        if self.ignoreOutput.get_active():
            return "false"
        else:
            return "true"