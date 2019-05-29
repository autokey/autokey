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

import typing

from autokey import iomediator, model


class Keyboard:
    """
    Provides access to the keyboard for event generation.
    """
    SendMode = model.SendMode

    def __init__(self, mediator):
        self.mediator = mediator  # type: iomediator.IoMediator

    def send_keys(self, key_string, send_mode: typing.Union[model.SendMode, int]=model.SendMode.KEYBOARD):
        """
        Send a sequence of keys via keyboard events as the default or via clipboard pasting.
        Because the clipboard can only contain
        printable characters, special keys and embedded key combinations can only be sent in keyboard mode.

        Trying to send special keys using a clipboard pasting method will paste the literal representation
        (e.g. "<ctrl>+<f11>") instead of the actual special key or key combination.


        Usage: C{keyboard.send_keys(keyString)}

        @param key_string: string of keys to send. Special keys are only possible in keyboard mode.
        @param send_mode: Determines how the string is send.
        """
        if not isinstance(key_string, str):
            raise TypeError("Only strings can be sent using this function")
        if isinstance(send_mode, int):
            if send_mode in range(len(model.SendMode)):
                send_mode = tuple(model.SendMode)[send_mode]  # type: mode.SendMode
            else:
                permissible = "\n".join(
                    "{}: keyboard.{}".format(
                        number, str(constant)) for number, constant in enumerate(model.SendMode)
                )
                raise ValueError(
                    "send_mode out of range for index-based access. "
                    "Permissible values are:\n{}".format(permissible))
        if not isinstance(send_mode, model.SendMode):
            permissible = "\n".join("keyboard.{}".format(mode) for mode in map(str, model.SendMode))
            raise TypeError(
                "send_mode must be set to an element from keyboard.SendMode (or an interger for index-based access). "
                "Permissible values are:\n{}".format(permissible))
        self.mediator.interface.begin_send()
        try:
            if send_mode is model.SendMode.KEYBOARD:
                self.mediator.send_string(key_string)
            else:
                self.mediator.paste_string(key_string, send_mode)
        finally:
            self.mediator.interface.finish_send()

    def send_key(self, key, repeat=1):
        """
        Send a keyboard event

        Usage: C{keyboard.send_key(key, repeat=1)}

        @param key: they key to be sent (e.g. "s" or "<enter>")
        @param repeat: number of times to repeat the key event
        """
        for _ in range(repeat):
            self.mediator.send_key(key)
        self.mediator.flush()

    def press_key(self, key):
        """
        Send a key down event

        Usage: C{keyboard.press_key(key)}

        The key will be treated as down until a matching release_key() is sent.
        @param key: they key to be pressed (e.g. "s" or "<enter>")
        """
        self.mediator.press_key(key)

    def release_key(self, key):
        """
        Send a key up event

        Usage: C{keyboard.release_key(key)}

        If the specified key was not made down using press_key(), the event will be
        ignored.
        @param key: they key to be released (e.g. "s" or "<enter>")
        """
        self.mediator.release_key(key)

    def fake_keypress(self, key, repeat=1):
        """
        Fake a keypress

        Usage: C{keyboard.fake_keypress(key, repeat=1)}

        Uses XTest to 'fake' a keypress. This is useful to send keypresses to some
        applications which won't respond to keyboard.send_key()

        @param key: they key to be sent (e.g. "s" or "<enter>")
        @param repeat: number of times to repeat the key event
        """
        for _ in range(repeat):
            self.mediator.fake_keypress(key)

    def wait_for_keypress(self, key, modifiers: list=None, timeOut=10.0):
        """
        Wait for a keypress or key combination

        Usage: C{keyboard.wait_for_keypress(self, key, modifiers=[], timeOut=10.0)}

        Note: this function cannot be used to wait for modifier keys on their own

        @param key: they key to wait for
        @param modifiers: list of modifiers that should be pressed with the key
        @param timeOut: maximum time, in seconds, to wait for the keypress to occur
        """
        if modifiers is None:
            modifiers = []
        w = iomediator.Waiter(key, modifiers, None, timeOut)
        return w.wait()
