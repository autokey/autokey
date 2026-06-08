import pytest
from autokey.sys_interface.abstract_interface import AbstractInterface

class DummyInterface(AbstractInterface):
    pass

def test_abstract_methods():
    with pytest.raises(TypeError):
        DummyInterface() # Should fail because abstract methods are not implemented

    class ImplementedInterface(AbstractInterface):
        def send_string(self, string): pass
        def send_key(self, key, modifiers=None): pass
        def get_window_info(self): pass
        def grab(self): pass
        def ungrab(self): pass
        def cancel(self): pass

    instance = ImplementedInterface()
    assert instance is not None
