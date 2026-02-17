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

import threading
import time
import queue
import os

import autokey
from autokey import common
from autokey.configmanager.configmanager import ConfigManager
from autokey.configmanager.configmanager_constants import INTERFACE_TYPE
from autokey.gnome_interface import GnomeExtensionWindowInterface
from autokey.sys_interface.clipboard import Clipboard
from autokey.model.phrase import SendMode

from autokey.model.key import Key, KEY_SPLIT_RE, MODIFIERS, HELD_MODIFIERS
from autokey.model.button import Button
from .constants import X_RECORD_INTERFACE

CURRENT_INTERFACE = None

logger = __import__("autokey.logger").logger.get_logger(__name__)


class IoMediator(threading.Thread):
    """
    The IoMediator is responsible for tracking the state of modifier keys and
    interfacing with the various Interface classes to obtain the correct
    characters to pass to the expansion service. 
    
    This class must not store or maintain any configuration details.
    """
    
    # List of targets interested in receiving keypress, hotkey and mouse events
    listeners = []
    
    def __init__(self, service):
        threading.Thread.__init__(self, name="KeypressHandler-thread")

        self.queue = queue.Queue()
        self.listeners.append(service)
        self.interfaceType = ConfigManager.SETTINGS[INTERFACE_TYPE]
        self.app = service.app
        
        # Modifier tracking
        self.modifiers = {}
        for key in MODIFIERS:
            self.modifiers[key]=False

        # self.interfaceType="uinput"
        session_type = common.SESSION_TYPE
        if session_type == "wayland":
            self.interfaceType = "uinput"
        elif session_type == "x11":
            pass
        elif session_type is None:
            pass

        if self.interfaceType == "uinput":
            logger.debug("Using gnome extension window interface")
            self.windowInterface = GnomeExtensionWindowInterface()
        else:
            from autokey.interface import XWindowInterface
            self.windowInterface = XWindowInterface()


        if self.interfaceType == "uinput":
            from autokey.uinput_interface import UInputInterface
            self.interface = UInputInterface(self, self.app)
        elif self.interfaceType == X_RECORD_INTERFACE:
            from autokey.interface import XRecordInterface
            self.interface = XRecordInterface(self, self.app)
        else:
            from autokey.interface import AtSpiInterface
            self.interface = AtSpiInterface(self, self.app)

        self.clipboard = Clipboard()

        global CURRENT_INTERFACE
        CURRENT_INTERFACE = self.interface
        logger.info("Created IoMediator instance, current interface is: {}".format(CURRENT_INTERFACE))

    def start(self):
        self.interface.initialise()
        self.interface.start()
        super().start()


    def shutdown(self):
        logger.debug("IoMediator shutting down")
        self.interface.cancel()
        logger.debug("queue.put_nowait()")
        self.queue.put_nowait((None, None))
        logger.debug("Waiting for IoMediator thread to end")
        self.join()
        logger.debug("IoMediator shutdown completed")

    def begin_send(self):
        self.interface.grab_keyboard()

    def finish_send(self):
        self.interface.ungrab_keyboard()

    def grab_hotkey(self, item):
        self.interface.grab_hotkey(item)
    def ungrab_hotkey(self, item):
        self.interface.ungrab_hotkey(item)

    # Callback methods for Interfaces ----

    def set_modifier_state(self, modifier, state):
        logger.debug("Set modifier %s to %r", modifier, state)
        self.modifiers[modifier] = state
    
    def handle_modifier_down(self, modifier):
        """
        Updates the state of the given modifier key to 'pressed'.

        :param modifier: Should be AutoKey Key value
        """
        logger.debug("%s pressed", modifier)
        if modifier in (Key.CAPSLOCK, Key.NUMLOCK):
            if self.modifiers[modifier]:
                self.modifiers[modifier] = False
            else:
                self.modifiers[modifier] = True
        else:
            self.modifiers[modifier] = True
        
    def handle_modifier_up(self, modifier):
        """
        Updates the state of the given modifier key to 'released'.
        """
        logger.debug("%s released", modifier)
        # Caps and num lock are handled on key down only
        if modifier not in (Key.CAPSLOCK, Key.NUMLOCK):
            self.modifiers[modifier] = False

    def handle_keypress(self, key_code, window_info):
        """
        Looks up the character for the given key code, applying any 
        modifiers currently in effect, and passes it to the expansion service.
        """
        self.queue.put_nowait((key_code, window_info))
        
    def run(self):
        while True:
            key_code, window_info = self.queue.get()
            if key_code is None and window_info is None:
                break
            
            num_lock = self.modifiers[Key.NUMLOCK]
            modifiers = self._get_modifiers_on()
            shifted = self.modifiers[Key.CAPSLOCK] ^ self.modifiers[Key.SHIFT]
            key = self.interface.lookup_string(key_code, shifted, num_lock, self.modifiers[Key.ALT_GR])
            raw_key = self.interface.lookup_string(key_code, False, False, False)

            # We make a copy here because the wait_for... functions modify the listeners,
            # and we want this processing cycle to complete before changing what happens
            logger.debug("Raw Key: {} | Modifiers: {} | Key: {} | Window Info: {}".format(raw_key, modifiers, key, window_info))
            for target in self.listeners.copy():
                target.handle_keypress(raw_key, modifiers, key, window_info)

            self.queue.task_done()
            
    def handle_mouse_click(self, root_x, root_y, rel_x, rel_y, button, window_info):
        # We make a copy here because the wait_for... functions modify the listeners,
        # and we want this processing cycle to complete before changing what happens
        for target in self.listeners.copy():
            target.handle_mouseclick(root_x, root_y, rel_x, rel_y, button, window_info)
        
    # Methods for expansion service ----

    def send_string(self, string: str):
        """
        Sends the given string for output.
        """
        if not string:
            return

        string = string.replace('\n', "<enter>")
        string = string.replace('\t', "<tab>")
        
        logger.debug("Send via event interface")
        self._clear_modifiers()
        IoMediator._send_string(string, self.interface)
        self._reapply_modifiers()

    # Mainly static for the purpose of testing
    @staticmethod
    def _send_string(string, interface):
        modifiers = []
        logger.debug("Sending string sections: %s", KEY_SPLIT_RE.split(string))
        for section in KEY_SPLIT_RE.split(string):
            if len(section) > 0:
                if Key.is_key(section[:-1]) and section[-1] == '+' and section[:-1] in MODIFIERS:
                    # Section is a modifier application (modifier followed by '+')
                    modifiers.append(section[:-1])

                else:
                    if len(modifiers) > 0:
                        # Modifiers ready for application - send modified key
                        if Key.is_key(section):
                            interface.send_modified_key(section, modifiers)
                            modifiers = []
                        else:
                            interface.send_modified_key(section[0], modifiers)
                            if len(section) > 1:
                                interface.send_string(section[1:])
                            modifiers = []
                    else:
                        # Normal string/key operation
                        if Key.is_key(section):
                            interface.send_key(section)
                        else:
                            interface.send_string(section)
        logger.debug("Finished Sending string?")

    def paste_string(self, string, paste_command: SendMode):
        """
        This method is called for Phrase expansion using one of the clipboard methods.
        :param string: The to-be pasted string
        :param paste_command: Optional paste command. If None, the mouse selection is used. Otherwise, it contains a
         keyboard combination string, like '<ctrl>+v', or '<shift>+<insert>' that is sent to the target application,
         causing a paste operation to happen.
        """
        if len(string) <= 0:
            return
        logger.debug("Sending string via clipboard: {}, PasteCommand: {}".format(string, paste_command))
        if paste_command in (None, SendMode.SELECTION):
            self.send_string_selection(string)
        else:
            self.send_string_clipboard(string, paste_command)

    def remove_string(self, string):
        backspaces = -1  # Start from -1 to discount the backspace already pressed by the user
        
        for section in KEY_SPLIT_RE.split(string):
            if Key.is_key(section):
                # TODO: Only a subset of keys defined in Key are printable, thus require a backspace.
                # Many keys are not printable, like the modifier keys or F-Keys.
                # If the current key is a modifier, it may affect the printability of the next character.
                # For example, if section == <alt>, and the next section begins with "+a", both the "+" and "a" are not
                # printable, because both belong to the keyboard combination "<alt>+a"
                backspaces += 1
            else:
                backspaces += len(section)
        logger.debug("Sending backspaces: %d", backspaces)
        self.send_backspace(backspaces)

    def send_key(self, key_name):
        key_name = key_name.replace('\n', "<enter>")
        self.interface.send_key(key_name)

    def press_key(self, key_name):
        key_name = key_name.replace('\n', "<enter>")
        self.interface.fake_keydown(key_name)

    def release_key(self, key_name):
        logger.debug("Release key: %s", key_name)
        key_name = key_name.replace('\n', "<enter>")
        self.interface.fake_keyup(key_name)

    def fake_keypress(self, key_name):
        key_name = key_name.replace('\n', "<enter>")
        self.interface.fake_keypress(key_name)

    def send_left(self, count):
        """
        Sends the given number of left key presses.
        """
        for _ in range(count):
            self.send_key(Key.LEFT)

    def send_right(self, count):
        for _ in range(count):
            self.send_key(Key.RIGHT)
    
    def send_up(self, count):
        """
        Sends the given number of up key presses.
        """        
        for _ in range(count):
            self.send_key(Key.UP)

    def send_backspace(self, count):
        """
        Sends the given number of backspace key presses.
        """
        for _ in range(count):
            self.send_key(Key.BACKSPACE)

    def flush(self):
        self.interface.flush()
        
    # Utility methods ----
    
    def _clear_modifiers(self):
        self.releasedModifiers = []
        
        for modifier in list(self.modifiers.keys()):
            if self.modifiers[modifier] and modifier not in (Key.CAPSLOCK, Key.NUMLOCK):
                self.releasedModifiers.append(modifier)
                self.release_key(modifier)

    def _reapply_modifiers(self):
        for modifier in self.releasedModifiers:
            self.press_key(modifier)

    def _get_modifiers_on(self):
        modifiers = []
        for modifier in HELD_MODIFIERS:
            if self.modifiers[modifier]:
                modifiers.append(modifier)
        
        modifiers.sort()
        return modifiers

    # Clipboard methods ----

    def send_string_clipboard(self, string: str, paste_command: autokey.model.phrase.SendMode):
        """
        This method is called from the IoMediator for Phrase expansion using one of the clipboard method.
        :param string: The to-be pasted string
        :param paste_command: Optional paste command. If None, the mouse selection is used. Otherwise, it contains a
         keyboard combination string, like '<ctrl>+v', or '<shift>+<insert>' that is sent to the target application,
         causing a paste operation to happen.
        """
        if common.USED_UI_TYPE == "QT":
            self.app.exec_in_main(self.__send_string_clipboard, string, paste_command)
        elif common.USED_UI_TYPE in ["GTK", "headless"]:
            self.__send_string_clipboard(string, paste_command)

    def send_string_selection(self, string: str):
        if common.USED_UI_TYPE == "QT":
            self.app.exec_in_main(self._send_string_selection, string)
        elif common.USED_UI_TYPE in ["GTK", "headless"]:
            self._send_string_selection(string)

    def __send_string_clipboard(self, string: str, paste_command: autokey.model.phrase.SendMode):
        """
        Use the clipboard to send a string.
        """
        backup = self.clipboard.text  # Keep a backup of current content, to restore the original afterwards.
        if backup is None:
            logger.warning("Tried to backup the X clipboard content, but got None instead of a string.")
        self.clipboard.text = string
        try:
            self.send_string(paste_command.value)
        finally:
            self.interface.ungrab_keyboard()
        # Because send_string is queued, also enqueue the clipboard restore, to keep the proper action ordering.
        self.__restore_clipboard_text(backup)

    def __restore_clipboard_text(self, backup: str):
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
        pos = self.interface.get_mouse_position()
        self.interface.send_mouse_click(pos[0], pos[1], Button.MIDDLE, False)
        self.__restore_clipboard_selection(backup)

    def __restore_clipboard_selection(self, backup: str):
        """Restore the selection clipboard content."""
        # Pasting takes some time, so wait a bit before restoring the content. Otherwise the restore is done before
        # the pasting happens, causing the backup to be pasted instead of the desired clipboard content.

        # Programmatically pressing the middle mouse button seems VERY slow, so wait rather long.
        # It might be a good idea to make this delay configurable. There might be systems that need even longer.
        time.sleep(1)
        self.clipboard.selection = backup if backup is not None else ""
