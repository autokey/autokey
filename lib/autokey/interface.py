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

__all__ = ["XRecordInterface", "AtSpiInterface", "WindowInfo"]

from abc import abstractmethod
import logging
import typing
import threading
import select
import queue
import subprocess
import time

import autokey.model.phrase

if typing.TYPE_CHECKING:
    from autokey.iomediator.iomediator import IoMediator
import autokey.configmanager.configmanager_constants as cm_constants


# Imported to enable threading in Xlib. See module description. Not an unused import statement.
import Xlib.threaded as xlib_threaded

# Delete again, as the reference is not needed anymore after the import side-effect has done it’s work.
# This (hopefully) also prevents automatic code cleanup software from deleting an "unused" import and re-introduce
# issues.
del xlib_threaded

from Xlib.error import ConnectionClosedError


from . import common
from autokey.model.button import Button

if common.USING_QT:
    from PyQt5.QtGui import QClipboard
    from PyQt5.QtWidgets import QApplication
else:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk

    try:
        gi.require_version('Atspi', '2.0')
        import pyatspi
        HAS_ATSPI = True
    except ImportError:
        HAS_ATSPI = False
    except ValueError:
        HAS_ATSPI = False
    except SyntaxError:  # pyatspi 2.26 fails when used with Python 3.7
        HAS_ATSPI = False

from Xlib import X, XK, display, error
try:
    from Xlib.ext import record, xtest
    HAS_RECORD = True
except ImportError:
    HAS_RECORD = False
    
from Xlib.protocol import rq, event


logger = __import__("autokey.logger").logger.get_logger(__name__)
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


def str_or_bytes_to_bytes(x: typing.Union[str, bytes, memoryview]) -> bytes:
    if type(x) == bytes:
        # logger.info("using LiuLang's python3-xlib")
        return x
    if type(x) == str:
        logger.debug("using official python-xlib")
        return x.encode("utf8")
    if type(x) == memoryview:
        logger.debug("using official python-xlib")
        return x.tobytes()
    raise RuntimeError("x must be str or bytes or memoryview object, type(x)={}, repr(x)={}".format(type(x), repr(x)))


# This tuple is used to return requested window properties.
WindowInfo = typing.NamedTuple("WindowInfo", [("wm_title", str), ("wm_class", str)])


class AbstractClipboard:
    """
    Abstract interface for clipboard interactions.
    This is an abstraction layer for platform dependent clipboard handling.
    It unifies clipboard handling for Qt and GTK.
    """
    @property
    @abstractmethod
    def text(self):
        """Get and set the keyboard clipboard content."""
        return

    @property
    @abstractmethod
    def selection(self):
        """Get and set the mouse selection clipboard content."""
        return


if common.USING_QT:
    class Clipboard(AbstractClipboard):
        def __init__(self):
            self._clipboard = QApplication.clipboard()

        @property
        def text(self):
            return self._clipboard.text(QClipboard.Clipboard)

        @text.setter
        def text(self, new_content: str):
            self._clipboard.setText(new_content, QClipboard.Clipboard)

        @property
        def selection(self):
            return self._clipboard.text(QClipboard.Selection)

        @selection.setter
        def selection(self, new_content: str):
            self._clipboard.setText(new_content, QClipboard.Selection)

else:
    class Clipboard(AbstractClipboard):
        def __init__(self):
            self._clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            self._selection = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)

        @property
        def text(self):
            Gdk.threads_enter()
            text = self._clipboard.wait_for_text()
            Gdk.threads_leave()
            return text

        @text.setter
        def text(self, new_content: str):
            Gdk.threads_enter()
            try:
                # This call might fail and raise an Exception.
                # If it does, make sure to release the mutex and not deadlock AutoKey.
                self._clipboard.set_text(new_content, -1)
            finally:
                Gdk.threads_leave()

        @property
        def selection(self):
            Gdk.threads_enter()
            text = self._selection.wait_for_text()
            Gdk.threads_leave()
            return text

        @selection.setter
        def selection(self, new_content: str):
            Gdk.threads_enter()
            try:
                # This call might fail and raise an Exception.
                # If it does, make sure to release the mutex and not deadlock AutoKey.
                self._selection.set_text(new_content, -1)
            finally:
                Gdk.threads_leave()


class XInterfaceBase(threading.Thread):
    """
    Encapsulates the common functionality for the two X interface classes.
    """

    def __init__(self, mediator, app):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("XInterface-thread")
        self.mediator = mediator  # type: IoMediator
        self.app = app
        self.lastChars = [] # QT4 Workaround
        self.__enableQT4Workaround = False # QT4 Workaround
        self.shutdown = False
        
        # Event loop
        self.eventThread = threading.Thread(target=self.__eventLoop)
        self.queue = queue.Queue()
        
        # Event listener
        self.listenerThread = threading.Thread(target=self.__flushEvents)
        self.clipboard = Clipboard()

        self.__initMappings()

        # Set initial lock state
        ledMask = self.localDisplay.get_keyboard_control().led_mask
        mediator.set_modifier_state(Key.CAPSLOCK, (ledMask & CAPSLOCK_LEDMASK) != 0)
        mediator.set_modifier_state(Key.NUMLOCK, (ledMask & NUMLOCK_LEDMASK) != 0)

        # Window name atoms
        self.__NameAtom = self.localDisplay.intern_atom("_NET_WM_NAME", True)
        self.__VisibleNameAtom = self.localDisplay.intern_atom("_NET_WM_VISIBLE_NAME", True)
        
        #move detection of key map changes to X event thread in order to have QT and GTK detection
        # if not common.USING_QT:
            # self.keyMap = Gdk.Keymap.get_default()
            # self.keyMap.connect("keys-changed", self.on_keys_changed)
        
        self.__ignoreRemap = False
        
        self.eventThread.start()
        self.listenerThread.start()
        
    def __eventLoop(self):
        while True:
            method, args = self.queue.get()
            
            if method is None and args is None:
                break
            elif method is not None and args is None:
                logger.debug("__eventLoop: Got method {} with None arguments!".format(method))
            try:
                method(*args)
            except Exception as e:
                logger.exception("Error in X event loop thread")

            self.queue.task_done()

    def __enqueue(self, method: typing.Callable, *args):
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
        self.rootWindow.change_attributes(event_mask=X.SubstructureNotifyMask|X.StructureNotifyMask)
        
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

        for keySym, ak in XK_TO_AK_MAP.items():
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

        if logger.getEffectiveLevel() == logging.DEBUG:
            self.keymap_test()

    def keymap_test(self):
        code = self.localDisplay.keycode_to_keysym(108, 0)
        for attr in XK.__dict__.items():
            if attr[0].startswith("XK"):
                if attr[1] == code:
                    logger.debug("Alt-Grid: %s, %s", attr[0], attr[1])

        logger.debug("X Server Keymap, listing unmapped keys.")
        for char in "\\|`1234567890-=~!@#$%^&*()qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?":
            keyCodeList = list(self.localDisplay.keysym_to_keycodes(ord(char)))
            if not keyCodeList:
                logger.debug("No mapping for [%s]", char)
                
    def __needsMutterWorkaround(self, item):
        if Key.SUPER not in item.modifiers:
            return False
    
        try:
            output = subprocess.check_output(["ps", "-eo", "command"]).decode()
        except subprocess.CalledProcessError:
            pass # since this is just a nasty workaround, if anything goes wrong just disable it 
        else:
            lines = output.splitlines()
            
            for line in lines:
                if "gnome-shell" in line or "cinnamon" in line or "unity" in line:
                    return True
                
        return False

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
                if self.__needsMutterWorkaround(item):
                    self.__enqueue(self.__grabRecurse, item, self.rootWindow, False)

        # Grab hotkeys without a filter in root window
        for item in hotkeys:
            if item.get_applicable_regex() is None:
                self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, self.rootWindow)
                if self.__needsMutterWorkaround(item):
                    self.__enqueue(self.__grabRecurse, item, self.rootWindow, False)

        self.__enqueue(self.__recurseTree, self.rootWindow, hotkeys)

    def __recurseTree(self, parent, hotkeys):
        # Grab matching hotkeys in all open child windows
        try:
            children = parent.query_tree().children
        except:
            return # window has been destroyed
            
        for window in children:
            try:
                window_info = self.get_window_info(window, False)
                
                if window_info.wm_title or window_info.wm_class:
                    for item in hotkeys:
                        if item.get_applicable_regex() is not None and item._should_trigger_window_title(window_info):
                            self.__grabHotkey(item.hotKey, item.modifiers, window)
                            self.__grabRecurse(item, window, False)
                        
                self.__enqueue(self.__recurseTree, window, hotkeys)
            except:
                logger.exception("grab on window failed")
                
    def __ungrabAllHotkeys(self):
        """
        Ungrab all hotkeys in preparation for keymap change
        """
        c = self.app.configManager
        hotkeys = c.hotKeys + c.hotKeyFolders

        # Ungrab global hotkeys in root window, recursively
        for item in c.globalHotkeys:
            if item.enabled:
                self.__ungrabHotkey(item.hotKey, item.modifiers, self.rootWindow)
                if self.__needsMutterWorkaround(item):
                    self.__ungrabRecurse(item, self.rootWindow, False)
        
        # Ungrab hotkeys without a filter in root window, recursively
        for item in hotkeys:
            if item.get_applicable_regex() is None:
                self.__ungrabHotkey(item.hotKey, item.modifiers, self.rootWindow)
                if self.__needsMutterWorkaround(item):
                    self.__ungrabRecurse(item, self.rootWindow, False)
                
        self.__recurseTreeUngrab(self.rootWindow, hotkeys)
                
    def __recurseTreeUngrab(self, parent, hotkeys):
        # Ungrab matching hotkeys in all open child windows
        try:
            children = parent.query_tree().children
        except:
            return # window has been destroyed
            
        for window in children:
            try:
                window_info = self.get_window_info(window, False)
                
                if window_info.wm_title or window_info.wm_class:
                    for item in hotkeys:
                        if item.get_applicable_regex() is not None and item._should_trigger_window_title(window_info):
                            self.__ungrabHotkey(item.hotKey, item.modifiers, window)
                            self.__ungrabRecurse(item, window, False)
                        
                self.__enqueue(self.__recurseTreeUngrab, window, hotkeys)
            except:
                logger.exception("ungrab on window failed")

    def __grabHotkeysForWindow(self, window):
        """
        Grab all hotkeys relevant to the window

        Used when a new window is created
        """
        c = self.app.configManager
        hotkeys = c.hotKeys + c.hotKeyFolders
        window_info = self.get_window_info(window)
        for item in hotkeys:
            if item.get_applicable_regex() is not None and item._should_trigger_window_title(window_info):
                self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, window)
            elif self.__needsMutterWorkaround(item):
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

        except Exception as e:
            logger.warning("Failed to grab hotkey %r %r: %s", modifiers, key, str(e))

    def grab_hotkey(self, item):
        """
        Grab a hotkey.

        If the hotkey has no filter regex, it is global and is grabbed recursively from the root window
        If it has a filter regex, iterate over all children of the root and grab from matching windows
        """
        if item.get_applicable_regex() is None:
            self.__enqueue(self.__grabHotkey, item.hotKey, item.modifiers, self.rootWindow)
            if self.__needsMutterWorkaround(item):
                self.__enqueue(self.__grabRecurse, item, self.rootWindow, False)
        else:
            self.__enqueue(self.__grabRecurse, item, self.rootWindow)

    def __grabRecurse(self, item, parent, checkWinInfo=True):
        try:
            children = parent.query_tree().children
        except:
            return # window has been destroyed
                     
        for window in children:
            shouldTrigger = False
            
            if checkWinInfo:
                window_info = self.get_window_info(window, False)
                shouldTrigger = item._should_trigger_window_title(window_info)

            if shouldTrigger or not checkWinInfo:
                self.__grabHotkey(item.hotKey, item.modifiers, window)
                self.__grabRecurse(item, window, False)
            else:
                self.__grabRecurse(item, window)

    def ungrab_hotkey(self, item):
        """
        Ungrab a hotkey.

        If the hotkey has no filter regex, it is global and is grabbed recursively from the root window
        If it has a filter regex, iterate over all children of the root and ungrab from matching windows
        """
        import copy
        newItem = copy.copy(item)
        
        if item.get_applicable_regex() is None:
            self.__enqueue(self.__ungrabHotkey, newItem.hotKey, newItem.modifiers, self.rootWindow)
            if self.__needsMutterWorkaround(item):
                self.__enqueue(self.__ungrabRecurse, newItem, self.rootWindow, False)
        else:
            self.__enqueue(self.__ungrabRecurse, newItem, self.rootWindow)

    def __ungrabRecurse(self, item, parent, checkWinInfo=True):
        try:
            children = parent.query_tree().children
        except:
            return # window has been destroyed
                     
        for window in children:
            shouldTrigger = False
            
            if checkWinInfo:
                window_info = self.get_window_info(window, False)
                shouldTrigger = item._should_trigger_window_title(window_info)

            if shouldTrigger or not checkWinInfo:
                self.__ungrabHotkey(item.hotKey, item.modifiers, window)
                self.__ungrabRecurse(item, window, False)
            else:
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
        except Exception as e:
            logger.warning("Failed to ungrab hotkey %r %r: %s", modifiers, key, str(e))

    def lookup_string(self, keyCode, shifted, numlock, altGrid):
        if keyCode == 0:
            return "<unknown>"

        keySym = self.localDisplay.keycode_to_keysym(keyCode, 0)

        if keySym in XK_TO_AK_NUMLOCKED and numlock and not (numlock and shifted):
            return XK_TO_AK_NUMLOCKED[keySym]

        elif keySym in XK_TO_AK_MAP:
            return XK_TO_AK_MAP[keySym]
        else:
            index = 0
            if shifted: index += 1
            if altGrid: index += 4
            try:
                return chr(self.localDisplay.keycode_to_keysym(keyCode, index))
            except ValueError:
                return "<code%d>" % keyCode

    def send_string_clipboard(self, string: str, paste_command: autokey.model.phrase.SendMode):
        """
        This method is called from the IoMediator for Phrase expansion using one of the clipboard method.
        :param string: The to-be pasted string
        :param paste_command: Optional paste command. If None, the mouse selection is used. Otherwise, it contains a
         keyboard combination string, like '<ctrl>+v', or '<shift>+<insert>' that is sent to the target application,
         causing a paste operation to happen.
        """
        logger.debug("Sending string via clipboard: " + string)
        if common.USING_QT:
            if paste_command in (None, autokey.model.phrase.SendMode.SELECTION):
                self.__enqueue(self.app.exec_in_main, self._send_string_selection, string)
            else:
                self.__enqueue(self.app.exec_in_main, self._send_string_clipboard, string, paste_command)
        else:
            if paste_command in (None, autokey.model.phrase.SendMode.SELECTION):
                self.__enqueue(self._send_string_selection, string)
            else:
                self.__enqueue(self._send_string_clipboard, string, paste_command)
        logger.debug("Sending via clipboard enqueued.")

    def _send_string_clipboard(self, string: str, paste_command: autokey.model.phrase.SendMode):
        """
        Use the clipboard to send a string.
        """
        backup = self.clipboard.text  # Keep a backup of current content, to restore the original afterwards.
        if backup is None:
            logger.warning("Tried to backup the X clipboard content, but got None instead of a string.")
        self.clipboard.text = string
        try:
            self.mediator.send_string(paste_command.value)
        finally:
            self.ungrab_keyboard()
        # Because send_string is queued, also enqueue the clipboard restore, to keep the proper action ordering.
        self.__enqueue(self._restore_clipboard_text, backup)

    def _restore_clipboard_text(self, backup: str):
        """Restore the clipboard content."""
        # Pasting takes some time, so wait a bit before restoring the content. Otherwise the restore is done before
        # the pasting happens, causing the backup to be pasted instead of the desired clipboard content.
        time.sleep(0.2)
        self.clipboard.text = backup if backup is not None else ""

    def _send_string_selection(self, string: str):
        """Use the mouse selection clipboard to send a string."""
        backup = self.clipboard.selection  # Keep a backup of current content, to restore the original afterwards.
        if backup is None:
            logger.warning("Tried to backup the X PRIMARY selection content, but got None instead of a string.")
        self.clipboard.selection = string
        self.__enqueue(self._paste_using_mouse_button_2)
        self.__enqueue(self._restore_clipboard_selection, backup)

    def _restore_clipboard_selection(self, backup: str):
        """Restore the selection clipboard content."""
        # Pasting takes some time, so wait a bit before restoring the content. Otherwise the restore is done before
        # the pasting happens, causing the backup to be pasted instead of the desired clipboard content.

        # Programmatically pressing the middle mouse button seems VERY slow, so wait rather long.
        # It might be a good idea to make this delay configurable. There might be systems that need even longer.
        time.sleep(1)
        self.clipboard.selection = backup if backup is not None else ""

    def _paste_using_mouse_button_2(self):
        """Paste using the mouse: Press the second mouse button, then release it again."""
        focus = self.localDisplay.get_input_focus().focus
        xtest.fake_input(focus, X.ButtonPress, X.Button2)
        xtest.fake_input(focus, X.ButtonRelease, X.Button2)
        logger.debug("Mouse Button2 event sent.")

    def begin_send(self):
        self.__enqueue(self.__grab_keyboard)

    def finish_send(self):
        self.__enqueue(self.__ungrabKeyboard)

    def grab_keyboard(self):
        self.__enqueue(self.__grab_keyboard)

    def __grab_keyboard(self):
        focus = self.localDisplay.get_input_focus().focus
        focus.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)
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
        if not cm.ConfigManager.SETTINGS[cm_constants.ENABLE_QT4_WORKAROUND]:
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

            for i in range(len(availCodes) - 1):
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
                    logger.warning("Unable to send character %r", char)
            except Exception as e:
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
        except Exception as e:
            logger.warning("Error sending modified key %r %r: %s", modifiers, keyName, str(e))

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

    def mouse_press(self, xCoord, yCoord, button):
        self.__enqueue(self.__mousePress, xCoord, yCoord, button)

    def __mousePress(self, xCoord, yCoord, button):
        focus = self.localDisplay.get_input_focus().focus
        xtest.fake_input(focus, X.ButtonPress, button, x=xCoord, y=yCoord)
        self.__flush()

    def mouse_release(self, xCoord, yCoord, button):
        self.__enqueue(self.__mouseRelease, xCoord, yCoord, button)

    def __mouseRelease(self, xCoord, yCoord, button):
        focus = self.localDisplay.get_input_focus().focus
        xtest.fake_input(focus, X.ButtonRelease, button, x=xCoord, y=yCoord)
        self.__flush()

    def mouse_location(self):
        pos = self.rootWindow.query_pointer()
        return (pos.root_x, pos.root_y)

    def relative_mouse_location(self, window=None):
        #return relative mouse location within given window
        if window==None:
            window = self.localDisplay.get_input_focus().focus
        pos = window.query_pointer()
        return (pos.win_x, pos.win_y)

    def scroll_down(self, number):
        for i in range(0, number):
            self.__enqueue(self.__scroll, Button.SCROLL_DOWN)

    def scroll_up(self, number):
        for i in range(0, number):
            self.__enqueue(self.__scroll, Button.SCROLL_UP)

    def __scroll(self, button):
        focus = self.localDisplay.get_input_focus().focus
        x,y = self.mouse_location()
        xtest.fake_input(self=focus, event_type=X.ButtonPress, detail=button, x=x, y=y)
        xtest.fake_input(self=focus, event_type=X.ButtonRelease, detail=button, x=x, y=y)
        self.__flush()

    def move_cursor(self, xCoord, yCoord, relative=False, relative_self=False):
        self.__enqueue(self.__moveCursor, xCoord, yCoord, relative, relative_self)

    def __moveCursor(self, xCoord, yCoord, relative=False, relative_self=False):
        if relative:
            focus = self.localDisplay.get_input_focus().focus
            focus.warp_pointer(xCoord, yCoord)
            self.__flush()
            return

        if relative_self:
            pos = self.rootWindow.query_pointer()
            xCoord += pos.root_x
            yCoord += pos.root_y
        
        self.rootWindow.warp_pointer(xCoord,yCoord)
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
        logger.debug("__flushEvents: Entering event loop.")
        while True:
            try:
                readable, w, e = select.select([self.localDisplay], [], [], 1)
                time.sleep(1)
                if self.localDisplay in readable:
                    createdWindows = []
                    destroyedWindows = []
                    
                    for x in range(self.localDisplay.pending_events()):
                        event = self.localDisplay.next_event()
                        if event.type == X.CreateNotify:
                            createdWindows.append(event.window)
                        if event.type == X.DestroyNotify:
                            destroyedWindows.append(event.window)
                        if event.type == X.MappingNotify:
                            logger.debug("X Mapping Event Detected")
                            self.on_keys_changed()
                            
                    for window in createdWindows:
                        if window not in destroyedWindows:
                            self.__enqueue(self.__grabHotkeysForWindow, window)

                if self.shutdown:
                    break
            except ConnectionClosedError:
                # Autokey does not properly exit on logout. It causes an infinite exception loop, accumulating stack
                # traces along. This acts like a memory leak, filling the system RAM until it hits an OOM condition.
                # TODO: implement a proper exit mechanic that gracefully exits AutoKey in this case.
                # Maybe react to a dbus message that announces the session end, before the X server forcefully closes
                # the connection.
                # See https://github.com/autokey/autokey/issues/198 for details
                logger.exception("__flushEvents: Connection to the X server closed. Forcefully exiting Autokey now.")
                import os
                os._exit(1)
            except Exception:
                logger.exception("__flushEvents: Some exception occured:")
                pass
        logger.debug("__flushEvents: Left event loop.")

    def handle_keypress(self, keyCode):
        self.__enqueue(self.__handleKeyPress, keyCode)
    
    def __handleKeyPress(self, keyCode):
        focus = self.localDisplay.get_input_focus().focus

        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_down(modifier)
        else:
            window_info = self.get_window_info(focus)
            self.mediator.handle_keypress(keyCode, window_info)

    def handle_keyrelease(self, keyCode):
        self.__enqueue(self.__handleKeyrelease, keyCode)
    
    def __handleKeyrelease(self, keyCode):
        modifier = self.__decodeModifier(keyCode)
        if modifier is not None:
            self.mediator.handle_modifier_up(modifier)
            
    def handle_mouseclick(self, button, x, y):
        self.__enqueue(self.__handleMouseclick, button, x, y)
        
    def __handleMouseclick(self, button, x, y):
        # Sleep a bit to timing issues. A mouse click might change the active application.
        # If so, the switch happens asynchronously somewhere during the execution of the first two queries below,
        # causing the queried window title (and maybe the window class or even none of those) to be invalid.
        time.sleep(0.005)  # TODO: may need some tweaking
        window_info = self.get_window_info()
        
        if x is None and y is None:
            ret = self.localDisplay.get_input_focus().focus.query_pointer()
            self.mediator.handle_mouse_click(ret.root_x, ret.root_y, ret.win_x, ret.win_y, button, window_info)
        else:
            focus = self.localDisplay.get_input_focus().focus
            try:
                rel = focus.translate_coords(self.rootWindow, x, y)
                self.mediator.handle_mouse_click(x, y, rel.x, rel.y, button, window_info)
            except:
                self.mediator.handle_mouse_click(x, y, 0, 0, button, window_info)

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
        if cm.ConfigManager.SETTINGS[cm_constants.ENABLE_QT4_WORKAROUND] or self.__enableQT4Workaround:
            self.__doQT4Workaround(keyCode)
        self.__sendKeyPressEvent(keyCode, modifiers, theWindow)
        self.__sendKeyReleaseEvent(keyCode, modifiers, theWindow)

    def __checkWorkaroundNeeded(self):
        focus = self.localDisplay.get_input_focus().focus
        window_info = self.get_window_info(focus)
        w = self.app.configManager.workAroundApps
        if w.match(window_info.wm_title) or w.match(window_info.wm_class):
            self.__enableQT4Workaround = True
        else:
            self.__enableQT4Workaround = False

    def __doQT4Workaround(self, keyCode):
        if len(self.lastChars) > 0:
            if keyCode in self.lastChars:
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

    def __lookupKeyCode(self, char: str) -> int:
        if char in AK_TO_XK_MAP:
            return self.localDisplay.keysym_to_keycode(AK_TO_XK_MAP[char])
        elif char.startswith("<code"):
            return int(char[5:-1])
        else:
            try:
                return self.localDisplay.keysym_to_keycode(ord(char))
            except Exception as e:
                logger.error("Unknown key name: %s", char)
                raise

    def get_window_info(self, window=None, traverse: bool=True) -> WindowInfo:
        try:
            if window is None:
                window = self.localDisplay.get_input_focus().focus
            return self._get_window_info(window, traverse)
        except error.BadWindow:
            logger.warning("Got BadWindow error while requesting window information.")
            return self._create_window_info(window, "", "")

    def _get_window_info(self, window, traverse: bool, wm_title: str=None, wm_class: str=None) -> WindowInfo:
        new_wm_title = self._try_get_window_title(window)
        new_wm_class = self._try_get_window_class(window)

        if not wm_title and new_wm_title:  # Found title, update known information
            wm_title = new_wm_title
        if not wm_class and new_wm_class:  # Found class, update known information
            wm_class = new_wm_class

        if traverse:
            # Recursive operation on the parent window
            if wm_title and wm_class:  # Both known, abort walking the tree and return the data.
                return self._create_window_info(window, wm_title, wm_class)
            else:  # At least one property is still not known. So walk the window tree up.
                parent = window.query_tree().parent
                # Stop traversal, if the parent is not a window. When querying the parent, at some point, an integer
                # is returned. Then just stop following the tree.
                if isinstance(parent, int):
                    # At this point, wm_title or wm_class may still be None. The recursive call with traverse=False
                    # will replace any None with an empty string. See below.
                    return self._get_window_info(window, False, wm_title, wm_class)
                else:
                    return self._get_window_info(parent, traverse, wm_title, wm_class)

        else:
            # No recursion, so fill unknown values with empty strings.
            if wm_title is None:
                wm_title = ""
            if wm_class is None:
                wm_class = ""
            return self._create_window_info(window, wm_title, wm_class)

    def _create_window_info(self, window, wm_title: str, wm_class: str):
        """
        Creates a WindowInfo object from the window title and WM_CLASS.
        Also checks for the Java XFocusProxyWindow workaround and applies it if needed:

        Workaround for Java applications: Java AWT uses a XFocusProxyWindow class, so to get usable information,
        the parent window needs to be queried. Credits: https://github.com/mooz/xkeysnail/pull/32
        https://github.com/JetBrains/jdk8u_jdk/blob/master/src/solaris/classes/sun/awt/X11/XFocusProxyWindow.java#L35
        """
        if "FocusProxy" in wm_class:
            parent = window.query_tree().parent
            # Discard both the already known wm_class and window title, because both are known to be wrong.
            return self._get_window_info(parent, False)
        else:
            return WindowInfo(wm_title=wm_title, wm_class=wm_class)

    def _try_get_window_title(self, window) -> typing.Optional[str]:
        atom = self._try_read_property(window, self.__VisibleNameAtom)
        if atom is None:
            atom = self._try_read_property(window, self.__NameAtom)
        if atom:
            value = atom.value  # type: typing.Union[str, bytes]
            # based on python3-xlib version, atom.value may be a bytes object, then decoding is necessary.
            return value.decode("utf-8") if isinstance(value, bytes) else value
        else:
            return None

    @staticmethod
    def _try_read_property(window, property_name: str):
        """
        Try to read the given property of the given window.
        Returns the atom, if successful, None otherwise.
        """
        try:
            return window.get_property(property_name, 0, 0, 255)
        except error.BadAtom:
            return None

    @staticmethod
    def _try_get_window_class(window) -> typing.Optional[str]:
        wm_class = window.get_wm_class()
        if wm_class:
            return "{}.{}".format(wm_class[0], wm_class[1])
        else:
            return None

    def get_window_title(self, window=None, traverse=True) -> str:
        return self.get_window_info(window, traverse).wm_title

    def get_window_class(self, window=None, traverse=True) -> str:
        return self.get_window_info(window, traverse).wm_class

    def cancel(self):
        logger.debug("XInterfaceBase: Try to exit event thread.")
        self.queue.put_nowait((None, None))
        logger.debug("XInterfaceBase: Event thread exit marker enqueued.")
        self.shutdown = True
        logger.debug("XInterfaceBase: self.shutdown set to True. This should stop the listener thread.")
        self.listenerThread.join()
        self.eventThread.join()
        self.localDisplay.flush()
        self.localDisplay.close()
        self.join()


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
        if not len(reply.data) or str_or_bytes_to_bytes(reply.data)[0] < 2:
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


from autokey.model.key import Key, MODIFIERS
import autokey.configmanager.configmanager as cm

XK.load_keysym_group('xkb')

XK_TO_AK_MAP = {
           XK.XK_Shift_L: Key.SHIFT,
           XK.XK_Shift_R: Key.SHIFT,
           XK.XK_Caps_Lock: Key.CAPSLOCK,
           XK.XK_Control_L: Key.CONTROL,
           XK.XK_Control_R: Key.CONTROL,
           XK.XK_Alt_L: Key.ALT,
           XK.XK_Alt_R: Key.ALT,
           XK.XK_ISO_Level3_Shift: Key.ALT_GR,
           XK.XK_Super_L: Key.SUPER,
           XK.XK_Super_R: Key.SUPER,
           XK.XK_Hyper_L: Key.HYPER,
           XK.XK_Hyper_R: Key.HYPER,
           XK.XK_Meta_L: Key.META,
           XK.XK_Meta_R: Key.META,
           XK.XK_Num_Lock: Key.NUMLOCK,
           #SPACE: Key.SPACE,
           XK.XK_Tab: Key.TAB,
           XK.XK_Left: Key.LEFT,
           XK.XK_Right: Key.RIGHT,
           XK.XK_Up: Key.UP,
           XK.XK_Down: Key.DOWN,
           XK.XK_Return: Key.ENTER,
           XK.XK_BackSpace: Key.BACKSPACE,
           XK.XK_Scroll_Lock: Key.SCROLL_LOCK,
           XK.XK_Print: Key.PRINT_SCREEN,
           XK.XK_Pause: Key.PAUSE,
           XK.XK_Menu: Key.MENU,
           XK.XK_F1: Key.F1,
           XK.XK_F2: Key.F2,
           XK.XK_F3: Key.F3,
           XK.XK_F4: Key.F4,
           XK.XK_F5: Key.F5,
           XK.XK_F6: Key.F6,
           XK.XK_F7: Key.F7,
           XK.XK_F8: Key.F8,
           XK.XK_F9: Key.F9,
           XK.XK_F10: Key.F10,
           XK.XK_F11: Key.F11,
           XK.XK_F12: Key.F12,
           XK.XK_F13: Key.F13,
           XK.XK_F14: Key.F14,
           XK.XK_F15: Key.F15,
           XK.XK_F16: Key.F16,
           XK.XK_F17: Key.F17,
           XK.XK_F18: Key.F18,
           XK.XK_F19: Key.F19,
           XK.XK_F20: Key.F20,
           XK.XK_F21: Key.F21,
           XK.XK_F22: Key.F22,
           XK.XK_F23: Key.F23,
           XK.XK_F24: Key.F24,
           XK.XK_F25: Key.F25,
           XK.XK_F26: Key.F26,
           XK.XK_F27: Key.F27,
           XK.XK_F28: Key.F28,
           XK.XK_F29: Key.F29,
           XK.XK_F30: Key.F30,
           XK.XK_F31: Key.F31,
           XK.XK_F32: Key.F32,
           XK.XK_F33: Key.F33,
           XK.XK_F34: Key.F34,
           XK.XK_F35: Key.F35,
           XK.XK_Escape: Key.ESCAPE,
           XK.XK_Insert: Key.INSERT,
           XK.XK_Delete: Key.DELETE,
           XK.XK_Home: Key.HOME,
           XK.XK_End: Key.END,
           XK.XK_Page_Up: Key.PAGE_UP,
           XK.XK_Page_Down: Key.PAGE_DOWN,
           XK.XK_KP_Insert: Key.NP_INSERT,
           XK.XK_KP_Delete: Key.NP_DELETE,
           XK.XK_KP_End: Key.NP_END,
           XK.XK_KP_Down: Key.NP_DOWN,
           XK.XK_KP_Page_Down: Key.NP_PAGE_DOWN,
           XK.XK_KP_Left: Key.NP_LEFT,
           XK.XK_KP_Begin: Key.NP_5,
           XK.XK_KP_Right: Key.NP_RIGHT,
           XK.XK_KP_Home: Key.NP_HOME,
           XK.XK_KP_Up: Key.NP_UP,
           XK.XK_KP_Page_Up: Key.NP_PAGE_UP,
           XK.XK_KP_Divide: Key.NP_DIVIDE,
           XK.XK_KP_Multiply: Key.NP_MULTIPLY,
           XK.XK_KP_Add: Key.NP_ADD,
           XK.XK_KP_Subtract: Key.NP_SUBTRACT,
           XK.XK_KP_Enter: Key.ENTER,
           XK.XK_space: ' '
           }

AK_TO_XK_MAP = dict((v,k) for k, v in XK_TO_AK_MAP.items())

XK_TO_AK_NUMLOCKED = {
           XK.XK_KP_Insert: "0",
           XK.XK_KP_Delete: ".",
           XK.XK_KP_End: "1",
           XK.XK_KP_Down: "2",
           XK.XK_KP_Page_Down: "3",
           XK.XK_KP_Left: "4",
           XK.XK_KP_Begin: "5",
           XK.XK_KP_Right: "6",
           XK.XK_KP_Home: "7",
           XK.XK_KP_Up: "8",
           XK.XK_KP_Page_Up: "9",
           XK.XK_KP_Divide: "/",
           XK.XK_KP_Multiply: "*",
           XK.XK_KP_Add: "+",
           XK.XK_KP_Subtract: "-",
           XK.XK_KP_Enter: Key.ENTER
           }
