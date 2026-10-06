# Copyright 2012-2025 Daniel Shub <daniel@shub.im>
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

"""AutoKey X interface."""
import threading
import time

import Xlib
import Xlib.display
import Xlib.XK
import Xlib.protocol

from .. import log
from ..config import config
from ..language import language
from ..model import HotKey, Script, Phrase
from .interface import Interface

logger = log.Log(__name__)

MODIFIER_KEYS = {
    'alt': Xlib.XK.XK_Mode_switch,
    'ctrl': Xlib.XK.Control_L,
    'meta': Xlib.XK.META_L,
    'shift': Xlib.XK.Shift_L,
}

class XInterface(Interface):
    """An interface to the X server via python-xlib."""

    def __init__(self):
        self.display = Xlib.display.Display()
        self.window = self.display.screen().root
        self._grabbed = False
        self._queue = []
        self._lock = threading.Lock()
        self._flush_lock = threading.Lock()
        self._flush_thread = None
        self._keys_down = set()
        self._modifier_keys_down = set()
        self._modifier_releases_pending = set()

    def _handle_event(self, event):
        """Handle an X event."""
        if isinstance(event, Xlib.protocol.event.KeyRelease):
            key_code = event.detail
            if key_code in self._modifier_keys_down:
                self._modifier_releases_pending.add(key_code)
        elif isinstance(event, Xlib.protocol.event.KeyPress):
            key_code = event.detail
            self._keys_down.add(key_code)

    def _release_modifiers(self):
        """Release any pending modifier key events."""
        with self._lock:
            releases = set(self._modifier_releases_pending)
            self._modifier_releases_pending.clear()

        for key_code in releases:
            if key_code in self._modifier_keys_down:
                self._modifier_keys_down.discard(key_code)
                self.display.core.AllowEvents(
                    Xlib.X.AsynchronousKeyboard,
                    Xlib.X.CurrentTime
                )
                self.window.ungrab_key(key_code, Xlib.X.AnyModifier)
                self.display.sync()

    def _flush_events(self):
        """Flush pending events to the X server."""
        while True:
            time.sleep(0.01)
            with self._flush_lock:
                if not self._queue:
                    continue
                events = list(self._queue)
                self._queue.clear()

            for event in events:
                try:
                    self._handle_event(event)
                except Exception:  # pylint: disable=broad-except
                    logger.debug("Error handling event", exc_info=True)

            self._release_modifiers()

    def start(self):
        """Start the interface."""
        self._flush_thread = threading.Thread(target=self._flush_events)
        self._flush_thread.daemon = True
        self._flush_thread.start()

    def stop(self):
        """Stop the interface."""
        if self._flush_thread is not None:
            self._flush_thread.join(timeout=1.0)
            self._flush_thread = None
        self.release_all_keys()

    def grab_key(self, key):
        """Grab a key combination."""
        if not self._grabbed:
            self.window.grab_key(
                key,
                Xlib.X.ControlMask | Xlib.X.Mod1Mask | Xlib.X.Mod2Mask |
                Xlib.X.Mod3Mask | Xlib.X.Mod4Mask | Xlib.X.Mod5Mask,
                Xlib.X.AsyncBoth,
                Xlib.X.SynchronousKeyboard,
                Xlib.X.SynchronousPointer
            )
            self.window.grab_key(
                key,
                Xlib.X.AnyModifier,
                Xlib.X.AsyncBoth,
                Xlib.X.SynchronousKeyboard,
                Xlib.X.SynchronousPointer
            )
            self._grabbed = True

    def ungrab_key(self, key):
        """Ungrab a key combination."""
        self.window.ungrab_key(key, Xlib.X.AnyModifier)
        self.window.ungrab_key(key, Xlib.X.ControlMask | Xlib.X.Mod1Mask |
                              Xlib.X.Mod2Mask | Xlib.X.Mod3Mask |
                              Xlib.X.Mod4Mask | Xlib.X.Mod5Mask)
        # Check if any other grabs remain
        remaining = False
        for grab_key in self.keys_down():
            if grab_key != key:
                remaining = True
                break
        if not remaining:
            self._grabbed = False

    def press_key(self, key):
        """Press a key."""
        self._keys_down.add(key)
        keycode = self.key_to_keycode(key)
        if keycode:
            self.window.click(btn=keycode,
                              win=Xlib.X.AnyWindow,
                              mods=Xlib.X.NoModifier,
                              pos=(0, 0),
                              rel=(0, 0))
            self.display.sync()
            time.sleep(0.01)

    def release_key(self, key):
        """Release a key."""
        self._keys_down.discard(key)
        keycode = self.key_to_keycode(key)
        if keycode:
            self.window.click(btn=keycode,
                              win=Xlib.X.AnyWindow,
                              mods=Xlib.X.NoModifier,
                              pos=(0, 0),
                              rel=(0, 0),
                              button=Xlib.X.ButtonRelease)
            self.display.sync()
            time.sleep(0.01)

    def release_all_keys(self):
        """Release all keys."""
        with self._lock:
            keys = set(self._keys_down)
            self._keys_down.clear()
            modifiers = set(self._modifier_keys_down)
            self._modifier_keys_down.clear()
            self._modifier_releases_pending.clear()

        for key in keys:
            try:
                keycode = self.key_to_keycode(key)
                if keycode:
                    self.window.click(btn=keycode,
                                      win=Xlib.X.AnyWindow,
                                      mods=Xlib.X.NoModifier,
                                      pos=(0, 0),
                                      rel=(0, 0),
                                      button=Xlib.X.ButtonRelease)
            except Exception:  # pylint: disable=broad-except
                pass

        for key in modifiers:
            try:
                keycode = self.key_to_keycode(key)
                if keycode:
                    self.window.click(btn=keycode,
                                      win=Xlib.X.AnyWindow,
                                      mods=Xlib.X.NoModifier,
                                      pos=(0, 0),
                                      rel=(0, 0),
                                      button=Xlib.X.ButtonRelease)
            except Exception:  # pylint: disable=broad-except
                pass
        self.display.sync()

    def key_to_keycode(self, key):
        """Convert a key name to an X keycode."""
        try:
            keycode = Xlib.XK.string_to_keysym(Xlib.XK.keycode_to_keysym(
                self.display.keysym_to_keycode(Xlib.XK.string_to_keysym(key))))
            return keycode
        except (Xlib.error.NoSuchIdentifier, AttributeError):
            return None

    def keys_down(self):
        """Return the set of keys currently down."""
        with self._lock:
            return set(self._keys_down)

    def add_hotkey(self, hotkey):
        """Add a hotkey to the system."""
        key = hotkey.key
        self.grab_key(key)

    def remove_hotkey(self, hotkey):
        """Remove a hotkey from the system."""
        key = hotkey.key
        self.ungrab_key(key)

    def add_script(self, script):
        """Add a script to the system."""
        pass

    def remove_script(self, script):
        """Remove a script from the system."""
        pass

    def add_phrase(self, phrase):
        """Add a phrase to the system."""
        pass

    def remove_phrase(self, phrase):
        """Remove a phrase from the system."""
        pass

    def listen_for_events(self):
        """Listen for X events."""
        while True:
            try:
                event = self.display.next_event()
                with self._lock:
                    self._queue.append(event)
            except Xlib.error.Xerror:
                break
            except Exception:  # pylint: disable=broad-except
                logger.debug("Error reading event", exc_info=True)
                time.sleep(0.1)
>>>ENDFILE<<<
