
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

import threading, re, time
from iomediator import Key, MODIFIERS
from configurationmanager import *

# Xlib Interface ----
from Xlib import X, XK, display, error
from Xlib.ext import record, xtest
from Xlib.protocol import rq, event

import select

# Modifiers
SHIFT = 'XK_Shift_L'
SHIFT_R = 'XK_Shift_R'
CAPSLOCK = 'XK_Caps_Lock'
CONTROL = 'XK_Control_L'
CONTROL_R = 'XK_Control_R'
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
           SHIFT_R : Key.SHIFT,
           CAPSLOCK : Key.CAPSLOCK,
           CONTROL : Key.CONTROL,
           CONTROL_R : Key.CONTROL,
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
        
    def __init__(self, mediator, testMode=False):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("XLibInterface-thread")
        self.mediator = mediator
        self.local_dpy = display.Display()
        self.record_dpy = display.Display()
        self.rootWindow = self.local_dpy.screen().root
        self.lock = threading.RLock()
        self.lastChars = [] # TODO QT4 Workaround - remove me once the bug is fixed
        self.testMode = testMode
        #self.cancelling = False
        
        #self.rootWindow.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask|X.ButtonPressMask)
        
        # Check for record extension 
        #if not self.record_dpy.has_extension("RECORD"):
        #    raise Exception("Your X-Server does not have the RECORD extension available/enabled.")                            
        
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

        #self.keyCodes[Key.ALT_GR] = 113
        #self.keyNames[113] = Key.ALT_GR
        
        if self.testMode:
            print repr(self.keyCodes)
        
    def keymap_test(self):
        print "XK keymap:"
        for attr in XK.__dict__.iteritems():
            if attr[0].startswith("XK"):
                print "%s, %s" % (attr[0], attr[1])        
        
        print "The following is a printout of how your X server maps each character"
        for char in "`1234567890-=~!@#$%^&*()qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?":
            keyCodeList = self.local_dpy.keysym_to_keycodes(ord(char))
            if len(keyCodeList) > 0:
                #keyCode, offset = keyCodeList[0]
                #print "[%s], %d, %d" % (char, keyCode, offset)
                print "[" + char + "] : " + repr(keyCodeList)
            else:
                print "No mapping for [" + char + "]"
                
        print "The following is a test for Alt-Gr modifier mapping. Please open a text editing program for this test."
        print "After 10 seconds, the test will commence. 6 key events will be sent. Please monitor the output and record"
        print "which of the 6 events produces a '{' (left curly brace)"
        time.sleep(10)
        keyCodeList = self.local_dpy.keysym_to_keycodes(ord("{"))
        keyCode, offset = keyCodeList[0]
        self.__sendKeyCode(keyCode, X.ShiftMask)
        time.sleep(0.5)
        self.__sendKeyCode(keyCode, X.Mod1Mask)
        time.sleep(0.5)
        self.__sendKeyCode(keyCode, X.Mod2Mask)
        time.sleep(0.5)
        self.__sendKeyCode(keyCode, X.Mod3Mask)
        time.sleep(0.5)
        self.__sendKeyCode(keyCode, X.Mod4Mask)
        time.sleep(0.5)
        self.__sendKeyCode(keyCode, X.Mod5Mask)
        print "Test complete. Now, please press the Alt-Gr key a few times (on its own)"
        
    def run_new(self):
        while not self.cancelling:
            #readable, w, e = select.select([self.local_dpy], [], [], 1)
            
            #if self.local_dpy in readable:
                #for i in range(self.local_dpy.pending_events()):
                
                    
            event = self.local_dpy.next_event()
            print "got event"
            if event.type == X.KeyPress:
                self.__handleKeyPress(event.detail)
            elif event.type == X.KeyRelease:
                self.__handleKeyRelease(event.detail)
            elif event.type == X.ButtonPress:
                self.mediator.handle_mouse_click()
            elif event.type == X.MappingNotify:
                self.__updateMapping(event)
                        
    def __updateMapping(self, event):
        print "update keyboard mapping"
        self.local_dpy.refresh_keyboard_mapping(event)        
        
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
        
    def cancel_new(self):
        self.cancelling = True
        self.local_dpy.flush()
        self.join()
        
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
                return "<unknown>"
    
    def send_string(self, string):
        """
        Send a string of printable characters.
        """
        for char in string:
            keyCodeList = self.local_dpy.keysym_to_keycodes(ord(char))
            if len(keyCodeList) > 0:
                keyCode, offset = keyCodeList[0]
                if offset == 1:
                    self.__sendKeyCode(keyCode, X.ShiftMask)
                elif offset == 2:
                    self.__sendKeyCode(keyCode, X.Mod1Mask)
                elif offset == 3:
                    self.__sendKeyCode(keyCode, X.Mod2Mask)
                elif offset == 4:
                    self.__sendKeyCode(keyCode, X.Mod3Mask)
                elif offset == 5:
                    self.__sendKeyCode(keyCode, X.Mod4Mask)
                elif offset == 6:
                    self.__sendKeyCode(keyCode, X.Mod5Mask)
                else:
                    self.__sendKeyCode(keyCode)                    
            else:
                self.send_unicode_char(char)
                
    def send_key(self, keyName):
        """
        Send a specific non-printing key, eg Up, Left, etc
        """
        self.__sendKeyCode(self.__lookupKeyCode(keyName))
        
    def send_modified_key(self, keyName, modifiers):
        """
        Send a modified key (e.g. when emulating a hotkey)
        """
        for modifier in modifiers:
            modifierCode = self.keyCodes[modifier]
            xtest.fake_input(self.rootWindow, X.KeyPress, modifierCode)
            
        keyCode = self.__lookupKeyCode(keyName)
        xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
        xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
        
        for modifier in modifiers:
            modifierCode = self.keyCodes[modifier]
            xtest.fake_input(self.rootWindow, X.KeyRelease, modifierCode)
            
    def send_unicode_char(self, char):
        self.send_modified_key('u', [Key.CONTROL, Key.SHIFT])
        
        keyDigits = "%04x" % ord(char)
        
        for digit in keyDigits:
            keyCode = self.__lookupKeyCode(digit)
            xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
            xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
            
        keyCode = self.__lookupKeyCode('\n')
        xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
        xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
        
    def flush(self):
        self.local_dpy.flush()
        self.lastChars = []
        
    def press_key(self, keyName):
        #xtest.fake_input(self.rootWindow, X.KeyPress, self.__lookupKeyCode(keyName))
        self.__sendKeyPressEvent(self.__lookupKeyCode(keyName), 0)
        
    def release_key(self, keyName):
        #xtest.fake_input(self.rootWindow, X.KeyRelease, self.__lookupKeyCode(keyName))
        self.__sendKeyReleaseEvent(self.__lookupKeyCode(keyName), 0)  

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
        if self.testMode:
            print repr(keyCode)
        self.lock.acquire()
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_down(modifier)
        else:
            self.mediator.handle_keypress(keyCode, self.__getWindowTitle())
            
    def __handleKeyRelease(self, keyCode):
        try:
            self.lock.release()
        except RuntimeError, e:
            pass # ignore releasing of lock when not acquired 
                 # just means we got a KeyRelease with no matching KeyPress
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
    
    #def __sendKeyCode(self, keyCode):
    #    xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
    #    xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
    
    def __sendKeyCode(self, keyCode, modifiers=0):
        if ConfigurationManager.SETTINGS[ENABLE_QT4_WORKAROUND]:
            self.__doQT4Workaround(keyCode)
        self.__sendKeyPressEvent(keyCode, modifiers)
        self.__sendKeyReleaseEvent(keyCode, modifiers)        
        
    def __doQT4Workaround(self, keyCode):
        if len(self.lastChars) > 0:
            if keyCode in self.lastChars and not self.lastChars[-1] == keyCode:
                time.sleep(0.0125)
                #print "waiting"

        self.lastChars.append(keyCode)
        
        if len(self.lastChars) > 10:
            self.lastChars.pop(0)
        
        #print self.lastChars
        
    def __sendKeyPressEvent(self, keyCode, modifiers):
        focus = self.local_dpy.get_input_focus().focus
        keyEvent = event.KeyPress(
                                  detail=keyCode,
                                  time=X.CurrentTime,
                                  root=self.rootWindow,
                                  window=focus,
                                  child=X.NONE,
                                  root_x=1,
                                  root_y=1,
                                  event_x=1,
                                  event_y=1,
                                  state=modifiers,
                                  same_screen=1
                                  )
        focus.send_event(keyEvent)
        
    def __sendKeyReleaseEvent(self, keyCode, modifiers):
        focus = self.local_dpy.get_input_focus().focus
        keyEvent = event.KeyRelease(
                                  detail=keyCode,
                                  time=X.CurrentTime,
                                  root=self.rootWindow,
                                  window=focus,
                                  child=X.NONE,
                                  root_x=1,
                                  root_y=1,
                                  event_x=1,
                                  event_y=1,
                                  state=modifiers,
                                  same_screen=1
                                  )
        focus.send_event(keyEvent)
        
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

class MockMediator:
    """
    Mock IoMediator for testing purposes.
    """
    
    def handle_modifier_down(self, modifier):
        pass
        
    def handle_modifier_up(self, modifier):
        pass    

    def handle_keypress(self, keyCode, windowName):
        pass
    
    def handle_mouse_click(self):
        pass
        

        
if __name__ == "__main__":
    import time
    x = XLibInterface(MockMediator(), True)
    x.start()
    x.keymap_test()
    time.sleep(10.0)
    #time.sleep(4.0)
    #x.send_unicode_key([0, 3, 9, 4])
    x.cancel()
    print "Test completed. Thank you for your assistance in improving AutoKey!"
