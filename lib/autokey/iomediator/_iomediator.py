import threading
import queue
import logging

from autokey.configmanager.configmanager import ConfigManager
from autokey.configmanager.configmanager_constants import INTERFACE_TYPE
from autokey.interface import XRecordInterface, AtSpiInterface
from autokey.model import SendMode

from .key import Key
from .constants import X_RECORD_INTERFACE, KEY_SPLIT_RE, MODIFIERS, HELD_MODIFIERS

CURRENT_INTERFACE = None
_logger = logging.getLogger("iomediator")


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
        
        # Modifier tracking
        self.modifiers = {
                          Key.CONTROL: False,
                          Key.ALT: False,
                          Key.ALT_GR: False,
                          Key.SHIFT: False,
                          Key.SUPER: False,
                          Key.HYPER: False,
                          Key.META: False,
                          Key.CAPSLOCK: False,
                          Key.NUMLOCK: False
                          }
        
        if self.interfaceType == X_RECORD_INTERFACE:
            self.interface = XRecordInterface(self, service.app)
        else:
            self.interface = AtSpiInterface(self, service.app)

        global CURRENT_INTERFACE
        CURRENT_INTERFACE = self.interface
        _logger.info("Created IoMediator instance, current interface is: {}".format(CURRENT_INTERFACE))
        
    def shutdown(self):
        _logger.debug("IoMediator shutting down")
        self.interface.cancel()
        self.queue.put_nowait((None, None))
        _logger.debug("Waiting for IoMediator thread to end")
        self.join()
        _logger.debug("IoMediator shutdown completed")

    # Callback methods for Interfaces ----

    def set_modifier_state(self, modifier, state):
        _logger.debug("Set modifier %s to %r", modifier, state)
        self.modifiers[modifier] = state
    
    def handle_modifier_down(self, modifier):
        """
        Updates the state of the given modifier key to 'pressed'
        """
        _logger.debug("%s pressed", modifier)
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
        _logger.debug("%s released", modifier)
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
            
            for target in self.listeners:
                target.handle_keypress(raw_key, modifiers, key, window_info)

            self.queue.task_done()
            
    def handle_mouse_click(self, root_x, root_y, rel_x, rel_y, button, window_info):
        for target in self.listeners:
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
        
        _logger.debug("Send via event interface")
        self._clear_modifiers()
        modifiers = []
        for section in KEY_SPLIT_RE.split(string):
            if len(section) > 0:
                if Key.is_key(section[:-1]) and section[-1] == '+' and section[:-1] in MODIFIERS:
                    # Section is a modifier application (modifier followed by '+')
                    modifiers.append(section[:-1])
                    
                else:
                    if len(modifiers) > 0:
                        # Modifiers ready for application - send modified key
                        if Key.is_key(section):
                            self.interface.send_modified_key(section, modifiers)
                            modifiers = []
                        else:
                            self.interface.send_modified_key(section[0], modifiers)
                            if len(section) > 1:
                                self.interface.send_string(section[1:])
                            modifiers = []
                    else:
                        # Normal string/key operation
                        if Key.is_key(section):
                            self.interface.send_key(section)
                        else:
                            self.interface.send_string(section)
                            
        self._reapply_modifiers()
        
    def paste_string(self, string, paste_command: SendMode):
        if len(string) > 0:
            _logger.debug("Send via clipboard")
            self.interface.send_string_clipboard(string, paste_command)

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
                
        self.send_backspace(backspaces)

    def send_key(self, key_name):
        key_name = key_name.replace('\n', "<enter>")
        self.interface.send_key(key_name)

    def press_key(self, key_name):
        key_name = key_name.replace('\n', "<enter>")
        self.interface.fake_keydown(key_name)

    def release_key(self, key_name):
        key_name = key_name.replace('\n', "<enter>")
        self.interface.fake_keyup(key_name)

    def fake_keypress(self, key_name):
        key_name = key_name.replace('\n', "<enter>")
        self.interface.fake_keypress(key_name)

    def send_left(self, count):
        """
        Sends the given number of left key presses.
        """
        for i in range(count):
            self.interface.send_key(Key.LEFT)

    def send_right(self, count):
        for i in range(count):
            self.interface.send_key(Key.RIGHT)
    
    def send_up(self, count):
        """
        Sends the given number of up key presses.
        """        
        for i in range(count):
            self.interface.send_key(Key.UP)

    def send_backspace(self, count):
        """
        Sends the given number of backspace key presses.
        """
        for i in range(count):
            self.interface.send_key(Key.BACKSPACE)

    def flush(self):
        self.interface.flush()
        
    # Utility methods ----
    
    def _clear_modifiers(self):
        self.releasedModifiers = []
        
        for modifier in list(self.modifiers.keys()):
            if self.modifiers[modifier] and modifier not in (Key.CAPSLOCK, Key.NUMLOCK):
                self.releasedModifiers.append(modifier)
                self.interface.release_key(modifier)

    def _reapply_modifiers(self):
        for modifier in self.releasedModifiers:
            self.interface.press_key(modifier)

    def _get_modifiers_on(self):
        modifiers = []
        for modifier in HELD_MODIFIERS:
            if self.modifiers[modifier]:
                modifiers.append(modifier)
        
        modifiers.sort()
        return modifiers
