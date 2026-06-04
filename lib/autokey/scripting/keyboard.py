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
"""Keyboard Functions"""

import typing
import time

import autokey.model.phrase
import autokey.iomediator.waiter as waiter
from autokey import iomediator, model
from typing import Callable

import autokey.configmanager.configmanager as cm
import autokey.configmanager.configmanager_constants as cm_constants

class Keyboard:
    """
    Provides access to the keyboard for event generation.
    """
    SendMode = autokey.model.phrase.SendMode

    def __init__(self, mediator):
        """Initialize the Keyboard"""
        self.mediator = mediator  # type: iomediator.IoMediator
        """See C{IoMediator} documentation"""

    def send_keys(self, key_string, delay = 0, send_mode: typing.Union[
        autokey.model.phrase.SendMode, int] = autokey.model.phrase.SendMode.KEYBOARD):
        """
        Send a sequence of keys via keyboard events as the default or via clipboard pasting.
        Because the clipboard can only contain
        printable characters, special keys and embedded key combinations can only be sent in keyboard mode.

        Trying to send special keys using a clipboard pasting method will paste the literal representation
        (e.g. "<ctrl>+<f11>") instead of the actual special key or key combination.

        Usage: C{keyboard.send_keys(keyString)}

        :param key_string: string of keys to send. Special keys are only possible in keyboard mode.
        :param delay: delay, in milliseconds, between sending each keystroke.  Only effective under Wayland, has no effect on X11 systems.
        :param send_mode: Determines how the string is sent.
        """

        if not isinstance(key_string, str):
            raise TypeError("Only strings can be sent using this function")
        send_mode = _validate_send_mode(send_mode)

        #  @dlk3 Fix for #19 - Temporarily change the setting for the uinput keystoke delay
        if delay > 0:
            saved_delay = cm.ConfigManager.SETTINGS[cm_constants.DELAY] 
            cm.ConfigManager.SETTINGS[cm_constants.DELAY] = saved_delay + delay

        self.mediator.begin_send()
        try:
            if send_mode is autokey.model.phrase.SendMode.KEYBOARD:
                self.mediator.send_string(key_string)
            else:
                self.mediator.paste_string(key_string, send_mode)
        finally:
            self.mediator.finish_send()
        
        #  @dlk3 Fix for #19 - Temporarily change the setting for the uinput keystoke delay
        if delay > 0:
            time.sleep(len(key_string) * delay / 1000)    # Give the thread that does the typing time to complete
            cm.ConfigManager.SETTINGS[cm_constants.DELAY] = saved_delay

    def send_key(self, key, repeat=1):
        """
        Send a keyboard event

        Usage: C{keyboard.send_key(key, repeat=1)}

        :param key: the key to be sent (e.g. "s" or "<enter>")
        :param repeat: number of times to repeat the key event
        """
        for _ in range(repeat):
            self.mediator.send_key(key)
        self.mediator.flush()

    def press_key(self, key):
        """
        Send a key down event

        Usage: C{keyboard.press_key(key)}

        The key will be treated as down until a matching release_key() is sent.
        :param key: they key to be pressed (e.g. "s" or "<enter>")
        """
        self.mediator.press_key(key)

    def release_key(self, key):
        """
        Send a key up event

        Usage: C{keyboard.release_key(key)}

        If the specified key was not made down using press_key(), the event will be
        ignored.
        :param key: the key to be released (e.g. "s" or "<enter>")
        """
        self.mediator.release_key(key)

    def fake_keypress(self, key, repeat=1):
        """
        Fake a keypress

        Usage: C{keyboard.fake_keypress(key, repeat=1)}

        Uses XTest to 'fake' a keypress. This is useful to send keypresses to some
        applications which won't respond to keyboard.send_key()

        :param key: the key to be sent (e.g. "s" or "<enter>")
        :param repeat: number of times to repeat the key event
        """
        for _ in range(repeat):
            self.mediator.fake_keypress(key)

    def wait_for_keypress(self, key, modifiers: list=None, timeOut=10.0):
        """
        Wait for a keypress or key combination

        Usage: C{keyboard.wait_for_keypress(self, key, modifiers=[], timeOut=10.0)}

        Note: this function cannot be used to wait for modifier keys on their own


        :param key: the key to wait for
        :param modifiers: list of modifiers that should be pressed with the key
        :param timeOut: maximum time, in seconds, to wait for the keypress to occur
        """
        if modifiers is None:
            modifiers = []
        w = waiter.Waiter(key, modifiers, None, None, None, timeOut)
        self.mediator.listeners.append(w)
        rtn = w.wait()
        self.mediator.listeners.remove(w)
        return rtn

    def wait_for_keyevent(self, check: Callable[[any,str,list,str], bool], name: str = None, timeOut=10.0):
        """
        Wait for a key event, potentially accumulating the intervening characters
        Usage: C{keyboard.wait_for_keypress(self, check, name=None, timeOut=10.0)}
        :param check: a function that returns True or False to signify we've finished waiting
        :param name: only one waiter can have this name. Used to prevent more threads waiting on this.
        :param timeOut: maximum time, in seconds, to wait for the keypress to occur
        Example:

        .. code-block:: python

            # Accumulate the traditional emacs C-u prefix arguments
            # See https://www.gnu.org/software/emacs/manual/html_node/elisp/Prefix-Command-Arguments.html
            def check(waiter,rawKey,modifiers,key,*args):
                isCtrlU = (key == 'u' and len(modifiers) == 1 and modifiers[0] == '<ctrl>')
                if isCtrlU: # If we get here, they've already pressed C-u at least 2x
                    try:
                        val = int(waiter.result) * 4
                        waiter.result = str(val)
                    except ValueError:
                        waiter.result = "16"
                    return False
                elif any(m == "<ctrl>" or m == "<alt>" or m == "<meta>" or m == "<super>" or m == "<hyper>" for m in modifiers):
                    # Some other control character is an indication we're done.
                    if waiter.result is None or waiter.result == "":
                        waiter.result = "4"
                    store.set_global_value("emacs-prefix-arg", waiter.result)
                    return True
                else: # accumulate as a string
                    waiter.result = waiter.result + key
                    return False
                    
            keyboard.wait_for_keyevent(check, "emacs-prefix")
        """
        if name is None or not any(elem.name == name for elem in self.mediator.listeners):
            w = waiter.Waiter(None, None, None, check, name, timeOut)
            self.mediator.listeners.append(w)
            rtn = w.wait()
            self.mediator.listeners.remove(w)
            return rtn
        return False

def _validate_send_mode(send_mode):
    permissible_values = "\n".join("keyboard.{}".format(mode) for mode in map(str, autokey.model.phrase.SendMode))
    if isinstance(send_mode, int):
        if send_mode in range(len(autokey.model.phrase.SendMode)):
            send_mode = tuple(autokey.model.phrase.SendMode)[send_mode]  # type: model.SendMode
        else:
            permissible_values = "\n".join(
                "{}: keyboard.{}".format(
                    number, str(constant)) for number, constant in enumerate(autokey.model.phrase.SendMode)
            )
            raise ValueError(
                "send_mode out of range for index-based access. "
                "Permissible values are:\n{}".format(permissible_values))
    elif isinstance(send_mode, str):
        try:
            send_mode = autokey.model.phrase.SendMode(send_mode)
        except ValueError as v:
            raise ValueError("Permissible values are: " + permissible_values) from v
    elif send_mode is None:  # Selection has value None
        send_mode = autokey.model.phrase.SendMode.SELECTION
    elif not isinstance(send_mode, autokey.model.phrase.SendMode):
        raise TypeError("Unsupported type for send_mode parameter: {} Use one of: {}".format(send_mode, permissible_values))
    return send_mode
