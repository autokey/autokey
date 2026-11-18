# Copyright (C) 2026 AutoKey contributors
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

"""
Tests for XInterfaceBase key mapping (re)initialisation.

These tests run without an X server: Xlib.display.Display is replaced with a
factory that hands out mock connections.
"""

import queue
from unittest.mock import MagicMock

import pytest

import autokey.interface


@pytest.fixture
def opened_displays(monkeypatch):
    """Replace Xlib Display with a factory recording every opened connection."""
    displays = []

    def fake_display_factory(*args, **kwargs):
        connection = MagicMock()
        # No keycodes at all: keeps the keycode bookkeeping loops empty.
        connection.keysym_to_keycodes.return_value = []
        connection.get_keyboard_mapping.return_value = []
        displays.append(connection)
        return connection

    monkeypatch.setattr(autokey.interface.display, "Display", fake_display_factory)
    return displays


def make_interface() -> autokey.interface.XInterfaceBase:
    """Build an XInterfaceBase without running __init__ (it needs a live X connection)."""
    interface = autokey.interface.XInterfaceBase.__new__(autokey.interface.XInterfaceBase)
    interface.app = MagicMock()
    interface.app.configManager.globalHotkeys = []
    interface.app.configManager.hotKeys = []
    interface.app.configManager.hotKeyFolders = []
    interface.queue = queue.Queue()
    return interface


def test_first_initialisation_opens_a_connection_without_closing_anything(opened_displays):
    interface = make_interface()

    interface._XInterfaceBase__initMappings()

    assert interface.localDisplay is opened_displays[0]
    opened_displays[0].close.assert_not_called()


def test_reinitialising_the_key_mapping_closes_the_previous_connection(opened_displays):
    # Every keyboard mapping change re-runs __initMappings (on_keys_changed →
    # __delayedInitMappings). Dropping the old Display without closing it leaks
    # one X client connection per change, until the X server client limit is
    # reached. See issue #1326.
    interface = make_interface()
    interface._XInterfaceBase__initMappings()
    first = interface.localDisplay

    interface._XInterfaceBase__initMappings()

    first.close.assert_called_once_with()
    assert interface.localDisplay is opened_displays[1]
    assert interface.localDisplay is not first
