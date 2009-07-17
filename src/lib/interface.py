# -*- coding: utf-8 -*-

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

__all__ = ["XRecordInterface", "EvDevInterface", "AtSpiInterface"]


import os, threading, re, time, socket, select, logging
try:
    import pyatspi
    HAS_ATSPI = True
except ImportError:
    HAS_ATSPI = False

from Xlib import X, XK, display, error
from Xlib.ext import record, xtest
from Xlib.protocol import rq, event

logger = logging.getLogger("interface")

# Misc
DOMAIN_SOCKET_PATH = "/tmp/autokey.daemon"
PACKET_SIZE = 32

# Modifiers
SHIFT = 'XK_Shift_L'
SHIFT_R = 'XK_Shift_R'
CAPSLOCK = 'XK_Caps_Lock'
CONTROL = 'XK_Control_L'
CONTROL_R = 'XK_Control_R'
ALT = 'XK_Alt_L'
ALT_R = 'XK_Alt_R'
ALT_GR = 'XK_ISO_Level3_Shift'
#ALT_GR = 'XK_Alt_R'
SUPER = 'XK_Super_L'
SUPER_R = 'XK_Super_R'
NUMLOCK = 'XK_Num_Lock'

# Misc Keys
SPACE = 'XK_space'
TAB = 'XK_Tab'
LEFT = 'XK_Left'
RIGHT = 'XK_Right'
UP = 'XK_Up'
DOWN = 'XK_Down'
RETURN = 'XK_Return'
BACKSPACE = 'XK_BackSpace'
SCROLL_LOCK = 'XK_Scroll_Lock'
PRINT_SCREEN = 'XK_Print'
PAUSE = 'XK_Pause'
MENU = 'XK_Menu'

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

# Keypad
KP_INSERT = "XK_KP_Insert"
KP_DELETE = "XK_KP_Delete"
KP_END = "XK_KP_End"
KP_DOWN = "XK_KP_Down"
KP_PAGE_DOWN = "XK_KP_Page_Down"
KP_LEFT = "XK_KP_Left"
KP_5 = "XK_KP_5"
KP_RIGHT = "XK_KP_Right"
KP_HOME = "XK_KP_Home"
KP_UP = "XK_KP_Up"
KP_PAGE_UP = "XK_KP_Page_Up"
KP_ENTER = "XK_KP_Enter"
KP_ADD = "XK_KP_Add"
KP_SUBTRACT = "XK_KP_Subtract"
KP_MULTIPLY = "XK_KP_Multiply"
KP_DIVIDE = "XK_KP_Divide"

# Other
ESCAPE = "XK_Escape"
INSERT = "XK_Insert"
DELETE = "XK_Delete"
HOME = "XK_Home"
END = "XK_End"
PAGE_UP = "XK_Page_Up"
PAGE_DOWN = "XK_Page_Down"


class XInterfaceBase(threading.Thread):
    """
    Encapsulates the common functionality for the two X interface classes.
    """
    
    def __init__(self, mediator, testMode):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("XInterface-thread")
        self.mediator = mediator
        self.localDisplay = display.Display()
        self.rootWindow = self.localDisplay.screen().root
        self.lock = threading.RLock()
        self.testMode = testMode
        self.lastChars = [] # TODO QT4 Workaround - remove me once the bug is fixed
        
        self.__initMappings()
        
    def __initMappings(self):
        # Map of keyname to keycode
        self.keyCodes = {}
        # Map of keycode to keyname
        self.keyNames = {}
        # One-way numpad key map - we only decode them
        self.numKeyNames = {}
        
        # Load xkb keysyms - related to non-US keyboard mappings
        XK.load_keysym_group('xkb')
        
        # Create map of iomediator key codes to X key codes
        keyList = KEY_MAP.keys()
        for xkKeyName in keyList:
            keyName = KEY_MAP[xkKeyName]
            keyCode = self.localDisplay.keysym_to_keycode(getattr(XK, xkKeyName))
            self.keyCodes[keyName] = keyCode
            self.keyNames[keyCode] = keyName

        altGrTuples = self.localDisplay.keysym_to_keycodes(XK.XK_ISO_Level3_Shift)
        for keyCode, level in altGrTuples:
            self.keyCodes[Key.ALT_GR] = keyCode
            self.keyNames[keyCode] = Key.ALT_GR
            
        # Create map of numpad keycodes, similar to above
        keyList = NUMPAD_MAP.keys()
        for xkKeyName in keyList:
            keyNames = NUMPAD_MAP[xkKeyName]
            keyCode = self.localDisplay.keysym_to_keycode(getattr(XK, xkKeyName))
            self.numKeyNames[keyCode] = keyNames
       
        logger.debug("Keycodes dict: %s", self.keyCodes)
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            self.keymap_test()
        
    def keymap_test(self):
        #logger.debug("XK keymap:")
        code = self.localDisplay.keycode_to_keysym(108, 0)
        for attr in XK.__dict__.iteritems():
            if attr[0].startswith("XK"):
                if attr[1] == code:
                    logger.debug("Alt-Grid: %s, %s", attr[0], attr[1])
        logger.debug(repr(self.localDisplay.keysym_to_keycodes(XK.XK_ISO_Level3_Shift)))
        
        logger.debug("X Server Keymap")
        for char in "\\|`1234567890-=~!@#$%^&*()qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?":
            keyCodeList = self.localDisplay.keysym_to_keycodes(ord(char))
            if len(keyCodeList) > 0:
                logger.debug("[%s] : %s", char, keyCodeList)
            else:
                logger.debug("No mapping for [%s]", char)
        
                
        #print "The following is a test for Alt-Gr modifier mapping. Please open a text editing program for this test."
        #print "After 10 seconds, the test will commence. 6 key events will be sent. Please monitor the output and record"
        #print "which of the 6 events produces a '{' (left curly brace)"
        #time.sleep(10)
        #keyCodeList = self.localDisplay.keysym_to_keycodes(ord("{"))
        #keyCode, offset = keyCodeList[0]
        #self.__sendKeyCode(keyCode, X.ShiftMask)
        #time.sleep(0.5)
        #self.__sendKeyCode(keyCode, X.Mod1Mask)
        #time.sleep(0.5)
        #self.__sendKeyCode(keyCode, X.Mod2Mask)
        #time.sleep(0.5)
        #self.__sendKeyCode(keyCode, X.Mod3Mask)
        #time.sleep(0.5)
        #self.__sendKeyCode(keyCode, X.Mod4Mask)
        #time.sleep(0.5)
        #self.__sendKeyCode(keyCode, X.Mod5Mask)
        #print "Test complete. Now, please press the Alt-Gr key a few times (on its own)"
        
    def lookup_string(self, keyCode, shifted, numlock, altGrid):
        if keyCode == 0:
            return "<unknown>"
        
        elif self.keyNames.has_key(keyCode):
            return self.keyNames[keyCode]
            
        elif self.numKeyNames.has_key(keyCode):
            values = self.numKeyNames[keyCode]
            if numlock:
                return values[1]
            else:
                return values[0]
                
        else:
            try:
                index = 0
                if shifted: index += 1 
                if altGrid: index += 4  
                return unichr(self.localDisplay.keycode_to_keysym(keyCode, index))
            except ValueError:
                return "<code%d>" % keyCode
    
    def send_string(self, string):
        """
        Send a string of printable characters.
        """
        logger.debug("Sending string: %s", string)
        for char in string:
            if self.keyCodes.has_key(char):
                self.send_key(char)
            else: 
                keyCodeList = self.localDisplay.keysym_to_keycodes(ord(char))
                if len(keyCodeList) > 0:
                    keyCode, offset = keyCodeList[0]
                    if offset == 1:
                        self.__sendKeyCode(keyCode, X.ShiftMask)
                    elif offset == 4:
                        self.send_modified_key(char, [Key.ALT_GR])
                    # TODO - I've given up trying to make it work the proper way
                    #elif offset == X.Mod1MapIndex:
                    #    print "mod1mask"
                    #    self.__sendKeyCode(keyCode, X.Mod1Mask)
                    #elif offset == X.Mod2MapIndex:
                    #    print "mod2mask"
                    #    self.__sendKeyCode(keyCode, X.Mod2Mask)
                    #elif offset == X.Mod3MapIndex:
                    #    print "mod3mask"
                    #    self.__sendKeyCode(keyCode, X.Mod3Mask)
                    #elif offset == X.Mod4MapIndex:
                    #    print "mod4mask"
                    #    self.__sendKeyCode(keyCode, X.Mod4Mask)
                    #elif offset == X.Mod5MapIndex:
                    #    print "mod5mask"
                    #    self.__sendKeyCode(keyCode, X.Mod5Mask)
                    else:
                        self.__sendKeyCode(keyCode)                    
                else:
                    self.send_unicode_char(char)
                    
    def send_key(self, keyName):
        """
        Send a specific non-printing key, eg Up, Left, etc
        """
        logger.debug("Send special key: [%s]", keyName)
        self.__sendKeyCode(self.__lookupKeyCode(keyName))
        
    def send_modified_key(self, keyName, modifiers):
        """
        Send a modified key (e.g. when emulating a hotkey)
        """
        logger.debug("Send modified key: modifiers: %s key: %s", modifiers, keyName)
        for modifier in modifiers:
            modifierCode = self.keyCodes[modifier.lower()]
            xtest.fake_input(self.rootWindow, X.KeyPress, modifierCode)
            
        keyCode = self.__lookupKeyCode(keyName)
        xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
        xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
        
        for modifier in modifiers:
            modifierCode = self.keyCodes[modifier.lower()]
            xtest.fake_input(self.rootWindow, X.KeyRelease, modifierCode)
            
    def send_unicode_char(self, char):
        logger.debug("Send unicode char: %s", char)
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
        self.localDisplay.flush()
        self.lastChars = []
        
    def press_key(self, keyName):
        self.__sendKeyPressEvent(self.__lookupKeyCode(keyName), 0)
        
    def release_key(self, keyName):
        self.__sendKeyReleaseEvent(self.__lookupKeyCode(keyName), 0)  
        
    def _handleKeyPress(self, keyCode):
        self.lock.acquire()
        
        # Initial attempt at detecting MappingNotify by polling for events
        r, w, x = select.select([self.localDisplay], [], [], 0)
        if self.localDisplay in r:
            for x in range(self.localDisplay.pending_events()):
                event = self.localDisplay.next_event()
                if event.type == X.MappingNotify:
                    self.__updateMapping(event)
        
        
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_down(modifier)
        else:
            self.mediator.handle_keypress(keyCode, self._getWindowTitle())
            
    def _handleKeyRelease(self, keyCode):
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
        if self.keyNames.has_key(keyCode):
            keyName = self.keyNames[keyCode]
            if keyName in MODIFIERS:
                return keyName
        
        return None
    
    def __updateMapping(self, event):
        logger.info("Got XMappingNotify - reloading keyboard mapping")
        self.localDisplay.refresh_keyboard_mapping(event)   
        self.__initMappings() 
    
    def __sendKeyCode(self, keyCode, modifiers=0):
        if ConfigManager.SETTINGS[ENABLE_QT4_WORKAROUND]:
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
        focus = self.localDisplay.get_input_focus().focus
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
        focus = self.localDisplay.get_input_focus().focus
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
        if self.keyCodes.has_key(char):
            return self.keyCodes[char]
        elif char.startswith("<code"):
            code = int(char[5:-1])
            return code
        else:
            # TODO I don't think this code is ever reached. Get rid of it at some point
            try:
                code = self.localDisplay.keysym_to_keycode(ord(char))
                return code
            except Exception, e:
                logger.error("Unknown key name: %s", char)
                raise
    
    def _getWindowTitle(self):
        try:
            windowvar = self.localDisplay.get_input_focus().focus
            wmname = windowvar.get_wm_name()
            wmclass = windowvar.get_wm_class()
            
            if (wmname == None) and (wmclass == None):
                windowvar = windowvar.query_tree().parent
                wmname = windowvar.get_wm_name()

            logger.debug("Window name: %s", str(wmname))
            return str(wmname)
        except:
            logger.debug("Unable to determine active window name")
            return ""


class EvDevInterface(XInterfaceBase):
    
    def __init__(self, mediator, testMode=False):
        XInterfaceBase.__init__(self, mediator, testMode)
        self.cancelling = False
        
        # Connect to event daemon
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        try:
            self.socket.connect(DOMAIN_SOCKET_PATH)
        except socket.error, e:
            raise Exception("Unable to connect to EvDev daemon:\n" + str(e))
        
    def cancel(self):
        self.cancelling = True
        #self.join()
        
    def run(self):
        logger.info("EvDev interface thread starting")
        while True:
            if self.cancelling:
                logger.info("EvDev interface thread terminated")
                break
            
            # Request next event
            try:
                data = self.socket.recv(PACKET_SIZE)
            except: continue
            
            data = data.strip()
            try:
                keyCode, button, state = data.split(',')
            except:
                logger.critical("Connection to EvDev daemon lost - terminating")
                break
            
            if keyCode:
                keyCode = int(keyCode)
                if state == '2':
                    self._handleKeyRelease(keyCode)
                    self._handleKeyPress(keyCode)
                elif state == '1':
                    self._handleKeyPress(keyCode)
                elif state == '0':
                    self._handleKeyRelease(keyCode)
                    
            if button:
                self.mediator.handle_mouse_click()


class XRecordInterface(XInterfaceBase):
        
    def __init__(self, mediator, testMode=False):
        XInterfaceBase.__init__(self, mediator, testMode)
        self.recordDisplay = display.Display()

        # Check for record extension 
        if not self.recordDisplay.has_extension("RECORD"):
            raise Exception("Your X-Server does not have the RECORD extension available/enabled.")                            
        
    def run(self):
        # Create a recording context; we only want key and mouse events
        self.ctx = self.recordDisplay.record_create_context(
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
        logger.info("XRecord interface thread starting")
        self.recordDisplay.record_enable_context(self.ctx, self.__processEvent)
        # Finally free the context
        self.recordDisplay.record_free_context(self.ctx)
        
    def cancel(self):
        self.localDisplay.record_disable_context(self.ctx)
        self.localDisplay.flush()
        #self.join()

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
            event, data = rq.EventField(None).parse_binary_value(data, self.recordDisplay.display, None, None)
            if event.type == X.KeyPress:
                self._handleKeyPress(event.detail)
            elif event.type == X.KeyRelease:
                self._handleKeyRelease(event.detail)
            elif event.type == X.ButtonPress:
                self.mediator.handle_mouse_click()

class AtSpiInterface(XInterfaceBase):
    
    def __init__(self, mediator, testMode=False):
        XInterfaceBase.__init__(self, mediator, testMode)
        self.registry = pyatspi.Registry        
        
    def start(self):
        logger.info("AT-SPI interface thread starting")
        self.registry.registerKeystrokeListener(self.__processKeyEvent, mask=pyatspi.allModifiers())
        self.registry.registerEventListener(self.__processWindowEvent, 'window:activate')
        self.registry.registerEventListener(self.__processMouseEvent, 'mouse:button')        
        
    def cancel(self):
        self.registry.deregisterKeystrokeListener(self.__processKeyEvent, mask=pyatspi.allModifiers())
        self.registry.deregisterEventListener(self.__processWindowEvent, 'window:activate')
        self.registry.deregisterEventListener(self.__processMouseEvent, 'mouse:button')
        self.registry.stop()
        
    def __processKeyEvent(self, event):
        if event.type == pyatspi.KEY_PRESSED_EVENT:
            self._handleKeyPress(event.hw_code)
        else:
            self._handleKeyRelease(event.hw_code)
            
    def __processMouseEvent(self, event):
        self.mediator.handle_mouse_click()
    
    def __processWindowEvent(self, event):
        #windowName = event.host_application.name.split('|')[1]
        self.activeWindow = event.host_application.name
    
    def _getWindowTitle(self):
        logger.debug("Window name: %s", self.activeWindow)
        return self.activeWindow
    
    def __pumpEvents(self):
        pyatspi.Registry.pumpQueuedEvents()
        return True
                
from iomediator import Key, MODIFIERS
from configmanager import *

KEY_MAP = {
           SHIFT : Key.SHIFT,
           SHIFT_R : Key.SHIFT,
           CAPSLOCK : Key.CAPSLOCK,
           CONTROL : Key.CONTROL,
           CONTROL_R : Key.CONTROL,
           ALT : Key.ALT,
           ALT_R : Key.ALT,
           ALT_GR : Key.ALT_GR,
           SUPER : Key.SUPER,
           SUPER_R : Key.SUPER,
           NUMLOCK : Key.NUMLOCK,
           SPACE : Key.SPACE,
           TAB : Key.TAB,
           LEFT : Key.LEFT,
           RIGHT : Key.RIGHT,
           UP : Key.UP,
           DOWN : Key.DOWN,
           RETURN : Key.RETURN,
           BACKSPACE : Key.BACKSPACE,
           SCROLL_LOCK : Key.SCROLL_LOCK,
           PRINT_SCREEN : Key.PRINT_SCREEN,
           PAUSE : Key.PAUSE,
           MENU : Key.MENU,
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
           
NUMPAD_MAP = {
           KP_INSERT : (Key.INSERT, "0"),
           KP_DELETE : (Key.DELETE, "."),
           KP_END : (Key.END, "1"),
           KP_DOWN : (Key.DOWN, "2"),
           KP_PAGE_DOWN : (Key.PAGE_DOWN, "3"),
           KP_LEFT : (Key.LEFT, "4"),
           KP_5 : ("<unknown>", "5"),
           KP_RIGHT : (Key.RIGHT, "6"),
           KP_HOME : (Key.HOME, "7"),
           KP_UP: (Key.UP, "8"),
           KP_PAGE_UP : (Key.PAGE_UP, "9"),
           KP_DIVIDE : ("/", "/"),
           KP_MULTIPLY : ("*", "*"),
           KP_ADD : ("+", "+"),
           KP_SUBTRACT : ("-", "-"),
           KP_ENTER : (Key.RETURN, Key.RETURN),
           }
    

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
