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


# Imported to enable threading in Xlib. See module description. Not an unused import statement.
import Xlib.threaded as xlib_threaded
# Delete again, as the reference is not needed anymore after the import side-effect has done it’s work.
# This (hopefully) also prevents automatic code cleanup software from deleting an "unused" import and re-introduce
# issues.
del xlib_threaded

from Xlib.error import ConnectionClosedError


if common.USED_UI_TYPE == "GTK":
    import gi
    gi.require_version('Gtk', '3.0')
    try:
        gi.require_version('Atspi', '2.0')
        import pyatspi
        HAS_ATSPI = True
    except ImportError:
        HAS_ATSPI = False
    except ValueError:
        HAS_ATSPI = False
    except SyntaxError:  # pyatspi 2.26 fails when used with Python 3.7
        HAS_ATSPI = False

logger = __import__("autokey.logger").logger.get_logger(__name__)

def str_or_bytes_to_bytes(x: typing.Union[str, bytes, memoryview]) -> bytes:
    if type(x) == bytes:
        # logger.info("using LiuLang's python3-xlib")
        return x
    if type(x) == str:
        logger.debug("using official python-xlib")
        return x.encode("utf8")
    if type(x) == memoryview:
        logger.debug("using official python-xlib")
        return x.tobytes()
    raise RuntimeError("x must be str or bytes or memoryview object, type(x)={}, repr(x)={}".format(type(x), repr(x)))


# This tuple is used to return requested window properties.
WindowInfo = typing.NamedTuple("WindowInfo", [("wm_title", str), ("wm_class", str)])


class XdoSendInterface(threading.Thread, AbstractSysKeyOutputInterface):

    def __init__(self, mediator, app):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("XdoSendInterface-thread")
        self.doer = xdo.Xdo()
        self.mediator = mediator  # type: IoMediator
        self.app = app
        self.shutdown = False

        self.eventThread = threading.Thread(target=self.__eventLoop)
        self.queue = queue.Queue()

        # Event listener
        self.listenerThread = threading.Thread(target=self.__flush_events_loop)
        self.clipboard = Clipboard()

    def write_delayed(self, text: str, delay: int=12*1000, start_delay:float=1):
        """
        Types text, using inter-key delay delay in μs,
        Wait start_delay seconds before typing to allow switching
        between windows after hitting enter in the interactive prompt.
        """
        time.sleep(start_delay)
        print(f"Send {text}")
        current_window = self.doer.get_focused_window_sane()
        print(f"Current window={current_window}")
        self.doer.enter_text_window(current_window, text.encode("utf-8"), delay=delay)
