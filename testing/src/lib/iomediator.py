
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

XLIB_INTERFACE = "XLib"
ATSPI_INTERFACE = "AT-SPI"

# Key codes
KEY_UP = "up"
KEY_LEFT = "left"
KEY_BACKSPACE = "backspace"
KEY_TAB = "\t"

# Modifier keys
KEY_CONTROL = "ctrl"
KEY_ALT = "alt"
KEY_ALT_GR = "alt_gr"
KEY_SHIFT = "shift"
KEY_SUPER = "super"
KEY_CAPSLOCK = "capslock"

MODIFIERS = [KEY_CONTROL, KEY_ALT, KEY_ALT_GR, KEY_SHIFT, KEY_SUPER, KEY_CAPSLOCK]
NON_PRINTING_MODIFIERS = [KEY_CONTROL, KEY_ALT, KEY_SUPER]

CHAR_NEWLINE = '\n'
CHAR_SPACE = ' '

import interface

class IoMediator:
    """
    The IoMediator is responsible for tracking the state of modifier keys and
    interfacing with the various Interface classes to obtain the correct
    characters to pass to the expansion service. 
    
    This class must not store or maintain any configuration details.
    """
    
    def __init__(self, service, interface):
        self.service = service
        self.interfaceType = interface
        
        # Modifier tracking
        self.modifiers = {
                          KEY_CONTROL : False,
                          KEY_ALT : False,
                          KEY_ALT_GR: False,
                          KEY_SHIFT : False,
                          KEY_SUPER : False,
                          KEY_CAPSLOCK : False                         
                          }
        
    def start(self):
        """
        Starts the underlying keystroke interface sending and receiving events.
        """
        if self.interfaceType == XLIB_INTERFACE:
            self.interface = interface.XLibInterface(self)
        else:
            self.interface = interface.AtSpiInterface(self)
        self.interface.start()
        
    def pause(self):
        """
        Stops the underlying keystroke interface from sending and receiving events.
        """        
        self.interface.cancel()
        
    def switch_interface(self, interface):
        """
        Switch the interface being used to receive and send key events to
        the given interface.
        
        Precondition: service must be running
        """
        self.pause()
        self.interfaceType = interface
        self.start()
        
    # Methods for Interfaces ----
    
    def handle_modifier_down(self, modifier):
        """
        Updates the state of the given modifier key to 'pressed'
        """
        if modifier == KEY_CAPSLOCK:
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
        # Caps lock is handled on key down only
        if not modifier == KEY_CAPSLOCK:
            self.modifiers[modifier] = False
                
    
    def handle_keypress(self, keyCode):
        """
        Looks up the character for the given key code, applying any 
        modifiers currently in effect, and passes it to the expansion service.
        """
        if self.__isNonPrintingModifierOn():
            # Non printing keypress (e.g. Ctrl + Z)
            # TODO Service should respond by resetting input stack
            self.service.handle_keypress(None)
        else:
            if self.modifiers[KEY_CAPSLOCK] and self.modifiers[KEY_SHIFT]:
                key = self.interface.lookup_string(keyCode, False)
            elif self.modifiers[KEY_CAPSLOCK] or self.modifiers[KEY_SHIFT]:
                key = self.interface.lookup_string(keyCode, True)
            else:
                key = self.interface.lookup_string(keyCode, False)
            self.service.handle_keypress(key)
            
    def handle_mouse_click(self):
        # Initial attempt at handling mouseclicks
        # Since we have no way of knowing where the caret is after the click,
        # just throw away the input buffer.
        self.service.handle_keypress(None)
        
    # Methods for expansion service ----
        
    def send_string(self, string):
        """
        Sends the given string for output.
        """
        self.__clearModifiers()
        self.interface.send_string(string.decode("utf-8"))
        self.__reapplyModifiers()
        
    def send_key(self, keyName):
        self.interface.send_key(keyName)
        
    def send_left(self, count):
        """
        Sends the given number of left key presses.
        """
        for i in range(count):
            self.interface.send_key(KEY_LEFT)
    
    def send_up(self, count):
        """
        Sends the given number of up key presses.
        """        
        for i in range(count):
            self.interface.send_key(KEY_UP)
            
    def send_backspace(self, count):
        """
        Sends the given number of backspace key presses.
        """        
        for i in range(count):
            self.interface.send_key(KEY_BACKSPACE)
            
    def flush(self):
        self.interface.flush()
            
    # Utility methods ----
    
    def __clearModifiers(self):
        self.releasedModifiers = []
        
        for modifier in self.modifiers.keys():
            if self.modifiers[modifier] and not modifier == KEY_CAPSLOCK:
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
    import time
    import expansionservice
    e = expansionservice.ExpansionService()
    e.start()
    time.sleep(15.0)
    #e.tempsendstring("blah")
    e.pause()
        
        
