# Copyright (C) 2026 AutoKey contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Unit tests for kde_interface and KDE wayland_checks, using mocked D-Bus."""

import json
import os
import queue
import time
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub out dbus and gi.repository.GLib before importing modules under test so
# the tests run without a real D-Bus session or KDE desktop.
# ---------------------------------------------------------------------------
import sys

_dbus_stub = MagicMock()
_dbus_stub.SessionBus = MagicMock
_dbus_stub.service = MagicMock()
_dbus_stub.service.BusName = MagicMock
_dbus_stub.service.Object = object
_dbus_stub.service.method = lambda *a, **kw: (lambda f: f)
_dbus_stub.Interface = MagicMock

_glib_stub = MagicMock()
_glib_stub.MainLoop = MagicMock

# Stub D-Bus / GLib / Qt / autokey internals so tests run without a real DE
for _mod in [
    'dbus', 'dbus.service', 'dbus.mainloop', 'dbus.mainloop.glib',
    'gi', 'gi.repository', 'gi.repository.GLib',
    'PyQt5', 'PyQt5.QtGui', 'PyQt5.QtCore', 'PyQt5.QtWidgets',
    'evdev', 'pyudev',
    'autokey.scripting', 'autokey.scripting.clipboard_qt',
    'autokey.configmanager', 'autokey.configmanager.configmanager',
]:
    sys.modules.setdefault(_mod, MagicMock())

sys.modules['dbus'] = _dbus_stub
sys.modules['dbus.service'] = _dbus_stub.service
sys.modules['gi.repository.GLib'] = _glib_stub

# Patch abstract_interface to avoid the Clipboard import
import types
_abs_mod = types.ModuleType('autokey.sys_interface.abstract_interface')
import typing

WindowInfo = typing.NamedTuple("WindowInfo", [("wm_title", str), ("wm_class", str)])

class AbstractWindowInterface:
    def get_window_info(self, window=None, traverse=True): ...
    def get_window_list(self): ...
    def get_window_title(self, window=None, traverse=True): ...
    def get_window_class(self, window=None, traverse=True): ...

_abs_mod.AbstractWindowInterface = AbstractWindowInterface
_abs_mod.WindowInfo = WindowInfo
_abs_mod.AbstractSysInterface = MagicMock
_abs_mod.AbstractMouseInterface = MagicMock
_abs_mod.queue_method = lambda q: (lambda f: f)
sys.modules['autokey.sys_interface'] = MagicMock()
sys.modules['autokey.sys_interface.abstract_interface'] = _abs_mod

import autokey.kde_interface as kde   # noqa: E402
# Patch WindowInfo/AbstractWindowInterface references inside the loaded module
kde.AbstractWindowInterface = AbstractWindowInterface
kde.WindowInfo = WindowInfo

import autokey.wayland_checks as wc   # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_kwin_interface(signal_data=None, response_data=None, timeout=0.05):
    """Return a KWinInterface with mocked D-Bus and pre-seeded queues."""
    with patch.object(kde.KWinInterface, '_run_dbus_service', lambda self: None), \
         patch.object(kde.KWinInterface, '_preload_signal_scripts', lambda self: None), \
         patch.object(kde.KWinInterface, '_cleanup_stale_scripts', lambda self: None):
        iface = kde.KWinInterface(timeout=timeout)

    iface.listener = MagicMock(spec=kde.KWinListener)
    iface.listener.response_queue = queue.Queue()
    iface.listener.signal_queue = queue.Queue()

    for item in (signal_data or []):
        iface.listener.signal_queue.put(json.dumps(item))
    for item in (response_data or []):
        iface.listener.response_queue.put(json.dumps(item))

    return iface


def _fake_window(title='Konsole', cls='konsole', active=True, **kw):
    return {
        'caption': title,
        'resourceClass': cls,
        'resourceName': cls,
        'active': active,
        'pid': 1234,
        'internalId': 'abc-uuid',
        'windowType': 0,
        'width': 800,
        'height': 600,
        'x': 0,
        'y': 0,
        'desktopWindow': False,
        'desktops': [{'id': 'desk-1', 'x11DesktopNumber': 1}],
        **kw,
    }


def _fake_desktop(desk_id='desk-1'):
    return {'id': desk_id, 'x11DesktopNumber': 1}


# ---------------------------------------------------------------------------
# KWinInterface — signal script caching
# ---------------------------------------------------------------------------

class TestKWinInterfaceSignalCache(unittest.TestCase):

    def test_returns_cached_signal_when_available(self):
        w = _fake_window()
        desk = _fake_desktop()
        iface = _make_kwin_interface(
            signal_data=[['get_active_window', [w, desk]]]
        )
        iface.signal_scripts['get_active_window'] = 'Script1'

        result = iface.run('', script_name='get_active_window', response_expected=False)
        self.assertEqual(result, [w, desk])

    def test_drains_all_queued_signals_returns_latest(self):
        w1 = _fake_window(title='First')
        w2 = _fake_window(title='Second')
        desk = _fake_desktop()
        iface = _make_kwin_interface(
            signal_data=[
                ['get_active_window', [w1, desk]],
                ['get_active_window', [w2, desk]],
            ]
        )
        iface.signal_scripts['get_active_window'] = 'Script1'

        result = iface.run('', script_name='get_active_window', response_expected=False)
        self.assertEqual(result[0]['caption'], 'Second')

    def test_returns_none_when_no_cache_and_timeout(self):
        iface = _make_kwin_interface(timeout=0.001)
        iface.signal_scripts['get_active_window'] = 'Script1'

        with patch.object(iface, '_write_temp_script', return_value='/tmp/fake.js'), \
             patch.object(iface, '_load_kwin_script', return_value='Script99'), \
             patch('dbus.Interface', return_value=MagicMock()):
            result = iface.run('let result=[];', script_name='get_active_window', response_expected=True)
        self.assertIsNone(result)

    def test_service_not_ready_returns_none(self):
        iface = _make_kwin_interface()
        iface.listener = None
        result = iface.run('let result=[];', script_name='any', response_expected=True)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# KWinInterface — one-shot response
# ---------------------------------------------------------------------------

class TestKWinInterfaceOneShot(unittest.TestCase):

    def test_reads_response_queue_for_one_shot_script(self):
        w = _fake_window()
        desk = _fake_desktop()
        iface = _make_kwin_interface(
            response_data=[['get_window_list', [[w], desk]]]
        )

        with patch.object(iface, '_write_temp_script', return_value='/tmp/fake.js'), \
             patch.object(iface, '_load_kwin_script', return_value='Script2'), \
             patch('dbus.Interface', return_value=MagicMock()):
            result = iface.run(
                'let result=[];',
                script_name='get_window_list',
                response_expected=True,
            )
        self.assertEqual(result, [[w], desk])

    def test_uses_stale_cache_on_timeout(self):
        w = _fake_window()
        desk = _fake_desktop()
        iface = _make_kwin_interface(timeout=0.001)
        iface.response_cache['get_window_list'] = [time.time(), [[w], desk]]

        with patch.object(iface, '_write_temp_script', return_value='/tmp/fake.js'), \
             patch.object(iface, '_load_kwin_script', return_value='Script3'), \
             patch('dbus.Interface', return_value=MagicMock()):
            result = iface.run(
                'let result=[];',
                script_name='get_window_list',
                response_expected=True,
            )
        self.assertEqual(result, [[w], desk])


# ---------------------------------------------------------------------------
# KdeWindowInterface
# ---------------------------------------------------------------------------

def _make_window_iface(window=None, desktop=None):
    if window is None:
        window = _fake_window()
    if desktop is None:
        desktop = _fake_desktop()
    kwin = _make_kwin_interface(
        signal_data=[['get_active_window', [window, desktop]]]
    )
    kwin.signal_scripts['get_active_window'] = 'Script1'

    with patch.object(kde.KdeWindowInterface, '__init__', lambda self: None):
        iface = kde.KdeWindowInterface.__new__(kde.KdeWindowInterface)
    iface.kwin = kwin
    return iface


class TestKdeWindowInterface(unittest.TestCase):

    def test_get_window_title(self):
        iface = _make_window_iface(_fake_window(title='Kate'))
        self.assertEqual(iface.get_window_title(), 'Kate')

    def test_get_window_class(self):
        iface = _make_window_iface(_fake_window(cls='kate'))
        self.assertEqual(iface.get_window_class(), 'kate')

    def test_get_window_info_returns_named_tuple(self):
        from autokey.sys_interface.abstract_interface import WindowInfo
        iface = _make_window_iface(_fake_window(title='Dolphin', cls='dolphin'))
        info = iface.get_window_info()
        self.assertIsInstance(info, WindowInfo)
        self.assertEqual(info.wm_title, 'Dolphin')
        self.assertEqual(info.wm_class, 'dolphin')

    def test_get_window_info_empty_when_null_active_window(self):
        from autokey.sys_interface.abstract_interface import WindowInfo
        desk = _fake_desktop()
        kwin = _make_kwin_interface(
            signal_data=[['get_active_window', [None, desk]]]
        )
        kwin.signal_scripts['get_active_window'] = 'Script1'
        with patch.object(kde.KdeWindowInterface, '__init__', lambda self: None):
            iface = kde.KdeWindowInterface.__new__(kde.KdeWindowInterface)
        iface.kwin = kwin
        info = iface.get_window_info()
        self.assertEqual(info.wm_title, '')
        self.assertEqual(info.wm_class, '')

    def test_get_window_list_filters_desktop_windows(self):
        desk = _fake_desktop()
        real_win = _fake_window(title='Konsole', cls='konsole')
        desktop_win = {**_fake_window(title='Desktop', cls='plasmashell'), 'desktopWindow': True}
        kwin = _make_kwin_interface(
            response_data=[['get_window_list', [[real_win, desktop_win], desk]]]
        )
        with patch.object(kde.KdeWindowInterface, '__init__', lambda self: None):
            iface = kde.KdeWindowInterface.__new__(kde.KdeWindowInterface)
        iface.kwin = kwin

        with patch.object(iface.kwin, '_write_temp_script', return_value='/tmp/f.js'), \
             patch.object(iface.kwin, '_load_kwin_script', return_value='Script5'), \
             patch('dbus.Interface', return_value=MagicMock()):
            result = iface.get_window_list()

        titles = [w['wm_title'] for w in result]
        self.assertIn('Konsole', titles)
        self.assertNotIn('Desktop', titles)

    def test_get_window_list_marks_in_current_workspace(self):
        desk = _fake_desktop('desk-42')
        w = _fake_window()
        w['desktops'] = [{'id': 'desk-42', 'x11DesktopNumber': 2}]
        kwin = _make_kwin_interface(
            response_data=[['get_window_list', [[w], desk]]]
        )
        with patch.object(kde.KdeWindowInterface, '__init__', lambda self: None):
            iface = kde.KdeWindowInterface.__new__(kde.KdeWindowInterface)
        iface.kwin = kwin

        with patch.object(iface.kwin, '_write_temp_script', return_value='/tmp/f.js'), \
             patch.object(iface.kwin, '_load_kwin_script', return_value='Script6'), \
             patch('dbus.Interface', return_value=MagicMock()):
            result = iface.get_window_list()
        self.assertTrue(result[0]['in_current_workspace'])

    def test_get_window_list_returns_empty_on_none_result(self):
        kwin = _make_kwin_interface()
        with patch.object(kde.KdeWindowInterface, '__init__', lambda self: None):
            iface = kde.KdeWindowInterface.__new__(kde.KdeWindowInterface)
        iface.kwin = kwin

        with patch.object(iface.kwin, 'run', return_value=None):
            result = iface.get_window_list()
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# wayland_checks — KDE detection helpers
# ---------------------------------------------------------------------------

class TestWaylandChecksKdeDetection(unittest.TestCase):

    def test_is_kde_via_current_desktop(self):
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_DESKTOP': ''}):
            self.assertTrue(wc._is_kde())

    def test_is_kde_via_plasma(self):
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'plasma', 'XDG_SESSION_DESKTOP': ''}):
            self.assertTrue(wc._is_kde())

    def test_is_kde_case_insensitive(self):
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE:GNOME', 'XDG_SESSION_DESKTOP': ''}):
            self.assertTrue(wc._is_kde())

    def test_is_kde_false_on_gnome(self):
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'GNOME', 'XDG_SESSION_DESKTOP': 'gnome'}):
            self.assertFalse(wc._is_kde())

    def test_is_gnome_via_session_desktop(self):
        env = {'XDG_SESSION_DESKTOP': 'gnome'}
        env.pop('GNOME_DESKTOP_SESSION_ID', None)
        with patch.dict(os.environ, env, clear=False):
            self.assertTrue(wc._is_gnome())

    def test_is_gnome_via_env_var(self):
        with patch.dict(os.environ, {'GNOME_DESKTOP_SESSION_ID': '1', 'XDG_SESSION_DESKTOP': ''}):
            self.assertTrue(wc._is_gnome())


class TestWaylandChecksRouting(unittest.TestCase):

    def test_kde_checks_pass_when_uinput_ok(self):
        with patch.object(wc, '_check_uinput_group', return_value=False):
            self.assertTrue(wc._kde_checks())

    def test_kde_checks_fail_when_not_in_input_group(self):
        with patch.object(wc, '_check_uinput_group', return_value=True), \
             patch('subprocess.run', MagicMock()):
            result = wc._kde_checks()
        self.assertFalse(result)

    def test_wayland_checks_routes_to_kde(self):
        env = {
            'XDG_SESSION_TYPE': 'wayland',
            'XDG_CURRENT_DESKTOP': 'KDE',
            'XDG_SESSION_DESKTOP': 'plasma',
        }
        with patch.dict(os.environ, env, clear=True):
            with patch.object(wc, '_kde_checks', return_value=True) as mk, \
                 patch.object(wc, '_gnome_checks', return_value=True) as mg:
                result = wc.waylandChecks()
        mk.assert_called_once()
        mg.assert_not_called()
        self.assertTrue(result)

    def test_wayland_checks_routes_to_gnome(self):
        env = {
            'XDG_SESSION_TYPE': 'wayland',
            'XDG_CURRENT_DESKTOP': 'GNOME',
            'XDG_SESSION_DESKTOP': 'gnome',
        }
        with patch.dict(os.environ, env, clear=True):
            with patch.object(wc, '_gnome_checks', return_value=True) as mg, \
                 patch.object(wc, '_kde_checks', return_value=True) as mk:
                result = wc.waylandChecks()
        mg.assert_called_once()
        mk.assert_not_called()
        self.assertTrue(result)

    def test_wayland_checks_skips_on_x11(self):
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'x11'}):
            self.assertTrue(wc.waylandChecks())

    def test_wayland_checks_shows_popup_for_unsupported_de(self):
        env = {'XDG_SESSION_TYPE': 'wayland', 'XDG_CURRENT_DESKTOP': 'XFCE', 'XDG_SESSION_DESKTOP': 'xfce'}
        with patch.dict(os.environ, env, clear=True):
            with patch('subprocess.run', MagicMock(side_effect=Exception)):
                result = wc.waylandChecks()
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
