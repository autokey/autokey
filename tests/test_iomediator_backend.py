import os
import pytest
from unittest.mock import patch, MagicMock
from autokey.iomediator.iomediator import IoMediator
from autokey.sys_interface.wayland_interface import WaylandInterface

def test_iomediator_wayland_selection():
    with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'wayland'}):
        service_mock = MagicMock()
        with patch('autokey.configmanager.configmanager.ConfigManager') as mock_config:
            mediator = IoMediator(service_mock)
            assert isinstance(mediator.interface, WaylandInterface)
