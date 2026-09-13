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

import time
import threading

from .iomediator import IoMediator

SEND_LOCK = threading.Lock()  # TODO: This is never accessed anywhere. Does creating this lock do anything?

# How long to wait for a click before giving up and notifying the dialog.
# Prevents the silent forever-wait described in issue #1189 when the session
# cannot observe the click (or window info cannot be resolved).
DEFAULT_DETECT_TIMEOUT_SECONDS = 15.0

logger = __import__("autokey.logger").logger.get_logger(__name__)


class WindowGrabber:

    def __init__(self, dialog, timeout_seconds=DEFAULT_DETECT_TIMEOUT_SECONDS):
        self.dialog = dialog
        self.timeout_seconds = timeout_seconds
        self._timer = None
        self._done = False
        self._lock = threading.Lock()

    def start(self):
        time.sleep(0.1)
        IoMediator.listeners.append(self)
        if self.timeout_seconds is not None and self.timeout_seconds > 0:
            self._timer = threading.Timer(self.timeout_seconds, self._on_timeout)
            self._timer.daemon = True
            self._timer.start()

    def cancel(self):
        """Stop listening and cancel any pending timeout. Safe to call more than once."""
        with self._lock:
            if self._done:
                return False
            self._done = True
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            if self in IoMediator.listeners:
                IoMediator.listeners.remove(self)
            return True

    def handle_keypress(self, raw_key, modifiers, key, *args):
        pass

    def handle_mouseclick(self, root_x, root_y, rel_x, rel_y, button, window_info):
        if not self.cancel():
            return
        self.dialog.receive_window_info(window_info)

    def _on_timeout(self):
        if not self.cancel():
            return
        logger.warning(
            "Window property detection timed out after %.1fs with no observed click "
            "(see issue #1189 — common on Wayland when mouse clicks are not forwarded).",
            self.timeout_seconds,
        )
        on_timeout = getattr(self.dialog, "receive_window_detect_timeout", None)
        if callable(on_timeout):
            on_timeout(self.timeout_seconds)
        else:
            # Fallback: re-enable UI if the dialog only exposes the detect button hook.
            logger.debug("Dialog has no receive_window_detect_timeout; timeout noted only in logs")
