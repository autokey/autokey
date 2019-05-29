# Copyright (C) 2019 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from unittest.mock import MagicMock
import itertools

import pytest
from hamcrest import *


from autokey.scripting import Keyboard


def create_keyboard() -> Keyboard:
    kb = Keyboard(MagicMock())

    return kb


@pytest.mark.parametrize("key_string, send_mode, expected_exception", [
    # Only string values allowed for key_string
    (12, Keyboard.SendMode.KEYBOARD, TypeError),
    (b"abc", Keyboard.SendMode.KEYBOARD, TypeError),
    # send_mode must be a SendMode element
    ("AB", "kb", TypeError),
    ("123", 42.5, TypeError),
    ("123", 42, ValueError)
])
def test_send_keys_type_checking(key_string, send_mode, expected_exception):
    keyboard = create_keyboard()
    assert_that(calling(keyboard.send_keys).with_args(key_string, send_mode), raises(expected_exception))
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.interface.begin_send.assert_not_called()
    mock_mediator.send_string.assert_not_called()
    mock_mediator.paste_string.assert_not_called()
    mock_mediator.interface.finish_send.assert_not_called()


def test_send_keys_send_mode_default():
    keyboard = create_keyboard()
    sent_string = "ABC"
    keyboard.send_keys(sent_string)
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.send_string.assert_called_once_with(sent_string)
    mock_mediator.interface.finish_send.assert_called_once()


def test_send_keys_send_mode_keyboard():
    keyboard = create_keyboard()
    sent_string = "ABC"
    keyboard.send_keys(sent_string, send_mode=keyboard.SendMode.KEYBOARD)
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.send_string.assert_called_once_with(sent_string)
    mock_mediator.interface.finish_send.assert_called_once()

def test_send_keys_send_mode_keyboard_index():
    keyboard = create_keyboard()
    sent_string = "ABC"
    keyboard.send_keys(sent_string, send_mode=list(keyboard.SendMode).index(keyboard.SendMode.KEYBOARD))
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.send_string.assert_called_once_with(sent_string)
    mock_mediator.interface.finish_send.assert_called_once()


@pytest.mark.parametrize("send_mode", itertools.chain(Keyboard.SendMode, range(len(Keyboard.SendMode))))
def test_send_keys_send_mode_clipboard(send_mode):
    kb_mode = Keyboard.SendMode.KEYBOARD
    mode_list = list(Keyboard.SendMode)
    if send_mode is kb_mode or send_mode == mode_list.index(kb_mode):
        # Skip keyboard mode for both value- and index-based access
        return
    keyboard = create_keyboard()
    sent_string = "ABC"
    keyboard.send_keys(sent_string, send_mode=send_mode)
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.paste_string.assert_called_once_with(
        sent_string,
        send_mode if isinstance(send_mode, Keyboard.SendMode) else mode_list[send_mode])
    mock_mediator.interface.finish_send.assert_called_once()
