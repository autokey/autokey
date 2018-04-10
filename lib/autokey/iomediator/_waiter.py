import threading

from ._iomediator import IoMediator


class Waiter:
    """
    Waits for a specified event to occur
    """

    def __init__(self, rawKey, modifiers, button, timeOut):
        IoMediator.listeners.append(self)
        self.rawKey = rawKey
        self.modifiers = modifiers
        self.button = button
        self.event = threading.Event()
        self.timeOut = timeOut

        if modifiers is not None:
            self.modifiers.sort()

    def wait(self):
        return self.event.wait(self.timeOut)

    def handle_keypress(self, rawKey, modifiers, key, *args):
        if rawKey == self.rawKey and modifiers == self.modifiers:
            IoMediator.listeners.remove(self)
            self.event.set()

    def handle_mouseclick(self, rootX, rootY, relX, relY, button, windowInfo):
        if button == self.button:
            self.event.set()
