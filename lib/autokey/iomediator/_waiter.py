import threading

from ._iomediator import IoMediator


class Waiter:
    """
    Waits for a specified event to occur
    """

    def __init__(self, raw_key, modifiers, button, time_out):
        IoMediator.listeners.append(self)
        self.raw_key = raw_key
        self.modifiers = modifiers
        self.button = button
        self.event = threading.Event()
        self.time_out = time_out

        if modifiers is not None:
            self.modifiers.sort()

    def wait(self):
        return self.event.wait(self.time_out)

    def handle_keypress(self, raw_key, modifiers, key, *args):
        if raw_key == self.raw_key and modifiers == self.modifiers:
            IoMediator.listeners.remove(self)
            self.event.set()

    def handle_mouseclick(self, root_x, root_y, rel_x, rel_y, button, window_info):
        if button == self.button:
            self.event.set()
