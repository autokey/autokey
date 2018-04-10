import datetime
import time

from .constants import MODIFIERS
from ._iomediator import IoMediator
from .key import Key
from . import _iomediator


class KeyGrabber:
    """
    Keygrabber used by the hotkey settings dialog to grab the key pressed
    """

    def __init__(self, parent):
        self.targetParent = parent

    def start(self):
        # In QT version, sometimes the mouseclick event arrives before we finish initialising
        # sleep slightly to prevent this
        time.sleep(0.1)
        IoMediator.listeners.append(self)
        _iomediator.CURRENT_INTERFACE.grab_keyboard()

    def handle_keypress(self, rawKey, modifiers, key, *args):
        if rawKey not in MODIFIERS:
            IoMediator.listeners.remove(self)
            self.targetParent.set_key(rawKey, modifiers)
            _iomediator.CURRENT_INTERFACE.ungrab_keyboard()

    def handle_mouseclick(self, rootX, rootY, relX, relY, button, windowInfo):
        IoMediator.listeners.remove(self)
        _iomediator.CURRENT_INTERFACE.ungrab_keyboard()
        self.targetParent.cancel_grab()


class Recorder(KeyGrabber):
    """
    Recorder used by the record macro functionality
    """

    def __init__(self, parent):
        KeyGrabber.__init__(self, parent)
        self.insideKeys = False

    def start(self, delay):
        time.sleep(0.1)
        IoMediator.listeners.append(self)
        self.targetParent.start_record()
        self.startTime = time.time()
        self.delay = delay
        self.delayFinished = False

    def start_withgrab(self):
        time.sleep(0.1)
        IoMediator.listeners.append(self)
        self.targetParent.start_record()
        self.startTime = time.time()
        self.delay = 0
        self.delayFinished = True
        _iomediator.CURRENT_INTERFACE.grab_keyboard()

    def stop(self):
        if self in IoMediator.listeners:
            IoMediator.listeners.remove(self)
            if self.insideKeys:
                self.targetParent.end_key_sequence()
            self.insideKeys = False

    def stop_withgrab(self):
        _iomediator.CURRENT_INTERFACE.ungrab_keyboard()
        if self in IoMediator.listeners:
            IoMediator.listeners.remove(self)
            if self.insideKeys:
                self.targetParent.end_key_sequence()
            self.insideKeys = False

    def set_record_keyboard(self, doIt):
        self.recordKeyboard = doIt

    def set_record_mouse(self, doIt):
        self.recordMouse = doIt

    def __delayPassed(self):
        if not self.delayFinished:
            now = time.time()
            delta = datetime.datetime.utcfromtimestamp(now - self.startTime)
            self.delayFinished = (delta.second > self.delay)

        return self.delayFinished

    def handle_keypress(self, rawKey, modifiers, key, *args):
        if self.recordKeyboard and self.__delayPassed():
            if not self.insideKeys:
                self.insideKeys = True
                self.targetParent.start_key_sequence()

            modifierCount = len(modifiers)

            if modifierCount > 1 or (modifierCount == 1 and Key.SHIFT not in modifiers) or \
                    (Key.SHIFT in modifiers and len(rawKey) > 1):
                self.targetParent.append_hotkey(rawKey, modifiers)

            elif key not in MODIFIERS:
                self.targetParent.append_key(key)

    def handle_mouseclick(self, rootX, rootY, relX, relY, button, windowInfo):
        if self.recordMouse and self.__delayPassed():
            if self.insideKeys:
                self.insideKeys = False
                self.targetParent.end_key_sequence()

            self.targetParent.append_mouseclick(relX, relY, button, windowInfo[0])
