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


from unittest.mock import MagicMock, Mock
import itertools
from typing import Union

import pytest
from hamcrest import *


from autokey.scripting import Keyboard


def create_keyboard(fail_sending: bool = False) -> Keyboard:
    """
    Creates a Keyboard instance connected to a mocked IOMediator instance. The Mock prevents actually sending output
    to the testing system. fail_sending can be used to simulate errors during the sending process, maybe caused by
    something broken on the user system. In these cases, the X11 keyboard grab must be released.
    :param fail_sending: Enable failing the send process, in order to verify that the keyboard is released in all cases
    """
    kb = Keyboard(MagicMock())
    if fail_sending:
        kb.mediator.send_string.side_effect = Mock(side_effect=Exception('Mock an error during send_string().'))
        kb.mediator.paste_string.side_effect = Mock(side_effect=Exception('Mock an error during paste_string().'))
    return kb


@pytest.mark.parametrize("key_string, send_mode, expected_exception", [
    # Only string values allowed for key_string
    (12, Keyboard.SendMode.KEYBOARD, TypeError),
    (b"abc", Keyboard.SendMode.KEYBOARD, TypeError),

    ("AB", "ueue", ValueError),  # Unsupported string value for send_mode

    ("123", 42.5, TypeError),
    ("123", len(Keyboard.SendMode), ValueError),  # Index based lookup is supported. Error if out of range
    ("123", -1, ValueError),  # Index based lookup is supported. Error if out of range
])
def test_send_keys_type_checking(key_string, send_mode, expected_exception):
    keyboard = create_keyboard()
    assert_that(calling(keyboard.send_keys).with_args(key_string, send_mode), raises(expected_exception))
    # System state is unaltered
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.begin_send.assert_not_called()
    mock_mediator.send_string.assert_not_called()
    mock_mediator.paste_string.assert_not_called()
    mock_mediator.finish_send.assert_not_called()


@pytest.mark.parametrize("cause_error", [False, True])
def test_send_keys_send_mode_default(cause_error: bool):
    keyboard = create_keyboard(cause_error)
    sent_string = "ABC"
    if cause_error:
        # Verify the test setup and swallow the exception created by the Mock
        assert_that(calling(keyboard.send_keys).with_args(sent_string), raises(Exception))
    else:
        keyboard.send_keys(sent_string)
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.send_string.assert_called_once_with(sent_string)
    mock_mediator.paste_string.assert_not_called()
    mock_mediator.finish_send.assert_called_once()


@pytest.mark.parametrize("cause_error", [False, True])
def test_send_keys_send_mode_keyboard(cause_error: bool):
    keyboard = create_keyboard(cause_error)
    sent_string = "ABC"
    if cause_error:
        # Verify the test setup and swallow the exception created by the Mock
        assert_that(
            calling(keyboard.send_keys).with_args(sent_string, send_mode=keyboard.SendMode.KEYBOARD),
            raises(Exception))
    else:
        keyboard.send_keys(sent_string, send_mode=keyboard.SendMode.KEYBOARD)
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.send_string.assert_called_once_with(sent_string)
    mock_mediator.paste_string.assert_not_called()
    mock_mediator.finish_send.assert_called_once()


@pytest.mark.parametrize("cause_error", [False, True])
def test_send_keys_send_mode_keyboard_index(cause_error: bool):
    keyboard = create_keyboard(cause_error)
    sent_string = "ABC"
    keyboard_index = list(keyboard.SendMode).index(keyboard.SendMode.KEYBOARD)
    if cause_error:
        # Verify the test setup and swallow the exception created by the Mock
        assert_that(
            calling(keyboard.send_keys).with_args(sent_string, send_mode=keyboard_index),
            raises(Exception))
    else:
        keyboard.send_keys(sent_string, send_mode=keyboard_index)
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.send_string.assert_called_once_with(sent_string)
    mock_mediator.paste_string.assert_not_called()
    mock_mediator.finish_send.assert_called_once()


@pytest.mark.parametrize("send_mode, cause_error", itertools.product(
                         itertools.chain(
                             Keyboard.SendMode,
                             range(len(Keyboard.SendMode)),
                             (mode.value for mode in Keyboard.SendMode)),
                         [False, True]))
def test_send_keys_send_mode_clipboard(send_mode: Union[Keyboard.SendMode, int], cause_error: bool):
    kb_mode = Keyboard.SendMode.KEYBOARD
    mode_list = list(Keyboard.SendMode)
    if send_mode is kb_mode \
            or (isinstance(send_mode, int) and send_mode == mode_list.index(kb_mode)) \
            or send_mode == kb_mode.value:
        # Skip keyboard mode for both value- and index-based access
        return
    print(type(send_mode), send_mode)
    keyboard = create_keyboard(cause_error)
    sent_string = "ABC"
    if cause_error:
        # Verify the test setup and swallow the exception created by the Mock
        assert_that(
            calling(keyboard.send_keys).with_args(sent_string, send_mode=send_mode),
            raises(Exception))
    else:
        keyboard.send_keys(sent_string, send_mode=send_mode)
    mock_mediator: MagicMock = keyboard.mediator
    mock_mediator.send_string.assert_not_called()

    if isinstance(send_mode, str):
        send_mode = Keyboard.SendMode(send_mode)
    elif send_mode is None:
        send_mode = Keyboard.SendMode.SELECTION
    elif isinstance(send_mode, int):
        send_mode = mode_list[send_mode]

    mock_mediator.paste_string.assert_called_once_with(sent_string, send_mode)
    mock_mediator.finish_send.assert_called_once()
