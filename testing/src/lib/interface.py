
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

import threading, re

from Xlib import X, XK, display, error
from Xlib.ext import record, xtest
from Xlib.protocol import rq

import iomediator

def threaded(f):
    
    def wrapper(*args):
        t = threading.Thread(target=f, args=args)
        t.setDaemon(True)
        t.start()
        
    wrapper.__name__ = f.__name__
    wrapper.__dict__ = f.__dict__
    wrapper.__doc__ = f.__doc__
    return wrapper

# Xlib Interface ----

# Modifiers
SHIFT_REGEX = '^Shift'
CAPSLOCK_REGEX = '^Caps_Lock'
CONTROL_REGEX = '^Control'
ALT_REGEX = '^Alt_L'
ALT_GR_REGEX = '^Alt_R'
SUPER_REGEX = '^Super'

SPACE_REGEX = '^space'
TAB_REGEX = '^Tab'
LEFT_REGEX = '^Left'
UP_REGEX = '^Up'
RETURN_REGEX = '^Return'
BACKSPACE_REGEX = '^BackSpace'

REGEX_MAP = {
           SHIFT_REGEX : iomediator.KEY_SHIFT,
           CAPSLOCK_REGEX : iomediator.KEY_CAPSLOCK,
           CONTROL_REGEX : iomediator.KEY_CONTROL,
           ALT_REGEX : iomediator.KEY_ALT,
           ALT_GR_REGEX : iomediator.KEY_ALT_GR,
           SUPER_REGEX : iomediator.KEY_SUPER,
           SPACE_REGEX : iomediator.CHAR_SPACE,
           TAB_REGEX : iomediator.KEY_TAB,
           LEFT_REGEX : iomediator.KEY_LEFT,
           UP_REGEX : iomediator.KEY_UP,
           RETURN_REGEX : iomediator.CHAR_NEWLINE,
           BACKSPACE_REGEX : iomediator.KEY_BACKSPACE
           }

class XLibInterface(threading.Thread):
        
    def __init__(self, mediator):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.mediator = mediator
        self.local_dpy = display.Display()
        self.record_dpy = display.Display()
        self.rootWindow = self.local_dpy.screen().root
        
        # Map of keyname to keycode
        self.keyCodes = {}
        # Map of keycode to keyname
        self.keyNames = {}
        
        # Create map of iomediator key codes to X key codes
        regexList = REGEX_MAP.keys()
        for name in dir(XK):
            for regex in regexList:
                if re.match(regex, name[3:]):
                    keyName = REGEX_MAP[regex]
                    keyCode = self.local_dpy.keysym_to_keycode(getattr(XK, name))
                    self.keyCodes[keyName] = keyCode
                    self.keyNames[keyCode] = keyName
                    regexList.remove(regex)
                    
            if len(regexList) == 0:
                # if all regexes have been mapped, leave the loop
                break
        
    def run(self):
        if not self.record_dpy.has_extension("RECORD"):
            print "RECORD extension not found"
            # TODO raise exception

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
        #self.join()
        
    def lookup_string(self, keyCode, shifted):
        if keyCode in self.keyNames.keys():
            return self.keyNames[keyCode]
        else:
            if shifted:
                return unichr(self.local_dpy.keycode_to_keysym(keyCode, 1))
            else:
                return unichr(self.local_dpy.keycode_to_keysym(keyCode, 0))
    
    def send_string(self, string):
        """
        Send a string of printable characters.
        """
        for char in string:
            keyCodeList = self.local_dpy.keysym_to_keycodes(ord(char))
            if len(keyCodeList) > 0:
                keyCode, offset = keyCodeList[0]
                if offset == 1:
                    self.press_key(iomediator.KEY_SHIFT)
                    self.__sendKeyCode(keyCode)
                    self.release_key(iomediator.KEY_SHIFT)
                elif offset == 2:
                    self.press_key(iomediator.KEY_ALT_GR)
                    self.__sendKeyCode(keyCode)
                    self.release_key(iomediator.KEY_ALT_GR)
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
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_down(modifier)
        #else:
        #    self.mediator.handle_keypress(keyCode)
            
    def __handleKeyRelease(self, keyCode):
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_up(modifier)
        else:
            self.mediator.handle_keypress(keyCode)
                    
    def __decodeModifier(self, keyCode):
        """
        Checks if the given keyCode is a modifier key. If it is, returns the modifier name
        constant as defined in the iomediator module. If not, returns C{None}
        """
        if keyCode in self.keyNames.keys():
            keyName = self.keyNames[keyCode]
            if keyName in iomediator.MODIFIERS:
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
        
        

class AtSpiInterface:
    
    pass

if __name__ == "__main__":
    import time
    x = XLibInterface(None)
    x.start()
    time.sleep(2.0)
    x.send_string("blah")
    x.cancel()
