
# Copyright (C) 2008 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

__all__ = ["XLibInterface"]

import threading, re
from iomediator import Key, MODIFIERS

# Xlib Interface ----

from Xlib import X, XK, display, error
from Xlib.ext import record, xtest
from Xlib.protocol import rq

# Modifiers
SHIFT = 'XK_Shift_L'
CAPSLOCK = 'XK_Caps_Lock'
CONTROL = 'XK_Control_L'
ALT = 'XK_Alt_L'
ALT_GR = 'XK_Alt_R'
SUPER = 'XK_Super_L'

# Misc Keys
SPACE = 'XK_space'
TAB = 'XK_Tab'
LEFT = 'XK_Left'
RIGHT = 'XK_Right'
UP = 'XK_Up'
DOWN = 'XK_Down'
RETURN = 'XK_Return'
BACKSPACE = 'XK_BackSpace'

# Function Keys
F1 = "XK_F1"
F2 = "XK_F2"
F3 = "XK_F3"
F4 = "XK_F4"
F5 = "XK_F5"
F6 = "XK_F6"
F7 = "XK_F7"
F8 = "XK_F8"
F9 = "XK_F9"
F10 = "XK_F10"
F11 = "XK_F11"
F12 = "XK_F12"

# Other
ESCAPE = "XK_Escape"
INSERT = "XK_Insert"
DELETE = "XK_Delete"
HOME = "XK_Home"
END = "XK_End"
PAGE_UP = "XK_Page_Up"
PAGE_DOWN = "XK_Page_Down"

KEY_MAP = {
           SHIFT : Key.SHIFT,
           CAPSLOCK : Key.CAPSLOCK,
           CONTROL : Key.CONTROL,
           ALT : Key.ALT,
           ALT_GR : Key.ALT_GR,
           SUPER : Key.SUPER,
           SPACE : Key.SPACE,
           TAB : Key.TAB,
           LEFT : Key.LEFT,
           RIGHT : Key.RIGHT,
           UP : Key.UP,
           DOWN : Key.DOWN,
           RETURN : Key.RETURN,
           BACKSPACE : Key.BACKSPACE,
           F1 : Key.F1,
           F2 : Key.F2,
           F3 : Key.F3,
           F4 : Key.F4,
           F5 : Key.F5,
           F6 : Key.F6,
           F7 : Key.F7,
           F8 : Key.F8,
           F9 : Key.F9,
           F10 : Key.F10,
           F11 : Key.F11,
           F12 : Key.F12,
           ESCAPE : Key.ESCAPE,
           INSERT : Key.INSERT,
           DELETE : Key.DELETE,
           HOME : Key.HOME,
           END : Key.END,
           PAGE_UP : Key.PAGE_UP,
           PAGE_DOWN : Key.PAGE_DOWN           
           }

class XLibInterface(threading.Thread):
        
    def __init__(self, mediator):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("XLibInterface-thread")
        self.mediator = mediator
        self.local_dpy = display.Display()
        self.record_dpy = display.Display()
        self.rootWindow = self.local_dpy.screen().root
        self.lock = threading.RLock()
        
        # Check for record extension 
        if not self.record_dpy.has_extension("RECORD"):
            raise Exception("Your X-Server does not have the RECORD extension available/enabled.")                            
        
        # Map of keyname to keycode
        self.keyCodes = {}
        # Map of keycode to keyname
        self.keyNames = {}
        
        # Create map of iomediator key codes to X key codes
        keyList = KEY_MAP.keys()
        for xkKeyName in keyList:
            keyName = KEY_MAP[xkKeyName]
            keyCode = self.local_dpy.keysym_to_keycode(getattr(XK, xkKeyName))
            self.keyCodes[keyName] = keyCode
            self.keyNames[keyCode] = keyName

        self.keyCodes[Key.ALT_GR] = 113
        self.keyNames[113] = Key.ALT_GR
        
    def run(self):
        # Create a recording context; we only want key and mouse events
        self.ctx = self.record_dpy.record_create_context(
                0,
                [record.AllClients],
                [{
                        'core_requests': (0, 0),
                        'core_replies': (0, 0),
                        'ext_requests': (0, 0, 0, 0),
                        'ext_replies': (0, 0, 0, 0),
                        'delivered_events': (0, 0),
                        'device_events': (X.KeyPress, X.ButtonPress), #X.KeyRelease, 
                        'errors': (0, 0),
                        'client_started': False,
                        'client_died': False,
                }])

        # Enable the context; this only returns after a call to record_disable_context,
        # while calling the callback function in the meantime
        self.record_dpy.record_enable_context(self.ctx, self.__processEvent)
        # Finally free the context
        self.record_dpy.record_free_context(self.ctx)
        
    def cancel(self):
        self.local_dpy.record_disable_context(self.ctx)
        self.local_dpy.flush()
        self.join()
        
    def lookup_string(self, keyCode, shifted):
        if keyCode in self.keyNames.keys():
            return self.keyNames[keyCode]
        else:
            try:
                if shifted:
                    return unichr(self.local_dpy.keycode_to_keysym(keyCode, 1))
                else:
                    return unichr(self.local_dpy.keycode_to_keysym(keyCode, 0))
            except ValueError:
                return None
    
    def send_string(self, string):
        """
        Send a string of printable characters.
        """
        for char in string:
            keyCodeList = self.local_dpy.keysym_to_keycodes(ord(char))
            if len(keyCodeList) > 0:
                keyCode, offset = keyCodeList[0]
                if offset == 1:
                    self.press_key(Key.SHIFT)
                    self.__sendKeyCode(keyCode)
                    self.release_key(Key.SHIFT)
                elif offset == 2:
                    self.press_key(Key.ALT_GR)
                    self.__sendKeyCode(keyCode)
                    self.release_key(Key.ALT_GR)
                else:
                    self.__sendKeyCode(keyCode)                    
            else:
                self.send_key(char)
                
    def send_key(self, keyName):
        """
        Send a specific non-printing key, eg Up, Left, etc
        """
        self.__sendKeyCode(self.__lookupKeyCode(keyName))
        
    def flush(self):
        self.local_dpy.flush()
        
    def press_key(self, keyName):
        xtest.fake_input(self.rootWindow, X.KeyPress, self.__lookupKeyCode(keyName))
        
    def release_key(self, keyName):
        xtest.fake_input(self.rootWindow, X.KeyRelease, self.__lookupKeyCode(keyName))  

    def __processEvent(self, reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            print "* received swapped protocol data, cowardly ignored"
            return
        if not len(reply.data) or ord(reply.data[0]) < 2:
            # not an event
            return
        
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, self.record_dpy.display, None, None)
            if event.type == X.KeyPress:
                self.__handleKeyPress(event.detail)
            elif event.type == X.KeyRelease:
                self.__handleKeyRelease(event.detail)
            elif event.type == X.ButtonPress:
                self.mediator.handle_mouse_click()
                
    def __handleKeyPress(self, keyCode):
        self.lock.acquire()
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_down(modifier)
        else:
            self.mediator.handle_keypress(keyCode, self.__getWindowTitle())
            
    def __handleKeyRelease(self, keyCode):
        self.lock.release()
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_up(modifier)
                    
    def __decodeModifier(self, keyCode):
        """
        Checks if the given keyCode is a modifier key. If it is, returns the modifier name
        constant as defined in the iomediator module. If not, returns C{None}
        """
        if keyCode in self.keyNames.keys():
            keyName = self.keyNames[keyCode]
            if keyName in MODIFIERS:
                return keyName
        
        return None
    
    def __sendKeyCode(self, keyCode):
        xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
        xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
        
    def __lookupKeyCode(self, char):
        if char in self.keyCodes.keys():
            return self.keyCodes[char]
        else:
            try:
                code = self.local_dpy.keysym_to_keycode(ord(char))
                if code == 94:
                    return 59 # workaround < doesn't seem to get sent properly
                else:
                    return code
            except Exception, e:
                # TODO - improve this
                print "Unknown key name: " + char
                raise
            
    def __getWindowTitle(self):
        try:
            windowvar = self.local_dpy.get_input_focus().focus
            wmname = windowvar.get_wm_name()
            wmclass = windowvar.get_wm_class()
            
            if (wmname == None) and (wmclass == None):
                windowvar = windowvar.query_tree().parent
                wmname = windowvar.get_wm_name()

            return wmname
        except:
            return ""
        
if __name__ == "__main__":
    import time
    x = XLibInterface(None)
    x.start()
    time.sleep(10.0)
    #x.send_string("blah")
    x.cancel()
