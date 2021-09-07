# Copyright (C) 2021 BlueDrink9
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
This file handles interactions with X, mainly sending strings.
"""

import xdo
import time
import typing
import threading
import queue
import subprocess

import autokey.model.phrase
if typing.TYPE_CHECKING:
    from autokey.iomediator.iomediator import IoMediator
import autokey.configmanager.configmanager_constants as cm_constants
from autokey.sys_interface.clipboard import Clipboard
from autokey.sys_interface.abstract_interface import AbstractSysInterface, AbstractMouseInterface, AbstractWindowInterface, AbstractSysKeyOutputInterface

from autokey import common


logger = __import__("autokey.logger").logger.get_logger(__name__)

# This tuple is used to return requested window properties.
WindowInfo = typing.NamedTuple("WindowInfo", [("wm_title", str), ("wm_class", str)])

class XdoSendInterface(AbstractSysKeyOutputInterface):
# class XdoSendInterface(threading.Thread, AbstractSysKeyOutputInterface):

    def __init__(self, mediator, app):
        # threading.Thread.__init__(self)
        # self.setDaemon(True)
        # self.setName("XdoSendInterface-thread")
        self.doer = xdo.Xdo()
        self.mediator = mediator  # type: IoMediator
        self.app = app
        # Uses XQueryKeymap
        # self.doer.get_active_keys_to_keycode_list()

    def send_string(self, string, delay: int=5*1000):
        """
        Types text, using inter-key delay `delay` in μs,
        Wait start_delay seconds before typing to allow switching
        between windows after hitting enter in the interactive prompt.
        """
        current_window = self.doer.get_focused_window_sane()
        self.__pause_autokey()
        self.doer.enter_text_window(current_window, string.encode("utf-8"), delay=delay)

    def send_key(self, key_name, delay: int=2*1000):
        """
        This allows you to send keysequences by symbol name. Any combination of
        X11 KeySym names separated by ‘+’ are valid. Single KeySym names are
        valid, too.

        Examples:
        “l” “semicolon” “alt+Return” “Alt_L+Tab”
        """
        current_window = self.doer.get_focused_window_sane()
        self.__pause_autokey()
        key = self.__convert_key_name_autokey_to_xdo(key_name)
        self.doer.send_keysequence_window(current_window, key, delay=delay)

    def send_modified_key(self, key_name, delay: int=2*1000):
        self.send_key(key_name, delay)

    def press_key(self, key_name, delay: int=5*1000):
        self.__press_or_release_key(key_name, delay, press=True)
    def release_key(self, key_name, delay: int=5*1000):
        self.__press_or_release_key(key_name, delay, press=False)

    def fake_keypress(self, key_name):
        pass
    def fake_keydown(self, key_name):
        pass
    def fake_keyup(self, key_name):
        pass

    def __press_or_release_key(self, key_name, delay: int=5*1000, press=True):
        current_window = self.doer.get_focused_window_sane()
        self.__pause_autokey()
        key = self.__convert_key_name_autokey_to_xdo(key_name)
        if press:
            self.doer.send_keysequence_window_down(current_window, key, delay=delay)
        else:
            self.doer.send_keysequence_window_up(current_window, key, delay=delay)

    def __convert_key_name_autokey_to_xdo(self, key_name):
        """
        At this stage, we rely on the assumption that all keys are sent as valid X11 KeySyms, only the modifiers are surrounded by <>
        """
        key_name =key_name.replace("<", "")
        key_name =key_name.replace(">", "")
        return key_name


    def __pause_autokey(self):
        """
        Xdo works at a higher level than the rest of the xrecord interface that autokey uses.
        This causes a couple of problems. It means that if xrecord has grabbed the keyboard to prevent input, xdo cannot input anything.
        It also means that xdo key events are seen by autokey as user key events.
        To avoid that, we ungrab the keyboard and pause responding to keyboard events while using xdo commands.
        """
        self.app.pause_service()
        self.mediator.finish_send()
        yield
        self.mediator.begin_send()
        self.app.unpause_service()

