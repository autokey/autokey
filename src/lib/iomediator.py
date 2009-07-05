
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

X_RECORD_INTERFACE = "XRecord"
X_EVDEV_INTERFACE = "XEvDev"

# Key codes enumeration
class Key:

    LEFT = "<left>"
    RIGHT = "<right>"
    UP = "<up>"
    DOWN = "<down>"
    BACKSPACE = "<backspace>"
    TAB = "<tab>"
    RETURN = '\n'
    SPACE = ' '
    
    # Modifier keys
    CONTROL = "<ctrl>"
    ALT = "<alt>"
    ALT_GR = "<alt_gr>"
    SHIFT = "<shift>"
    SUPER = "<super>"
    CAPSLOCK = "<capslock>"
    
    F1 = "<f1>"
    F2 = "<f2>"
    F3 = "<f3>"
    F4 = "<f4>"
    F5 = "<f5>"
    F6 = "<f6>"
    F7 = "<f7>"
    F8 = "<f8>"
    F9 = "<f9>"
    F10 = "<f10>"
    F11 = "<f11>"
    F12 = "<f12>"
    
    # Other
    ESCAPE = "<escape>"
    INSERT = "<insert>"
    DELETE = "<delete>"
    HOME = "<home>"
    END = "<end>"
    PAGE_UP = "<page_up>"
    PAGE_DOWN = "<page_down>"

    @classmethod
    def is_key(klass, keyString):
        # Key strings must be treated as case insensitive - always convert to lowercase
        # before doing any comparisons
        return keyString.lower() in klass.__dict__.values() or keyString.startswith("<code")

import time, threading, Queue, re

MODIFIERS = [Key.CONTROL, Key.ALT, Key.ALT_GR, Key.SHIFT, Key.SUPER, Key.CAPSLOCK]
NON_PRINTING_MODIFIERS = [Key.CONTROL, Key.ALT, Key.SUPER]
NAVIGATION_KEYS = [Key.LEFT, Key.RIGHT, Key.UP, Key.DOWN, Key.BACKSPACE, Key.HOME, Key.END, Key.PAGE_UP, Key.PAGE_DOWN]

#KEY_SPLIT_RE = re.compile("(<.+?>\+{0,1})", re.UNICODE)
KEY_SPLIT_RE = re.compile("(<[^<>]+>\+?)", re.UNICODE)

from interface import *
from configurationmanager import ConfigurationManager

def threaded(f):
    
    def wrapper(*args):
        t = threading.Thread(target=f, args=args, name="KeypressHandlerThread")
        t.setDaemon(False)
        t.start()
        
    wrapper.__name__ = f.__name__
    wrapper.__dict__ = f.__dict__
    wrapper.__doc__ = f.__doc__
    return wrapper

class IoMediator(threading.Thread):
    """
    The IoMediator is responsible for tracking the state of modifier keys and
    interfacing with the various Interface classes to obtain the correct
    characters to pass to the expansion service. 
    
    This class must not store or maintain any configuration details.
    """
    
    # List of targets interested in receiving keypress, hotkey and mouse events
    listeners = []
    
    def __init__(self, service, interface):
        threading.Thread.__init__(self, name="KeypressHandler-thread")
        self.queue = Queue.Queue()
        #self.service = service
        self.listeners.append(service)
        self.interfaceType = interface
        
        # Modifier tracking
        self.modifiers = {
                          Key.CONTROL : False,
                          Key.ALT : False,
                          Key.ALT_GR: False,
                          Key.SHIFT : False,
                          Key.SUPER : False,
                          Key.CAPSLOCK : False                         
                          }
        
    def initialise(self):
        """
        Starts the underlying keystroke interface sending and receiving events.
        """
        self.__createInterface()
        self.interface.start()
        self.start()
        
    def __createInterface(self):
        if self.interfaceType == X_RECORD_INTERFACE:
            self.interface = XRecordInterface(self)
        else:
            self.interface = EvDevInterface(self)        
        
    def shutdown(self):
        self.interface.cancel()
        self.queue.put_nowait((None, None))
        
    def switch_interface(self, interface):
        """
        Switch the interface being used to receive and send key events to the
        given interface type.
        """
        self.interface.cancel()
        self.interfaceType = interface
        self.__createInterface()
        self.interface.start()
        
    # Callback methods for Interfaces ----
    
    def handle_modifier_down(self, modifier):
        """
        Updates the state of the given modifier key to 'pressed'
        """
        #print modifier + " pressed"
        if modifier == Key.CAPSLOCK:
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
        #print modifier + " released"
        # Caps lock is handled on key down only
        if not modifier == Key.CAPSLOCK:
            self.modifiers[modifier] = False
    
    def handle_keypress(self, keyCode, windowName):
        """
        Looks up the character for the given key code, applying any 
        modifiers currently in effect, and passes it to the expansion service.
        """
        self.queue.put_nowait((keyCode, windowName))
        
    def run(self):
        while True:
            keyCode, windowName = self.queue.get()
            
            if keyCode is None and windowName is None:
                break
            
            if self.__isNonPrintingModifierOn():
                key = self.interface.lookup_string(keyCode, False)
                modifiers = []
                for modifier, isOn in self.modifiers.iteritems():
                    if isOn:
                        modifiers.append(modifier)
                modifiers.sort()
                
                #self.service.handle_hotkey(key, modifiers, windowName)
                for target in self.listeners:
                    target.handle_hotkey(key, modifiers, windowName)
                
            else:
                if self.modifiers[Key.CAPSLOCK] and self.modifiers[Key.SHIFT]:
                    key = self.interface.lookup_string(keyCode, False)
                elif self.modifiers[Key.CAPSLOCK] or self.modifiers[Key.SHIFT]:
                    key = self.interface.lookup_string(keyCode, True)
                else:
                    key = self.interface.lookup_string(keyCode, False)
                
                #self.service.handle_keypress(key, windowName)
                for target in self.listeners:
                    target.handle_keypress(key, windowName)
                
                
            self.queue.task_done()
            
    def handle_mouse_click(self):
        #self.service.handle_mouseclick()
        for target in self.listeners:
            target.handle_mouseclick()
        
    # Methods for expansion service ----
        
    def send_string(self, string):
        """
        Sends the given string for output.
        """
        self.acquire_lock()
        k = Key()
        
        self.__clearModifiers()
        modifiers = []
        
        for section in KEY_SPLIT_RE.split(string.decode("utf-8")):
            if len(section) > 0:
                if k.is_key(section[:-1]) and section[-1] == '+' and section[:-1] in MODIFIERS:
                    # Section is a modifier application (modifier followed by '+')
                    modifiers.append(section[:-1])
                    
                else:
                    if len(modifiers) > 0:
                        # Modifiers ready for application - send modified key
                        if k.is_key(section):
                            self.interface.send_modified_key(section, modifiers)
                        else:
                            self.interface.send_modified_key(section[0], modifiers)
                            if len(section) > 1:
                                self.interface.send_string(section[1:])
                            modifiers = []
                    else:
                        # Normal string/key operation                    
                        if k.is_key(section):
                            self.interface.send_key(section)
                        else:
                            self.interface.send_string(section)
                        
        self.__reapplyModifiers()
        
        self.release_lock()
        
    def send_key(self, keyName):
        self.acquire_lock()
            
        self.interface.send_key(keyName)
        
        self.release_lock()
        
    def send_left(self, count):
        """
        Sends the given number of left key presses.
        """
        self.acquire_lock()
        
        for i in range(count):
            self.interface.send_key(Key.LEFT)
            
        self.release_lock()
    
    def send_up(self, count):
        """
        Sends the given number of up key presses.
        """        
        self.acquire_lock()
        
        for i in range(count):
            self.interface.send_key(Key.UP)
            
        self.release_lock()
        
    def send_backspace(self, count):
        """
        Sends the given number of backspace key presses.
        """
        self.acquire_lock()
        
        for i in range(count):
            self.interface.send_key(Key.BACKSPACE)
            
        self.release_lock()
            
    def flush(self):
        self.interface.flush()
        
    def acquire_lock(self):
        """
        Acquires the lock that is engaged while a key is pressed. 
        """
        self.interface.lock.acquire()
        
    def release_lock(self):
        """
        Releases the lock that is engaged while a key is pressed. 
        """
        self.interface.lock.release()
            
    # Utility methods ----
    
    def __clearModifiers(self):
        self.releasedModifiers = []
        
        for modifier in self.modifiers.keys():
            if self.modifiers[modifier] and not modifier == Key.CAPSLOCK:
                self.releasedModifiers.append(modifier)
                self.interface.release_key(modifier)
        
    def __reapplyModifiers(self):
        for modifier in self.releasedModifiers:
            self.interface.press_key(modifier)
            
    def __isNonPrintingModifierOn(self):
        for modifier in NON_PRINTING_MODIFIERS:
            if self.modifiers[modifier]:
                return True
        
        return False
    
if __name__ == "__main__":
    pass
        
