import pytest
from autokey.sys_interface.wayland_interface import WaylandInterface

def test_wayland_interface_init():
    class DummyMediator:
        pass
    class DummyApp:
        pass
    interface = WaylandInterface(DummyMediator(), DummyApp())
    assert interface is not None

def test_get_window_info():
    class DummyMediator:
        pass
    class DummyApp:
        pass
    interface = WaylandInterface(DummyMediator(), DummyApp())
    window_class, window_title = interface.get_window_info()
    assert window_class is not None
    assert window_title is not None
