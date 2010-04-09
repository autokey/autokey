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
try:
    from Xlib.ext import record, xtest
    HAS_RECORD = True
except ImportError:
    HAS_RECORD = False
    
from Xlib.protocol import rq, event

import common
if common.USING_QT:
    from PyQt4.QtGui import QClipboard, QApplication
else:
    import gtk

logger = logging.getLogger("interface")

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

MASK_INDEXES = [
               (X.ShiftMapIndex, X.ShiftMask),
               (X.ControlMapIndex, X.ControlMask),
               (X.LockMapIndex, X.LockMask),
               (X.Mod1MapIndex, X.Mod1Mask),
               (X.Mod2MapIndex, X.Mod2Mask),
               (X.Mod3MapIndex, X.Mod3Mask),
               (X.Mod4MapIndex, X.Mod4Mask),
               (X.Mod5MapIndex, X.Mod5Mask),
               ]

class XInterfaceBase(threading.Thread):
    """
    Encapsulates the common functionality for the two X interface classes.
    """
    
    def __init__(self, mediator, app):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("XInterface-thread")
        self.mediator = mediator
        self.app = app
        self.localDisplay = display.Display()
        self.rootWindow = self.localDisplay.screen().root
        self.lock = threading.RLock()
        self.dpyLock = threading.RLock()
        self.lastChars = [] # TODO QT4 Workaround - remove me once the bug is fixed
        self.sendInProgress = False
        
        if common.USING_QT:
            self.clipBoard = QApplication.clipboard()
        else:
            self.clipBoard = gtk.Clipboard()
            self.selection = gtk.Clipboard(selection="PRIMARY")
        
        self.__initMappings()
        self.rootWindow.change_attributes(event_mask=X.SubstructureNotifyMask)
        
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

        # Build modifier mask mapping
        self.modMasks = {}
        mapping = self.localDisplay.get_modifier_mapping()
        for index, mask in MASK_INDEXES:
            
            for mod in MODIFIERS:
                if self.keyCodes[mod] in mapping[index]:
                    self.modMasks[mod] = mask

        self.__grabHotkeys()
       
        logger.debug("Keycodes dict: %s", self.keyCodes)
        logger.debug("Modifier masks: %r", self.modMasks)
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

    def __grabHotkeys(self):
        """
        Run during startup to grab global and specific hotkeys in all open windows
        """
        c = self.app.configManager
        hotkeys = c.hotKeys + c.hotKeyFolders

        # Grab global hotkeys in root window
        for item in c.globalHotkeys:
            if item.enabled:
                self.__grabHotkey(item.hotKey, item.modifiers, self.rootWindow)

        # Grab hotkeys without a filter in root window
        for item in hotkeys:
            if item.windowTitleRegex is None:
                self.__grabHotkey(item.hotKey, item.modifiers, self.rootWindow)

        self.__recurseTree(self.rootWindow, hotkeys)

    def __recurseTree(self, parent, hotkeys):
        # Grab matching hotkeys in all open child windows
        for window in parent.query_tree().children:
            title = self.get_window_title(window)
            if title != "" and title != "None":
                for item in hotkeys:
                    if item.windowTitleRegex is not None and item._should_trigger_window_title(title):
                        self.__grabHotkey(item.hotKey, item.modifiers, window)

            self.__recurseTree(window, hotkeys)


    def __grabHotkeysForWindow(self, window):
        """
        Grab all hotkeys relevant to the window

        Used when a new windows is mapped
        """
        c = self.app.configManager
        hotkeys = c.hotKeys + c.hotKeyFolders
        title = self.get_window_title(window)
        if title != "" and title != "None":
            for item in hotkeys:
                if item._should_trigger_window_title(title):
                    self.__grabHotkey(item.hotKey, item.modifiers, window)

    def __grabHotkey(self, key, modifiers, window):
        """
        Grab a specific hotkey in the given window
        """
        logger.debug("Grabbing hotkey: %r %r", modifiers, key)
        keycode = self.__lookupKeyCode(key)
        mask = 0
        for mod in modifiers:
            mask |= self.modMasks[mod]
                
        window.grab_key(keycode, mask, True, X.GrabModeAsync, X.GrabModeAsync)
        window.grab_key(keycode, mask|self.modMasks[Key.NUMLOCK], True, X.GrabModeAsync, X.GrabModeAsync)
        window.grab_key(keycode, mask|self.modMasks[Key.CAPSLOCK], True, X.GrabModeAsync, X.GrabModeAsync)
        window.grab_key(keycode, mask|self.modMasks[Key.CAPSLOCK]|self.modMasks[Key.NUMLOCK], True, X.GrabModeAsync, X.GrabModeAsync)

    def grab_hotkey(self, item):
        """
        Grab a hotkey.

        If the hotkey has no filter regex, it is global and need only be grabbed from the root window
        If it has a filter regex, iterate over all children of the root and grab from matching windows
        """
        if item.windowTitleRegex is None:
            self.__grabHotkey(item.hotKey, item.modifiers, self.rootWindow)
        else:
            self.__grabRecurse(item, self.rootWindow)

    def __grabRecurse(self, item, parent):
        for window in parent.query_tree().children:
            title = self.get_window_title(window)
            if title != "" and title != "None" and item._should_trigger_window_title(title):
                self.__grabHotkey(item.hotKey, item.modifiers, window)

            self.__grabRecurse(item, window)

    def ungrab_hotkey(self, item):
        """
        Ungrab a hotkey.

        If the hotkey has no filter regex, it is global and need only be ungrabbed from the root window
        If it has a filter regex, iterate over all children of the root and ungrab from matching windows
        """
        if item.windowTitleRegex is None:
            self.__ungrabHotkey(item.hotKey, item.modifiers, self.rootWindow)
        else:
            self.__ungrabRecurse(item, self.rootWindow)

    def __ungrabRecurse(self, item, parent):
        for window in parent.query_tree().children:
            title = self.get_window_title(window)
            if title != "" and title != "None" and item._should_trigger_window_title(title):
                self.__ungrabHotkey(item.hotKey, item.modifiers, window)

            self.__ungrabRecurse(item, window)

    def __ungrabHotkey(self, key, modifiers, window):
        """
        Ungrab a specific hotkey in the given window
        """
        logger.debug("Ungrabbing hotkey: %r %r", modifiers, key)
        keycode = self.__lookupKeyCode(key)
        mask = 0
        for mod in modifiers:
            mask |= self.modMasks[mod]

        window.ungrab_key(keycode, mask)
        window.ungrab_key(keycode, mask|self.modMasks[Key.NUMLOCK])
        window.ungrab_key(keycode, mask|self.modMasks[Key.CAPSLOCK])
        window.ungrab_key(keycode, mask|self.modMasks[Key.CAPSLOCK]|self.modMasks[Key.NUMLOCK])
        
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
                
    def send_string_clipboard(self, string):
        logger.debug("Sending string: %r", string)
        
        if common.USING_QT:
            self.sem = threading.Semaphore(0)
            self.app.exec_in_main(self.__fillSelection, string)
            self.sem.acquire()
        else:
            self.__fillSelection(string)
        
        focus = self.localDisplay.get_input_focus().focus
        xtest.fake_input(focus, X.ButtonPress, X.Button2)
        xtest.fake_input(focus, X.ButtonRelease, X.Button2)
        logger.debug("Send via clipboard done")
        
    def __fillSelection(self, string):
        if common.USING_QT:
            self.clipBoard.setText(string, QClipboard.Selection)
            self.sem.release()
        else:
            self.selection.set_text(string.encode("utf-8"))

    def begin_send(self):
        self.queuedEvents = []
        self.sendInProgress = True
        focus = self.localDisplay.get_input_focus().focus
        focus.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)
        self.localDisplay.flush()

    def finish_send(self):
        self.localDisplay.ungrab_keyboard(X.CurrentTime)
        self.sendInProgress = False
        for event in self.queuedEvents:
            if event.type == X.KeyPress:
                self.__sendKeyPressEvent(event.detail, event.state)
            elif event.type == X.KeyRelease:
                self.__sendKeyReleaseEvent(event.detail, event.state)
        self.localDisplay.flush()
    
    def send_string(self, string):
        """
        Send a string of printable characters.
        """
        logger.debug("Sending string: %r", string)
        for char in string:
            if self.keyCodes.has_key(char):
                self.send_key(char)
            else: 
                keyCodeList = self.localDisplay.keysym_to_keycodes(ord(char))
                if len(keyCodeList) > 0:
                    keyCode, offset = keyCodeList[0]
                    if offset == 0:
                        self.__sendKeyCode(keyCode)
                    if offset == 1:
                        self.__sendKeyCode(keyCode, self.modMasks[Key.SHIFT])
                    if offset == 4:
                        self.__sendKeyCode(keyCode, self.modMasks[Key.ALT_GR])
                else:
                    self.send_unicode_char(char)
                    
    def send_key(self, keyName):
        """
        Send a specific non-printing key, eg Up, Left, etc
        """
        logger.debug("Send special key: [%r]", keyName)
        self.__sendKeyCode(self.__lookupKeyCode(keyName))
        
    def send_modified_key(self, keyName, modifiers):
        """
        Send a modified key (e.g. when emulating a hotkey)
        """
        logger.debug("Send modified key: modifiers: %s key: %s", modifiers, keyName)
        """for modifier in modifiers:
            modifierCode = self.keyCodes[modifier.lower()]
            xtest.fake_input(self.rootWindow, X.KeyPress, modifierCode)
            
        keyCode = self.__lookupKeyCode(keyName)
        xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
        xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
        
        for modifier in modifiers:
            modifierCode = self.keyCodes[modifier.lower()]
            xtest.fake_input(self.rootWindow, X.KeyRelease, modifierCode)"""
        mask = 0
        for mod in modifiers:
            mask |= self.modMasks[mod]
        keyCode = self.__lookupKeyCode(keyName)
        self.__sendKeyCode(keyCode, mask)
            
    def send_unicode_char(self, char):
        logger.debug("Send unicode char: %s", char)
        self.send_modified_key('u', [Key.CONTROL, Key.SHIFT])
        
        keyDigits = "%04x" % ord(char)
        
        for digit in keyDigits:
            keyCode = self.__lookupKeyCode(digit)
            xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
            xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
            
        keyCode = self.__lookupKeyCode('<enter>')
        xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
        xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)
        
    def send_mouse_click(self, xCoord, yCoord, button, relative):
        # Get current pointer position so we can return it there
        pos = self.rootWindow.query_pointer()

        if relative:
            focus = self.localDisplay.get_input_focus().focus
            focus.warp_pointer(xCoord, yCoord)
            xtest.fake_input(focus, X.ButtonPress, button, x=xCoord, y=yCoord)
            xtest.fake_input(focus, X.ButtonRelease, button, x=xCoord, y=yCoord)
        else:
            self.rootWindow.warp_pointer(xCoord, yCoord)
            xtest.fake_input(self.rootWindow, X.ButtonPress, button, x=xCoord, y=yCoord)
            xtest.fake_input(self.rootWindow, X.ButtonRelease, button, x=xCoord, y=yCoord)
            
        self.rootWindow.warp_pointer(pos.root_x, pos.root_y)
            
        self.flush()
        
    def flush(self):
        self.localDisplay.flush()
        self.lastChars = []
        
    def press_key(self, keyName):
        self.__sendKeyPressEvent(self.__lookupKeyCode(keyName), 0)
        
    def release_key(self, keyName):
        self.__sendKeyReleaseEvent(self.__lookupKeyCode(keyName), 0)

    def __flushEvents(self):
        r, w, x = select.select([self.localDisplay], [], [], 0)
        if self.localDisplay in r:
            for x in range(self.localDisplay.pending_events()):
                event = self.localDisplay.next_event()
                if event.type == X.MappingNotify:
                    self.__updateMapping(event)
                elif event.type == X.MapNotify:
                    logger.debug("New window mapped, grabbing hotkeys")
                    try:
                        self.__grabHotkeysForWindow(event.window)
                    except:
                        logging.exception("Window destroyed during hotkey grab")

                elif event.type in (X.KeyPress, X.KeyRelease) and self.sendInProgress:
                    self.queuedEvents.append(event)
        
    def _handleKeyPress(self, keyCode):
        self.lock.acquire()

        self.__flushEvents()
        
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_down(modifier)
        else:
            self.mediator.handle_keypress(keyCode, self.get_window_title())
            
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
    
    def get_window_title(self, window=None):
        self.dpyLock.acquire()
        try:
            if window is None:
                windowvar = self.localDisplay.get_input_focus().focus
            else:
                windowvar = window
            wmname = windowvar.get_wm_name()
            wmclass = windowvar.get_wm_class()
            
            if (wmname == None) and (wmclass == None):
                #self.dpyLock.release()
                return self.get_window_title(windowvar.query_tree().parent)
            elif wmname == "":
                #self.dpyLock.release()
                return self.get_window_title(windowvar.query_tree().parent)

            return str(wmname)
        except:
            return ""
        finally:
            self.dpyLock.release()


class EvDevInterface(XInterfaceBase):
    
    def __init__(self, mediator, app):
        XInterfaceBase.__init__(self, mediator, app)
        self.cancelling = False
        self.__connect()
        
    def cancel(self):
        self.cancelling = True
        self.join(1.0)
        self.localDisplay.close()
        
    def run(self):
        logger.info("EvDev interface thread starting")
        while True:
            if self.cancelling:
                logger.info("EvDev interface thread terminated")
                break
            
            try:
                # Request next event
                try:
                    data = self.socket.recv(common.PACKET_SIZE)
                except socket.timeout:
                    continue # Timeout means no data to received
                    
                
                data = data.strip()
                keyCode, button, state = data.split(',')

                
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
                    ret = self.localDisplay.get_input_focus().focus.query_pointer()
                    self.mediator.handle_mouse_click(ret.root_x, ret.root_y, ret.win_x, ret.win_y, button)
                
            except:
                logger.exception("Connection to EvDev daemon lost")
                self.__connLost()
                continue
                
                
    def __connect(self):
        # Connect to event daemon
        self.connected = False
        logger.info("Attempting to establish connection to EvDev daemon")
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        try:
            self.socket.connect(common.DOMAIN_SOCKET_PATH)
            logger.info("EvDev daemon connected")
            self.connected = True
        except socket.error, e:
            raise Exception("Unable to connect to EvDev daemon:\n" + str(e))
        
    def __connLost(self):
        # Called when the connection is lost - try to re-establish
        # Loops every 10 seconds trying to establish a connection.
        self.socket.close()
        self.connected = False
        
        while not self.connected:
            try:
                self.__connect()
            except:
                pass # don't care if something went wrong - keep retrying
                
            if self.cancelling:
                break
                
            if not self.connected:
                time.sleep(10)


class XRecordInterface(XInterfaceBase):
        
    def __init__(self, mediator, app):
        XInterfaceBase.__init__(self, mediator, app)
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
        self.recordDisplay.close()
        
    def cancel(self):
        self.localDisplay.record_disable_context(self.ctx)
        self.localDisplay.flush()
        self.localDisplay.close()
        self.join(1.0)

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
                focus = self.localDisplay.get_input_focus().focus
                try:
                    rel = focus.translate_coords(self.rootWindow, event.root_x, event.root_y)
                    self.mediator.handle_mouse_click(event.root_x, event.root_y, rel.x, rel.y, event.detail)
                except:
                    self.mediator.handle_mouse_click(event.root_x, event.root_y, 0, 0, event.detail)


class AtSpiInterface(XInterfaceBase):
    
    def __init__(self, mediator, app):
        XInterfaceBase.__init__(self, mediator, app)
        self.registry = pyatspi.Registry
        self.activeWindow = ""    
        
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
        self.localDisplay.close()
        
    def __processKeyEvent(self, event):
        if event.type == pyatspi.KEY_PRESSED_EVENT:
            self._handleKeyPress(event.hw_code)
        else:
            self._handleKeyRelease(event.hw_code)
            
    def __processMouseEvent(self, event):
        if event.type[-1] == 'p':
            button = int(event.type[-2])
            
            focus = self.localDisplay.get_input_focus().focus
            try:
                rel = focus.translate_coords(self.rootWindow, event.detail1, event.detail2)
                relX = rel.x
                relY = rel.y
            except:
                relX = 0
                relY = 0
            
            self.mediator.handle_mouse_click(event.detail1, event.detail2, relX, relY, button)
    
    def __processWindowEvent(self, event):
        self.activeWindow = event.source_name
        self.mediator.handle_mouse_click(0, 0, 0, 0, 0)
    
    def get_window_title(self):
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
           #RETURN : Key.RETURN,
           RETURN : Key.ENTER,
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
           KP_ENTER : (Key.ENTER, Key.ENTER),
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
