# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ["XRecordInterface", "EvDevInterface", "AtSpiInterface"]


import os, threading, re, time, socket, select, logging, gtk, Queue

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

logger = logging.getLogger("interface")

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

CAPSLOCK_LEDMASK = 1<<0
NUMLOCK_LEDMASK = 1<<1

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
        self.lastChars = [] # QT4 Workaround
        self.__enableQT4Workaround = False # QT4 Workaround
        
        # Event loop
        self.eventThread = threading.Thread(target=self.__eventLoop)
        self.queue = Queue.Queue()
        
        # Event listener
        self.listenerThread = threading.Thread(target=self.__flushEvents)
        self.listenerThread.setDaemon(True)

        self.clipBoard = gtk.Clipboard()
        self.selection = gtk.Clipboard(selection="PRIMARY")

        self.__initMappings()

        # Set initial lock state
        ledMask = self.localDisplay.get_keyboard_control().led_mask
        mediator.set_modifier_state(Key.CAPSLOCK, (ledMask & CAPSLOCK_LEDMASK) != 0)
        mediator.set_modifier_state(Key.NUMLOCK, (ledMask & NUMLOCK_LEDMASK) != 0)

        # Window name atoms
        self.__NameAtom = self.localDisplay.intern_atom("_NET_WM_NAME", True)
        self.__VisibleNameAtom = self.localDisplay.intern_atom("_NET_WM_VISIBLE_NAME", True)
        
        self.keyMap = gtk.gdk.keymap_get_default()
        self.keyMap.connect("keys-changed", self.on_keys_changed)
        self.__ignoreRemap = False
        
        self.eventThread.start()
        self.listenerThread.start()
        
    def __eventLoop(self):
        while True:
            method, args = self.queue.get()
            
            if method is None and args is None:
                break
    
            method(*args)
            self.queue.task_done()
    
    def __enqueue(self, method, *args):
        self.queue.put_nowait((method, args))

    def on_keys_changed(self, data=None):
        if not self.__ignoreRemap:
            logger.debug("Recorded keymap change event")
            self.__ignoreRemap = True
            time.sleep(0.2)
            self.__enqueue(self.__ungrabAllHotkeys)
            self.__enqueue(self.__delayedInitMappings)
        else:
            logger.debug("Ignored keymap change event")

    def __delayedInitMappings(self):        
        self.__initMappings()
        self.__ignoreRemap = False

    def __initMappings(self):
        self.localDisplay = display.Display()
        self.rootWindow = self.localDisplay.screen().root
        self.rootWindow.change_attributes(event_mask=X.SubstructureNotifyMask)
        
        altList = self.localDisplay.keysym_to_keycodes(XK.XK_ISO_Level3_Shift)
        self.__usableOffsets = (0, 1)
        for code, offset in altList:
            if code == 108 and offset == 0:
                self.__usableOffsets += (4, 5)
                logger.debug("Enabling sending using Alt-Grid")
                break

        # Build modifier mask mapping
        self.modMasks = {}
        mapping = self.localDisplay.get_modifier_mapping()

        for keySym, ak in XK_TO_AK_MAP.iteritems():
            if ak in MODIFIERS:
                keyCodeList = self.localDisplay.keysym_to_keycodes(keySym)
                found = False

                for keyCode, lvl in keyCodeList:
                    for index, mask in MASK_INDEXES:
                        if keyCode in mapping[index]:
                            self.modMasks[ak] = mask
                            found = True
                            break

                    if found: break

        logger.debug("Modifier masks: %r", self.modMasks)

        self.__grabHotkeys()
        self.localDisplay.flush()

        # --- get list of keycodes that are unused in the current keyboard mapping

        keyCode = 8
        avail = []
        for keyCodeMapping in self.localDisplay.get_keyboard_mapping(keyCode, 200):
            codeAvail = True
            for offset in keyCodeMapping:
                if offset != 0:
                    codeAvail = False
                    break

            if codeAvail:
                avail.append(keyCode)

            keyCode += 1

        self.__availableKeycodes = avail
        self.remappedChars = {}

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            self.keymap_test()

    def keymap_test(self):
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
                self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, self.rootWindow)

        # Grab hotkeys without a filter in root window
        for item in hotkeys:
            if item.windowInfoRegex is None:
                self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, self.rootWindow)

        self.__enqueue(self.__recurseTree, self.rootWindow, hotkeys)

    def __recurseTree(self, parent, hotkeys):
        # Grab matching hotkeys in all open child windows
        for window in parent.query_tree().children:
            try:
                title = self.get_window_title(window)
                klass = self.get_window_class(window)
                for item in hotkeys:
                    if item.windowInfoRegex is not None and item._should_trigger_window_title((title, klass)):
                        self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, window)

                
                self.__recurseTree(window, hotkeys)
            except:
                logger.exception("grab on window failed")
                
    def __ungrabAllHotkeys(self):
        """
        Ungrab all hotkeys in preparation for keymap change
        """
        c = self.app.configManager
        hotkeys = c.hotKeys + c.hotKeyFolders

        # Ungrab global hotkeys in root window
        for item in c.globalHotkeys:
            if item.enabled:
                self.__ungrabHotkey(item.hotKey, item.modifiers, self.rootWindow)
        
        # Ungrab hotkeys without a filter in root window
        for item in hotkeys:
            if item.windowInfoRegex is None:
                self.__ungrabHotkey(item.hotKey, item.modifiers, self.rootWindow)
                
        self.__recurseTreeUngrab(self.rootWindow, hotkeys)
                
    def __recurseTreeUngrab(self, parent, hotkeys):
        # Ungrab matching hotkeys in all open child windows
        for window in parent.query_tree().children:
            try:
                title = self.get_window_title(window)
                klass = self.get_window_class(window)
                for item in hotkeys:
                    if item.windowInfoRegex is not None and item._should_trigger_window_title((title, klass)):
                        self.__ungrabHotkey(item.hotKey, item.modifiers, window)

                
                self.__recurseTreeUngrab(window, hotkeys)
            except:
                logger.exception("ungrab on window failed")

    def __grabHotkeysForWindow(self, window):
        """
        Grab all hotkeys relevant to the window

        Used when a new window is created
        """
        c = self.app.configManager
        hotkeys = c.hotKeys + c.hotKeyFolders
        title = self.get_window_title(window)
        klass = self.get_window_class(window)
        for item in hotkeys:
            if item.windowInfoRegex is not None and item._should_trigger_window_title((title, klass)):
                self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, window)

    def __grabHotkey(self, key, modifiers, window):
        """
        Grab a specific hotkey in the given window
        """
        logger.debug("Grabbing hotkey: %r %r", modifiers, key)
        try:
            keycode = self.__lookupKeyCode(key)
            mask = 0
            for mod in modifiers:
                mask |= self.modMasks[mod]

            window.grab_key(keycode, mask, True, X.GrabModeAsync, X.GrabModeAsync)

            if Key.NUMLOCK in self.modMasks:
                window.grab_key(keycode, mask|self.modMasks[Key.NUMLOCK], True, X.GrabModeAsync, X.GrabModeAsync)

            if Key.CAPSLOCK in self.modMasks:
                window.grab_key(keycode, mask|self.modMasks[Key.CAPSLOCK], True, X.GrabModeAsync, X.GrabModeAsync)

            if Key.CAPSLOCK in self.modMasks and Key.NUMLOCK in self.modMasks:
                window.grab_key(keycode, mask|self.modMasks[Key.CAPSLOCK]|self.modMasks[Key.NUMLOCK], True, X.GrabModeAsync, X.GrabModeAsync)

        except Exception, e:
            logger.warn("Failed to grab hotkey %r %r: %s", modifiers, key, str(e))

    def grab_hotkey(self, item):
        """
        Grab a hotkey.

        If the hotkey has no filter regex, it is global and need only be grabbed from the root window
        If it has a filter regex, iterate over all children of the root and grab from matching windows
        """
        if item.windowInfoRegex is None:
            self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, self.rootWindow)
        else:
            self.__enqueue(self.__grabRecurse, item, self.rootWindow)
        

    def __grabRecurse(self, item, parent):
        for window in parent.query_tree().children:
            title = self.get_window_title(window)
            klass = self.get_window_class(window)
            if item._should_trigger_window_title((title, klass)):
                self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, window)
                break

            self.__grabRecurse(item, window)

    def ungrab_hotkey(self, item):
        """
        Ungrab a hotkey.

        If the hotkey has no filter regex, it is global and need only be ungrabbed from the root window
        If it has a filter regex, iterate over all children of the root and ungrab from matching windows
        """
        if item.windowInfoRegex is None:
            self.__enqueue(self.__ungrabHotkey, item.hotKey, item.modifiers, self.rootWindow)
        else:
            self.__enqueue(self.__ungrabRecurse, item, self.rootWindow)

    def __ungrabRecurse(self, item, parent):
        for window in parent.query_tree().children:
            title = self.get_window_title(window)
            klass = self.get_window_class(window)
            if item._should_trigger_window_title((title, klass)):
                self.__enqueue(self.__ungrabHotkey, item.hotKey, item.modifiers, window)
                break

            self.__ungrabRecurse(item, window)

    def __ungrabHotkey(self, key, modifiers, window):
        """
        Ungrab a specific hotkey in the given window
        """
        logger.debug("Ungrabbing hotkey: %r %r", modifiers, key)
        try:
            keycode = self.__lookupKeyCode(key)
            mask = 0
            for mod in modifiers:
                mask |= self.modMasks[mod]

            window.ungrab_key(keycode, mask)

            if Key.NUMLOCK in self.modMasks:
                window.ungrab_key(keycode, mask|self.modMasks[Key.NUMLOCK])

            if Key.CAPSLOCK in self.modMasks:
                window.ungrab_key(keycode, mask|self.modMasks[Key.CAPSLOCK])

            if Key.CAPSLOCK in self.modMasks and Key.NUMLOCK in self.modMasks:
                window.ungrab_key(keycode, mask|self.modMasks[Key.CAPSLOCK]|self.modMasks[Key.NUMLOCK])
        except Exception, e:
            logger.warn("Failed to ungrab hotkey %r %r: %s", modifiers, key, str(e))

    def lookup_string(self, keyCode, shifted, numlock, altGrid):
        if keyCode == 0:
            return "<unknown>"

        keySym = self.localDisplay.keycode_to_keysym(keyCode, 0)

        if keySym in XK_TO_AK_NUMLOCKED and numlock and not (numlock and shifted):
            return XK_TO_AK_NUMLOCKED[keySym]

        elif keySym in XK_TO_AK_MAP:
            return XK_TO_AK_MAP[keySym]
        else:
            try:
                index = 0
                if shifted: index += 1
                if altGrid: index += 4
                return unichr(self.localDisplay.keycode_to_keysym(keyCode, index))
            except ValueError:
                return "<code%d>" % keyCode

    def send_string_clipboard(self, string, pasteCommand):
        self.__enqueue(self.__sendStringClipboard, string, pasteCommand)
        
    def __sendStringClipboard(self, string, pasteCommand):
        logger.debug("Sending string: %r", string)

        if pasteCommand is None:
            self.__fillSelection(string)

            focus = self.localDisplay.get_input_focus().focus
            xtest.fake_input(focus, X.ButtonPress, X.Button2)
            xtest.fake_input(focus, X.ButtonRelease, X.Button2)

        else:
            self.__fillClipboard(string)
            self.mediator.send_string(pasteCommand)

        logger.debug("Send via clipboard done")

    def __fillSelection(self, string):
        gtk.gdk.threads_enter()
        self.selection.set_text(string.encode("utf-8"))
        gtk.gdk.threads_leave()

    def __fillClipboard(self, string):
        gtk.gdk.threads_enter()
        self.clipBoard.set_text(string.encode("utf-8"))
        gtk.gdk.threads_leave()

    def begin_send(self):
        self.__enqueue(self.__grab_keyboard)

    def finish_send(self):
        self.__enqueue(self.__ungrabKeyboard)

    def grab_keyboard(self):
        self.__enqueue(self.__grab_keyboard)

    def __grab_keyboard(self):
        self.rootWindow.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)
        self.localDisplay.flush()

    def ungrab_keyboard(self):
        self.__enqueue(self.__ungrabKeyboard)
        
    def __ungrabKeyboard(self):
        self.localDisplay.ungrab_keyboard(X.CurrentTime)
        self.localDisplay.flush()

    def __findUsableKeycode(self, codeList):
        for code, offset in codeList:
            if offset in self.__usableOffsets:
                return code, offset

        return None, None

    def send_string(self, string):
        self.__enqueue(self.__sendString, string)
        
    def __sendString(self, string):
        """
        Send a string of printable characters.
        """
        logger.debug("Sending string: %r", string)
        # Determine if workaround is needed
        if not ConfigManager.SETTINGS[ENABLE_QT4_WORKAROUND]:
            self.__checkWorkaroundNeeded()

        # First find out if any chars need remapping
        remapNeeded = False
        for char in string:
            keyCodeList = self.localDisplay.keysym_to_keycodes(ord(char))
            usableCode, offset = self.__findUsableKeycode(keyCodeList)
            if usableCode is None and char not in self.remappedChars:
                remapNeeded = True
                break

        # Now we know chars need remapping, do it
        if remapNeeded:
            self.__ignoreRemap = True
            self.remappedChars = {}
            remapChars = []

            for char in string:
                keyCodeList = self.localDisplay.keysym_to_keycodes(ord(char))
                usableCode, offset = self.__findUsableKeycode(keyCodeList)
                if usableCode is None:
                    remapChars.append(char)

            logger.debug("Characters requiring remapping: %r", remapChars)
            availCodes = self.__availableKeycodes
            logger.debug("Remapping with keycodes in the range: %r", availCodes)
            mapping = self.localDisplay.get_keyboard_mapping(8, 200)
            firstCode = 8

            for i in xrange(len(availCodes) - 1):
                code = availCodes[i]
                sym1 = 0
                sym2 = 0

                if len(remapChars) > 0:
                    char = remapChars.pop(0)
                    self.remappedChars[char] = (code, 0)
                    sym1 = ord(char)
                if len(remapChars) > 0:
                    char = remapChars.pop(0)
                    self.remappedChars[char] = (code, 1)
                    sym2 = ord(char)

                if sym1 != 0:
                    mapping[code - firstCode][0] = sym1
                    mapping[code - firstCode][1] = sym2

            mapping = [tuple(l) for l in mapping]
            self.localDisplay.change_keyboard_mapping(firstCode, mapping)
            self.localDisplay.flush()

        focus = self.localDisplay.get_input_focus().focus

        for char in string:
            try:
                keyCodeList = self.localDisplay.keysym_to_keycodes(ord(char))
                keyCode, offset = self.__findUsableKeycode(keyCodeList)
                if keyCode is not None:
                    if offset == 0:
                        self.__sendKeyCode(keyCode, theWindow=focus)
                    if offset == 1:
                        self.__pressKey(Key.SHIFT)
                        self.__sendKeyCode(keyCode, self.modMasks[Key.SHIFT], focus)
                        self.__releaseKey(Key.SHIFT)
                    if offset == 4:
                        self.__pressKey(Key.ALT_GR)
                        self.__sendKeyCode(keyCode, self.modMasks[Key.ALT_GR], focus)
                        self.__releaseKey(Key.ALT_GR)
                    if offset == 5:
                        self.__pressKey(Key.ALT_GR)
                        self.__pressKey(Key.SHIFT)
                        self.__sendKeyCode(keyCode, self.modMasks[Key.ALT_GR]|self.modMasks[Key.SHIFT], focus)
                        self.__releaseKey(Key.SHIFT)
                        self.__releaseKey(Key.ALT_GR)

                elif char in self.remappedChars:
                    keyCode, offset = self.remappedChars[char]
                    if offset == 0:
                        self.__sendKeyCode(keyCode, theWindow=focus)
                    if offset == 1:
                        self.__pressKey(Key.SHIFT)
                        self.__sendKeyCode(keyCode, self.modMasks[Key.SHIFT], focus)
                        self.__releaseKey(Key.SHIFT)
                else:
                    logger.warn("Unable to send character %r", char)
            except Exception, e:
                logger.exception("Error sending char %r: %s", char, str(e))

        self.__ignoreRemap = False


    def send_key(self, keyName):
        """
        Send a specific non-printing key, eg Up, Left, etc
        """
        self.__enqueue(self.__sendKey, keyName)
        
    def __sendKey(self, keyName):
        logger.debug("Send special key: [%r]", keyName)
        self.__sendKeyCode(self.__lookupKeyCode(keyName))

    def fake_keypress(self, keyName):
         self.__enqueue(self.__fakeKeypress, keyName)
         
    def __fakeKeypress(self, keyName):        
        keyCode = self.__lookupKeyCode(keyName)
        xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)
        xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)

    def fake_keydown(self, keyName):
        self.__enqueue(self.__fakeKeydown, keyName)
        
    def __fakeKeydown(self, keyName):
        keyCode = self.__lookupKeyCode(keyName)
        xtest.fake_input(self.rootWindow, X.KeyPress, keyCode)

    def fake_keyup(self, keyName):
        self.__enqueue(self.__fakeKeyup, keyName)
        
    def __fakeKeyup(self, keyName):
        keyCode = self.__lookupKeyCode(keyName)
        xtest.fake_input(self.rootWindow, X.KeyRelease, keyCode)

    def send_modified_key(self, keyName, modifiers):
        """
        Send a modified key (e.g. when emulating a hotkey)
        """
        self.__enqueue(self.__sendModifiedKey, keyName, modifiers)
        
    def __sendModifiedKey(self, keyName, modifiers):
        logger.debug("Send modified key: modifiers: %s key: %s", modifiers, keyName)
        try:
            mask = 0
            for mod in modifiers:
                mask |= self.modMasks[mod]
            keyCode = self.__lookupKeyCode(keyName)
            for mod in modifiers: self.__pressKey(mod)
            self.__sendKeyCode(keyCode, mask)
            for mod in modifiers: self.__releaseKey(mod)
        except Exception, e:
            logger.warn("Error sending modified key %r %r: %s", modifiers, keyName, str(e))

    def send_mouse_click(self, xCoord, yCoord, button, relative):
        self.__enqueue(self.__sendMouseClick, xCoord, yCoord, button, relative)
        
    def __sendMouseClick(self, xCoord, yCoord, button, relative):    
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

        self.__flush()

    def send_mouse_click_relative(self, xoff, yoff, button):
        self.__enqueue(self.__sendMouseClickRelative, xoff, yoff, button)
        
    def __sendMouseClickRelative(self, xoff, yoff, button):
        # Get current pointer position
        pos = self.rootWindow.query_pointer()

        xCoord = pos.root_x + xoff
        yCoord = pos.root_y + yoff

        self.rootWindow.warp_pointer(xCoord, yCoord)
        xtest.fake_input(self.rootWindow, X.ButtonPress, button, x=xCoord, y=yCoord)
        xtest.fake_input(self.rootWindow, X.ButtonRelease, button, x=xCoord, y=yCoord)

        self.rootWindow.warp_pointer(pos.root_x, pos.root_y)

        self.__flush()

    def flush(self):
        self.__enqueue(self.__flush)
        
    def __flush(self):
        self.localDisplay.flush()
        self.lastChars = []

    def press_key(self, keyName):
        self.__enqueue(self.__pressKey, keyName)
        
    def __pressKey(self, keyName):
        self.__sendKeyPressEvent(self.__lookupKeyCode(keyName), 0)

    def release_key(self, keyName):
        self.__enqueue(self.__releaseKey, keyName)
        
    def __releaseKey(self, keyName):
        self.__sendKeyReleaseEvent(self.__lookupKeyCode(keyName), 0)

    def __flushEvents(self):
        while True:
            try:
                readable, w, e = select.select([self.localDisplay], [], [], 1)
                time.sleep(0.2)
                if self.localDisplay in readable:
                    for x in xrange(self.localDisplay.pending_events()):
                        event = self.localDisplay.next_event()
                        if event.type == X.CreateNotify:
                            self.__enqueue(self.__grabHotkeysForWindow, event.window)
            except:
                pass

    def handle_keypress(self, keyCode):
        self.__enqueue(self.__handleKeyPress, keyCode)
    
    def __handleKeyPress(self, keyCode):
        focus = self.localDisplay.get_input_focus().focus

        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_down(modifier)
        else:
            self.mediator.handle_keypress(keyCode, self.get_window_title(focus), self.get_window_class(focus))

    def handle_keyrelease(self, keyCode):
        self.__enqueue(self.__handleKeyrelease, keyCode)
    
    def __handleKeyrelease(self, keyCode):
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_up(modifier)
            
    def handle_mouseclick(self, button, x, y):
        self.__enqueue(self.__handleMouseclick, button, x, y)
        
    def __handleMouseclick(self, button, x, y):        
        title = self.get_window_title()
        klass = self.get_window_class()
        info = (title, klass)
        
        if x is None and y is None:
            ret = self.localDisplay.get_input_focus().focus.query_pointer()
            self.mediator.handle_mouse_click(ret.root_x, ret.root_y, ret.win_x, ret.win_y, button, info)
        else:
            focus = self.localDisplay.get_input_focus().focus
            try:
                rel = focus.translate_coords(self.rootWindow, x, y)
                self.mediator.handle_mouse_click(x, y, rel.x, rel.y, button, info)
            except:
                self.mediator.handle_mouse_click(x, y, 0, 0, button, info)

    def __decodeModifier(self, keyCode):
        """
        Checks if the given keyCode is a modifier key. If it is, returns the modifier name
        constant as defined in the iomediator module. If not, returns C{None}
        """
        keyName = self.lookup_string(keyCode, False, False, False)
        if keyName in MODIFIERS:
            return keyName

        return None

    def __sendKeyCode(self, keyCode, modifiers=0, theWindow=None):
        if ConfigManager.SETTINGS[ENABLE_QT4_WORKAROUND] or self.__enableQT4Workaround:
            self.__doQT4Workaround(keyCode)
        self.__sendKeyPressEvent(keyCode, modifiers, theWindow)
        self.__sendKeyReleaseEvent(keyCode, modifiers, theWindow)

    def __checkWorkaroundNeeded(self):
        focus = self.localDisplay.get_input_focus().focus
        windowName = self.get_window_title(focus)
        windowClass = self.get_window_class(focus)
        w = self.app.configManager.workAroundApps

        if w.match(windowName) or w.match(windowClass):
            self.__enableQT4Workaround = True
        else:
            self.__enableQT4Workaround = False

    def __doQT4Workaround(self, keyCode):
        if len(self.lastChars) > 0:
            if keyCode in self.lastChars and not self.lastChars[-1] == keyCode:
                self.localDisplay.flush()
                time.sleep(0.0125)

        self.lastChars.append(keyCode)

        if len(self.lastChars) > 10:
            self.lastChars.pop(0)

    def __sendKeyPressEvent(self, keyCode, modifiers, theWindow=None):
        if theWindow is None:
            focus = self.localDisplay.get_input_focus().focus
        else:
            focus = theWindow
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

    def __sendKeyReleaseEvent(self, keyCode, modifiers, theWindow=None):
        if theWindow is None:
            focus = self.localDisplay.get_input_focus().focus
        else:
            focus = theWindow
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
        if char in AK_TO_XK_MAP:
            return self.localDisplay.keysym_to_keycode(AK_TO_XK_MAP[char])
        elif char.startswith("<code"):
            return int(char[5:-1])
        else:
            try:
                return self.localDisplay.keysym_to_keycode(ord(char))
            except Exception, e:
                logger.error("Unknown key name: %s", char)
                raise

    def get_window_title(self, window=None):
        try:
            if window is None:
                windowvar = self.localDisplay.get_input_focus().focus
            else:
                windowvar = window

            atom = windowvar.get_property(self.__VisibleNameAtom, 0, 0, 255)
            atom = atom or windowvar.get_property(self.__NameAtom, 0, 0, 255)

            if atom:
                return atom.value
            else:
                return self.__getWinTitle(windowvar)

        except:
            return ""


    def __getWinTitle(self, windowvar):
        wmname = windowvar.get_wm_name()
        wmclass = windowvar.get_wm_class()

        if (wmname == None) and (wmclass == None):
            return self.__getWinTitle(windowvar.query_tree().parent)
        elif wmname == "" and wmclass == "":
            return self.__getWinTitle(windowvar.query_tree().parent)

        return str(wmname)

    def get_window_class(self, window=None):
        try:
            if window is None:
                windowvar = self.localDisplay.get_input_focus().focus
            else:
                windowvar = window

            return self.__getWinClass(windowvar)
        except:
            return ""
    
    def __getWinClass(self, windowvar):
        wmclass = windowvar.get_wm_class()

        if wmclass == None or wmclass == "":
            return self.__getWinClass(windowvar.query_tree().parent)

        return wmclass[0] + '.' + wmclass[1]
    
    def cancel(self):
        self.queue.put_nowait((None, None))
        self.localDisplay.flush()
        self.localDisplay.close()
        self.eventThread.join()
        self.join(1.0)


class EvDevInterface(XInterfaceBase):

    def initialise(self):
        self.cancelling = False
        self.connected = False
        retryCount = 0

        while not self.connected:
            try:
                self.__connect()
            except:
                if retryCount >= 6:
                    raise

            if self.cancelling:
                break

            if not self.connected:
                retryCount += 1
                time.sleep(10)


    def cancel(self):
        self.cancelling = True
        XInterfaceBase.cancel(self)

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
                        self.handle_keyrelease(keyCode)
                        self.handle_keypress(keyCode)
                    elif state == '1':
                        self.handle_keypress(keyCode)
                    elif state == '0':
                        self.handle_keyrelease(keyCode)

                if button:
                    self.handle_mouseclick(button, None, None)

            except:
                logger.exception("Connection to EvDev daemon lost")
                self.__connLost()
                continue


    def __connect(self):
        # Connect to event daemon
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

    def initialise(self):
        self.recordDisplay = display.Display()
        self.__locksChecked = False

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
        XInterfaceBase.cancel(self)

    def __processEvent(self, reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            return
        if not len(reply.data) or ord(reply.data[0]) < 2:
            # not an event
            return

        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, self.recordDisplay.display, None, None)
            if event.type == X.KeyPress:
                self.handle_keypress(event.detail)
            elif event.type == X.KeyRelease:
                self.handle_keyrelease(event.detail)
            elif event.type == X.ButtonPress:
                self.handle_mouseclick(event.detail, event.root_x, event.root_y)


class AtSpiInterface(XInterfaceBase):

    def initialise(self):
        self.registry = pyatspi.Registry

    def start(self):
        logger.info("AT-SPI interface thread starting")
        self.registry.registerKeystrokeListener(self.__processKeyEvent, mask=pyatspi.allModifiers())
        self.registry.registerEventListener(self.__processMouseEvent, 'mouse:button')

    def cancel(self):
        self.registry.deregisterKeystrokeListener(self.__processKeyEvent, mask=pyatspi.allModifiers())
        self.registry.deregisterEventListener(self.__processMouseEvent, 'mouse:button')
        self.registry.stop()
        XInterfaceBase.cancel(self)

    def __processKeyEvent(self, event):
        if event.type == pyatspi.KEY_PRESSED_EVENT:
            self.handle_keypress(event.hw_code)
        else:
            self.handle_keyrelease(event.hw_code)

    def __processMouseEvent(self, event):
        if event.type[-1] == 'p':
            button = int(event.type[-2])            
            self.handle_mouseclick(button, event.detail1, event.detail2)

    def __pumpEvents(self):
        pyatspi.Registry.pumpQueuedEvents()
        return True

from iomediator import Key, MODIFIERS
from configmanager import *

XK.load_keysym_group('xkb')

XK_TO_AK_MAP = {
           XK.XK_Shift_L : Key.SHIFT,
           XK.XK_Shift_R : Key.SHIFT,
           XK.XK_Caps_Lock : Key.CAPSLOCK,
           XK.XK_Control_L : Key.CONTROL,
           XK.XK_Control_R : Key.CONTROL,
           XK.XK_Alt_L : Key.ALT,
           XK.XK_Alt_R : Key.ALT,
           XK.XK_ISO_Level3_Shift : Key.ALT_GR,
           XK.XK_Super_L : Key.SUPER,
           XK.XK_Super_R : Key.SUPER,
           XK.XK_Num_Lock : Key.NUMLOCK,
           #SPACE : Key.SPACE,
           XK.XK_Tab : Key.TAB,
           XK.XK_Left : Key.LEFT,
           XK.XK_Right : Key.RIGHT,
           XK.XK_Up : Key.UP,
           XK.XK_Down : Key.DOWN,
           XK.XK_Return : Key.ENTER,
           XK.XK_BackSpace : Key.BACKSPACE,
           XK.XK_Scroll_Lock : Key.SCROLL_LOCK,
           XK.XK_Print : Key.PRINT_SCREEN,
           XK.XK_Pause : Key.PAUSE,
           XK.XK_Menu : Key.MENU,
           XK.XK_F1 : Key.F1,
           XK.XK_F2 : Key.F2,
           XK.XK_F3 : Key.F3,
           XK.XK_F4 : Key.F4,
           XK.XK_F5 : Key.F5,
           XK.XK_F6 : Key.F6,
           XK.XK_F7 : Key.F7,
           XK.XK_F8 : Key.F8,
           XK.XK_F9 : Key.F9,
           XK.XK_F10 : Key.F10,
           XK.XK_F11 : Key.F11,
           XK.XK_F12 : Key.F12,
           XK.XK_Escape : Key.ESCAPE,
           XK.XK_Insert : Key.INSERT,
           XK.XK_Delete : Key.DELETE,
           XK.XK_Home : Key.HOME,
           XK.XK_End : Key.END,
           XK.XK_Page_Up : Key.PAGE_UP,
           XK.XK_Page_Down : Key.PAGE_DOWN,
           XK.XK_KP_Insert : Key.NP_INSERT,
           XK.XK_KP_Delete : Key.NP_DELETE,
           XK.XK_KP_End : Key.NP_END,
           XK.XK_KP_Down : Key.NP_DOWN,
           XK.XK_KP_Page_Down : Key.NP_PAGE_DOWN,
           XK.XK_KP_Left : Key.NP_LEFT,
           XK.XK_KP_Begin : Key.NP_5,
           XK.XK_KP_Right : Key.NP_RIGHT,
           XK.XK_KP_Home : Key.NP_HOME,
           XK.XK_KP_Up: Key.NP_UP,
           XK.XK_KP_Page_Up : Key.NP_PAGE_UP,
           XK.XK_KP_Divide : Key.NP_DIVIDE,
           XK.XK_KP_Multiply : Key.NP_MULTIPLY,
           XK.XK_KP_Add : Key.NP_ADD,
           XK.XK_KP_Subtract : Key.NP_SUBTRACT,
           XK.XK_KP_Enter : Key.ENTER,
           XK.XK_space : ' '
           }

AK_TO_XK_MAP = dict((v,k) for k, v in XK_TO_AK_MAP.iteritems())

XK_TO_AK_NUMLOCKED = {
           XK.XK_KP_Insert : "0",
           XK.XK_KP_Delete : ".",
           XK.XK_KP_End : "1",
           XK.XK_KP_Down : "2",
           XK.XK_KP_Page_Down : "3",
           XK.XK_KP_Left : "4",
           XK.XK_KP_Begin : "5",
           XK.XK_KP_Right : "6",
           XK.XK_KP_Home : "7",
           XK.XK_KP_Up: "8",
           XK.XK_KP_Page_Up : "9",
           XK.XK_KP_Divide : "/",
           XK.XK_KP_Multiply : "*",
           XK.XK_KP_Add : "+",
           XK.XK_KP_Subtract : "-",
           XK.XK_KP_Enter : Key.ENTER
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
