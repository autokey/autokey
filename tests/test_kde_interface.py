# Copyright (C) 2026 AutoKey contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Unit tests for kde_interface.py and the KDE branch of wayland_checks.py.

pydbus and gi.repository.GLib are stubbed out so these tests run without a
real D-Bus session or a KDE desktop present.
"""

import json
import os
import queue
import sys
import time
import types
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub pydbus / GLib before importing the module under test.
# ---------------------------------------------------------------------------
_pydbus_stub = types.ModuleType('pydbus')
_pydbus_stub.SessionBus = MagicMock
sys.modules.setdefault('pydbus', _pydbus_stub)

_glib_module = types.ModuleType('gi.repository.GLib')
_glib_module.MainLoop = MagicMock
_gi_repository_stub = sys.modules.get('gi.repository')
if _gi_repository_stub is None:
    _gi_repository_stub = types.ModuleType('gi.repository')
    sys.modules.setdefault('gi', types.ModuleType('gi'))
    sys.modules['gi.repository'] = _gi_repository_stub
_gi_repository_stub.GLib = _glib_module
sys.modules.setdefault('gi.repository.GLib', _glib_module)

import autokey.kde_interface as kde  # noqa: E402
import autokey.wayland_checks as wc  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_kwin_interface(signal_data=None, response_data=None, timeout=0.05):
    """Build a KWinInterface with the D-Bus service/preload steps stubbed out
    and its listener queues pre-seeded, so run() can be exercised directly."""
    with patch.object(kde.subprocess, 'run', return_value=MagicMock(stdout=b'plasmashell 5.27.0\n')), \
         patch.object(kde.KWinInterface, '_dbus_service', lambda self: None), \
         patch.object(kde.KWinInterface, '_preload_signal_scripts', lambda self: None):
        iface = kde.KWinInterface(timeout=timeout)

    iface.listener = MagicMock()
    iface.listener.response_queue = queue.Queue()
    iface.listener.signal_queue = queue.Queue()

    for item in (signal_data or []):
        iface.listener.signal_queue.put(json.dumps(item))
    for item in (response_data or []):
        iface.listener.response_queue.put(json.dumps(item))

    return iface


def _make_window_interface(kwin):
    with patch.object(kde.KdeWindowInterface, '__init__', lambda self: None):
        iface = kde.KdeWindowInterface.__new__(kde.KdeWindowInterface)
    iface.kwin = kwin
    return iface


def _fake_window(title='Konsole', cls='konsole', active=True, **kw):
    return {
        'caption': title,
        'resourceClass': cls,
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
# KWinInterface - persistent signal-script cache (the hot path)
# ---------------------------------------------------------------------------

class TestKWinInterfaceSignalCache(unittest.TestCase):

    def test_returns_cached_signal_when_available(self):
        w = _fake_window()
        desk = _fake_desktop()
        iface = _make_kwin_interface(signal_data=[['get_active_window', [w, desk]]])
        iface.signal_scripts['get_active_window'] = 'Script1'

        result = iface.run('', script_name='get_active_window', response_expected=False)
        self.assertEqual(result, [w, desk])

    def test_drains_all_queued_signals_returns_latest(self):
        w1 = _fake_window(title='First')
        w2 = _fake_window(title='Second')
        desk = _fake_desktop()
        iface = _make_kwin_interface(signal_data=[
            ['get_active_window', [w1, desk]],
            ['get_active_window', [w2, desk]],
        ])
        iface.signal_scripts['get_active_window'] = 'Script1'

        result = iface.run('', script_name='get_active_window', response_expected=False)
        self.assertEqual(result[0]['caption'], 'Second')

    def test_falls_back_to_running_script_when_no_cache_yet(self):
        # Not a signal script at all -> always falls through to _load_script/run.
        iface = _make_kwin_interface()
        result = iface.run(
            'let result = JSON.stringify(["thing", null]);',
            script_name='thing',
            response_expected=False,
        )
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# KWinInterface - one-shot query scripts
# ---------------------------------------------------------------------------

class TestKWinInterfaceOneShot(unittest.TestCase):

    def test_reads_response_queue_for_one_shot_script(self):
        w = _fake_window()
        desk = _fake_desktop()
        iface = _make_kwin_interface(response_data=[['get_window_list', [[w], desk]]])

        result = iface.run(
            'let result = JSON.stringify(["get_window_list", []]);',
            script_name='get_window_list',
            response_expected=True,
        )
        self.assertEqual(result, [[w], desk])

    def test_uses_stale_cache_on_timeout(self):
        w = _fake_window()
        desk = _fake_desktop()
        iface = _make_kwin_interface(timeout=0.01)
        iface.response_cache['get_window_list'] = [time.time(), [[w], desk]]

        result = iface.run(
            'let result = JSON.stringify(["get_window_list", []]);',
            script_name='get_window_list',
            response_expected=True,
        )
        self.assertEqual(result, [[w], desk])

    def test_returns_none_on_timeout_with_no_cache(self):
        iface = _make_kwin_interface(timeout=0.01)

        result = iface.run(
            'let result = JSON.stringify(["get_window_list", []]);',
            script_name='get_window_list',
            response_expected=True,
        )
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# KdeWindowInterface
# ---------------------------------------------------------------------------

class TestKdeWindowInterface(unittest.TestCase):

    def test_get_window_title(self):
        w = _fake_window(title='Kate')
        desk = _fake_desktop()
        kwin = _make_kwin_interface(response_data=[['get_active_window', [w, desk]]])
        iface = _make_window_interface(kwin)

        self.assertEqual(iface.get_window_title(), 'Kate')

    def test_get_window_class(self):
        w = _fake_window(cls='kate')
        desk = _fake_desktop()
        kwin = _make_kwin_interface(response_data=[['get_active_window', [w, desk]]])
        iface = _make_window_interface(kwin)

        self.assertEqual(iface.get_window_class(), 'kate')

    def test_get_window_info_returns_named_tuple(self):
        w = _fake_window(title='Dolphin', cls='dolphin')
        desk = _fake_desktop()
        kwin = _make_kwin_interface(response_data=[['get_active_window', [w, desk]]])
        iface = _make_window_interface(kwin)

        info = iface.get_window_info()
        self.assertIsInstance(info, kde.WindowInfo)
        self.assertEqual(info.wm_title, 'Dolphin')
        self.assertEqual(info.wm_class, 'dolphin')

    def test_get_window_info_returns_empty_strings_when_no_active_window(self):
        # get_active_window() always returns a dict (never falsy), so
        # get_window_info()'s 'unknown' fallback is unreachable in practice;
        # this documents the actual observed behavior.
        kwin = _make_kwin_interface(response_data=[['get_active_window', [None, None]]])
        iface = _make_window_interface(kwin)

        info = iface.get_window_info()
        self.assertEqual(info.wm_title, '')
        self.assertEqual(info.wm_class, '')

    def test_get_window_list_filters_desktop_windows(self):
        desk = _fake_desktop()
        real_win = _fake_window(title='Konsole', cls='konsole')
        desktop_win = {**_fake_window(title='Desktop', cls='plasmashell'), 'desktopWindow': True}
        kwin = _make_kwin_interface(response_data=[['get_window_list', [[real_win, desktop_win], desk]]])
        iface = _make_window_interface(kwin)

        result = iface.get_window_list()

        titles = [w['wm_title'] for w in result]
        self.assertIn('Konsole', titles)
        self.assertNotIn('Desktop', titles)

    def test_get_window_list_excludes_xwayland_video_bridge(self):
        desk = _fake_desktop()
        real_win = _fake_window(title='Konsole', cls='konsole')
        bridge_win = _fake_window(title='Xwayland Video Bridge', cls='xwaylandvideobridge')
        kwin = _make_kwin_interface(response_data=[['get_window_list', [[real_win, bridge_win], desk]]])
        iface = _make_window_interface(kwin)

        result = iface.get_window_list()

        titles = [w['wm_title'] for w in result]
        self.assertIn('Konsole', titles)
        self.assertNotIn('Xwayland Video Bridge', titles)

    def test_get_window_list_marks_in_current_workspace(self):
        desk = _fake_desktop('desk-42')
        w = _fake_window()
        w['desktops'] = [{'id': 'desk-42', 'x11DesktopNumber': 2}]
        kwin = _make_kwin_interface(response_data=[['get_window_list', [[w], desk]]])
        iface = _make_window_interface(kwin)

        result = iface.get_window_list()
        self.assertTrue(result[0]['in_current_workspace'])

    def test_get_window_list_returns_empty_on_no_result(self):
        kwin = _make_kwin_interface(timeout=0.01)
        iface = _make_window_interface(kwin)

        result = iface.get_window_list()
        self.assertEqual(result, [])

    def test_get_properties_returns_none_when_window_not_found(self):
        # Regression check: KWin script replies [null, null] when the
        # window_id doesn't match any window; get_properties() must not
        # raise trying to subscript None.
        kwin = _make_kwin_interface(response_data=[['get_properties', [None, None]]])
        iface = _make_window_interface(kwin)

        self.assertIsNone(iface.get_properties('nonexistent-id'))

    def test_get_properties_reads_maximized_flags(self):
        window = {'keepAbove': False, 'fullScreen': False, 'hidden': False,
                  'height': 600, 'width': 800, 'shade': False,
                  'skipPager': False, 'skipTaskbar': False}
        screen = {'height': 600, 'width': 1024}
        kwin = _make_kwin_interface(response_data=[['get_properties', [window, screen]]])
        iface = _make_window_interface(kwin)

        props = iface.get_properties('some-id')
        self.assertTrue(props['is_maximized_vert'])
        self.assertFalse(props['is_maximized_horz'])


# ---------------------------------------------------------------------------
# KdeMouseInterface
# ---------------------------------------------------------------------------

class TestKdeMouseInterface(unittest.TestCase):

    def test_mouse_location_reads_kwin_cursor_pos(self):
        mouse = kde.KdeMouseInterface()
        mouse.mediator = MagicMock()
        mouse.mediator.windowInterface.kwin.run.return_value = {'x': 12, 'y': 34}

        self.assertEqual(mouse.mouse_location(), [12, 34])

    def test_mouse_location_returns_none_without_reply(self):
        mouse = kde.KdeMouseInterface()
        mouse.mediator = MagicMock()
        mouse.mediator.windowInterface.kwin.run.return_value = None

        self.assertIsNone(mouse.mouse_location())


# ---------------------------------------------------------------------------
# wayland_checks - KDE detection and routing
# ---------------------------------------------------------------------------

class TestWaylandChecksKdeDetection(unittest.TestCase):

    def test_is_kde_via_current_desktop(self):
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE', 'XDG_SESSION_DESKTOP': ''}):
            self.assertTrue(wc._is_kde())

    def test_is_kde_via_plasma(self):
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'plasma', 'XDG_SESSION_DESKTOP': ''}):
            self.assertTrue(wc._is_kde())

    def test_is_kde_handles_colon_separated_list(self):
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'KDE:GNOME', 'XDG_SESSION_DESKTOP': ''}):
            self.assertTrue(wc._is_kde())

    def test_is_kde_false_on_gnome(self):
        with patch.dict(os.environ, {'XDG_CURRENT_DESKTOP': 'GNOME', 'XDG_SESSION_DESKTOP': 'gnome'}):
            self.assertFalse(wc._is_kde())

    def test_is_gnome_via_session_desktop(self):
        with patch.dict(os.environ, {'XDG_SESSION_DESKTOP': 'gnome'}):
            self.assertTrue(wc._is_gnome())


class TestWaylandChecksRoutesToKde(unittest.TestCase):

    def test_skips_gnome_extension_check_on_kde(self):
        env = {
            'XDG_SESSION_TYPE': 'wayland',
            'XDG_CURRENT_DESKTOP': 'KDE',
            'XDG_SESSION_DESKTOP': 'plasma',
        }
        with patch.dict(os.environ, env, clear=True), \
             patch.object(wc, 'subprocess') as mock_subprocess, \
             patch.object(wc, 'getpass'), \
             patch.object(wc.grp, 'getgrnam', side_effect=KeyError('input')), \
             patch.object(wc, '__show_popup', create=True):
            wc.waylandChecks()

        mock_subprocess.run.assert_not_called()

    def test_kde_message_omits_gnome_extension_install_line(self):
        env = {
            'XDG_SESSION_TYPE': 'wayland',
            'XDG_CURRENT_DESKTOP': 'KDE',
            'XDG_SESSION_DESKTOP': 'plasma',
        }
        messages = []
        with patch.dict(os.environ, env, clear=True), \
             patch.object(wc.grp, 'getgrnam', side_effect=KeyError('input')), \
             patch.object(
                 wc, '__show_popup',
                 lambda title, message: messages.append(message),
             ):
            result = wc.waylandChecks()

        self.assertFalse(result)
        self.assertTrue(messages)
        self.assertNotIn('gnome-extensions install', messages[0])


if __name__ == '__main__':
    unittest.main()
