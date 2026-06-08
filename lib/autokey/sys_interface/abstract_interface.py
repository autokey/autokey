from abc import ABC, abstractmethod

class AbstractInterface(ABC):
    @abstractmethod
    def send_string(self, string):
        pass

    @abstractmethod
    def send_key(self, key, modifiers=None):
        pass

    @abstractmethod
    def get_window_info(self):
        pass

    @abstractmethod
    def grab(self):
        pass

    @abstractmethod
    def ungrab(self):
        pass

    @abstractmethod
    def cancel(self):
        pass
