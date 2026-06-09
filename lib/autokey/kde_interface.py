#  Copyright (C) 2026 David King  (original implementation in dlk3/autokey-wayland)
#  Copyright (C) 2026 AutoKey contributors
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
KDE Plasma / KWin window interface for AutoKey on Wayland.

Architecture
------------
KWinListener   — a dbus.service.Object that receives JSON pushed by KWin scripts
KWinInterface  — manages script lifecycle (persistent signal scripts + one-shot
                 query scripts) and caches responses
KdeWindowInterface — implements AbstractWindowInterface using KWinInterface

Persistent signal scripts are loaded once at startup.  They subscribe to
``workspace.windowActivated`` so that window metadata is pushed to AutoKey
only when focus actually changes, not on every keystroke.  This avoids the
high-traffic KWin scripting problem identified in PR #1085.

One-shot query scripts (e.g. ``get_window_list``) are loaded on demand,
executed, and immediately unloaded.
"""

from gi.repository import GLib
from pydbus import SessionBus
import glob
import json
import os
import queue
import subprocess
import tempfile
import threading
import time

from autokey.sys_interface.abstract_interface import AbstractWindowInterface, WindowInfo

logger = __import__("autokey.logger").logger.get_logger(__name__)

VERBOSE = False
DBUS_SERVICE_NAME = 'org.autokey.KWinListener'
_SERVICE_PATH = '/' + DBUS_SERVICE_NAME.replace('.', '/')


class KWinListener:
    """D-Bus service that receives JSON responses pushed by KWin scripts.

    The ``dbus`` class attribute is the pydbus introspection XML — not a comment.
    """

    dbus = """
        <node>
            <interface name='org.autokey.KWinListener'>
                <method name='Response'>
                    <arg type='s' name='response' direction='in'/>
                </method>
                <method name='Signal'>
                    <arg type='s' name='response' direction='in'/>
                </method>
                <method name='Shutdown'/>
            </interface>
        </node>
    """

    def __init__(self):
        self.response_queue = queue.Queue()
        self.signal_queue = queue.Queue()

    def Response(self, message):
        self.response_queue.put(message)
        if VERBOSE:
            logger.debug('KWinListener.Response: %s', json.loads(message))
        return True

    def Signal(self, message):
        self.signal_queue.put(message)
        if VERBOSE:
            logger.debug('KWinListener.Signal: %s', json.loads(message))
        return True

    def Shutdown(self):
        return True


class KWinInterface:
    """
    Manages KWin script lifecycle and response caching.

    Persistent signal scripts run once at startup (subscribing to KWin
    window-activation events).  One-shot scripts are run and cleaned up
    immediately after use.
    """

    def __init__(self, timeout: float = 1.0):
        self.timeout = timeout
        self.response_cache: dict = {}
        self.signal_scripts: dict = {}
        self.signal_response_cache: dict = {}
        self._script_fn: str | None = None
        self._service_ready = threading.Event()
        self.listener: KWinListener | None = None
        self.loop = GLib.MainLoop()
        self._dbus_publication = None

        try:
            proc = subprocess.run(
                ['plasmashell', '--version'],
                capture_output=True, text=True, check=True,
            )
            logger.debug('KDE Plasma version = %s', proc.stdout.split()[-1].strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug('Could not determine KDE Plasma version')

        self._cleanup_stale_scripts()

        self.dbus_thread = threading.Thread(
            target=self._run_dbus_service,
            daemon=True,
            name='KWin-DBus-service',
        )
        self.dbus_thread.start()

        if not self._service_ready.wait(timeout=5):
            logger.error('KWinInterface: D-Bus service did not start within 5 s')
            return

        self._preload_signal_scripts()

    # ── D-Bus service thread ───────────────────────────────────────────────

    def _run_dbus_service(self):
        self.listener = KWinListener()
        bus = SessionBus()
        self._dbus_publication = bus.publish(DBUS_SERVICE_NAME, self.listener)
        self._service_ready.set()
        self.loop.run()

    def cancel(self):
        """Stop the D-Bus service and clean up KWin scripts and temp files."""
        self.loop.quit()
        self.dbus_thread.join(timeout=2)
        try:
            bus = SessionBus()
            for script_id in self.signal_scripts.values():
                try:
                    obj = bus.get('org.kde.KWin', f'/Scripting/{script_id}')
                    obj.stop()
                except Exception:
                    pass
        except Exception:
            pass
        self._cleanup_stale_scripts()

    # ── Script utilities ───────────────────────────────────────────────────

    def _cleanup_stale_scripts(self):
        for fn in glob.glob(os.path.join(tempfile.gettempdir(), 'autokey.kwin.script.*.js')):
            try:
                os.unlink(fn)
            except OSError:
                pass

    def _write_temp_script(self, label: str, content: str) -> str:
        fd, fn = tempfile.mkstemp(prefix=f'autokey.kwin.script.{label}.', suffix='.js')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
        except Exception:
            os.close(fd)
            raise
        return fn

    def _load_kwin_script(self, fn: str) -> str:
        bus = SessionBus()
        scripting = bus.get('org.kde.KWin', '/Scripting')
        script_num = int(scripting.loadScript(fn))
        return f'Script{script_num}'

    # ── Persistent signal scripts ──────────────────────────────────────────

    def _preload_signal_scripts(self):
        svc = DBUS_SERVICE_NAME
        path = _SERVICE_PATH

        scripts = {
            'get_active_window': f"""function _ak_send_active(client) {{
    var result = ['get_active_window', [client, workspace.currentDesktop]];
    callDBus("{svc}", "{path}", "{svc}", "Signal", JSON.stringify(result));
}}
var result = ['get_active_window', [workspace.activeWindow, workspace.currentDesktop]];
callDBus("{svc}", "{path}", "{svc}", "Signal", JSON.stringify(result));
workspace.windowActivated.connect(_ak_send_active);""",

            'get_active_desktop_index': f"""function _ak_send_desktop(previous) {{
    var result = ['get_active_desktop_index', workspace.currentDesktop];
    callDBus("{svc}", "{path}", "{svc}", "Signal", JSON.stringify(result));
}}
var result = ['get_active_desktop_index', workspace.currentDesktop];
callDBus("{svc}", "{path}", "{svc}", "Signal", JSON.stringify(result));
workspace.currentDesktopChanged.connect(_ak_send_desktop);""",
        }

        for name, content in scripts.items():
            try:
                fn = self._write_temp_script(name, content)
                script_id = self._load_kwin_script(fn)
                self.signal_scripts[name] = script_id
                bus = SessionBus()
                obj = bus.get('org.kde.KWin', f'/Scripting/{script_id}')
                obj.run()
                logger.debug('KWin signal script loaded: %s -> %s', name, script_id)
            except Exception:
                logger.exception('Failed to load KWin signal script: %s', name)

    # ── Script runner ──────────────────────────────────────────────────────

    def run(self, kwin_script: str, script_name: str | None = None,
            response_expected: bool = False):
        """
        Run a KWin script and optionally wait for its JSON response.

        If *script_name* matches a persistent signal script, drain its queue
        and return the cached value without launching a new script.
        """
        if self.listener is None:
            logger.error('KWinInterface.run() called before service was ready')
            return None

        # Persistent signal script: drain queue, return cache
        if script_name in self.signal_scripts:
            try:
                while True:
                    raw = self.listener.signal_queue.get_nowait()
                    parsed = json.loads(raw)
                    if VERBOSE:
                        logger.debug('Caching signal response: %s', parsed[0])
                    self.signal_response_cache[parsed[0]] = parsed[1]
            except queue.Empty:
                pass
            if script_name in self.signal_response_cache:
                if VERBOSE:
                    logger.debug('Returning cached signal response: %s', script_name)
                return self.signal_response_cache[script_name]
            logger.warning(
                'Signal script %s has no cached response; falling back to one-shot',
                script_name,
            )

        # One-shot script: append callDBus callback then load, run, unload
        if response_expected:
            kwin_script = (
                kwin_script
                + f' callDBus("{DBUS_SERVICE_NAME}", "{_SERVICE_PATH}",'
                f' "{DBUS_SERVICE_NAME}", "Response", result);'
            )

        fn = self._write_temp_script(script_name or 'query', kwin_script)
        script_id = self._load_kwin_script(fn)
        reply = None
        script_iface = None
        try:
            bus = SessionBus()
            script_iface = bus.get('org.kde.KWin', f'/Scripting/{script_id}')
            script_iface.run()

            if response_expected:
                deadline = time.monotonic() + self.timeout
                try:
                    while True:
                        remaining = max(0.001, deadline - time.monotonic())
                        raw = self.listener.response_queue.get(timeout=remaining)
                        parsed = json.loads(raw)
                        if VERBOSE:
                            logger.debug('Caching response: %s', parsed[0])
                        self.response_cache[parsed[0]] = [time.time(), parsed[1]]
                        if parsed[0] == script_name:
                            reply = parsed[1]
                except queue.Empty:
                    if reply is None and script_name in self.response_cache:
                        age = time.time() - self.response_cache[script_name][0]
                        if age < 30:
                            if VERBOSE:
                                logger.debug('Using stale cache for %s (age=%.1fs)', script_name, age)
                            reply = self.response_cache[script_name][1]
                if reply is None:
                    logger.warning('Timed out waiting for KWin script response: %s', script_name)
        finally:
            if script_iface is not None:
                try:
                    script_iface.stop()
                except Exception:
                    pass
            try:
                os.unlink(fn)
            except OSError:
                pass

        return reply


# ── Window interface ───────────────────────────────────────────────────────────

_EMPTY_WINDOW = {
    'wm_class': '', 'wm_class_instance': '', 'wm_title': '',
    'workspace': None, 'desktop': None, 'pid': None, 'id': None,
    'frame_type': None, 'window_type': None,
    'width': None, 'height': None, 'x': None, 'y': None,
    'focus': False, 'in_current_workspace': False,
}


class KdeWindowInterface(AbstractWindowInterface):
    """AbstractWindowInterface implementation for KDE Plasma on Wayland."""

    def __init__(self):
        super().__init__()
        self.kwin = KWinInterface()

    def cancel(self):
        self.kwin.cancel()

    # ── AbstractWindowInterface ────────────────────────────────────────────

    def get_window_info(self, window=None, traverse: bool = True) -> WindowInfo:
        w = self._get_active_window()
        return WindowInfo(wm_title=w['wm_title'], wm_class=w['wm_class'])

    def get_window_title(self, window=None, traverse=True) -> str:
        return self._get_active_window()['wm_title']

    def get_window_class(self, window=None, traverse=True) -> str:
        return self._get_active_window()['wm_class']

    def get_window_list(self) -> list:
        script = (
            'let result = JSON.stringify(["get_window_list",'
            ' [workspace.windowList(), workspace.currentDesktop]]);'
        )
        result = self.kwin.run(script, script_name='get_window_list', response_expected=True)
        if not result:
            return []
        windows, current_desktop = result
        out = []
        for w in windows:
            if w.get('desktopWindow') or not w.get('desktops'):
                continue
            if 'Xwayland Video Bridge' in w.get('caption', ''):
                continue
            in_ws = any(d['id'] == current_desktop['id'] for d in w['desktops'])
            out.append({
                'wm_class': w['resourceClass'],
                'wm_class_instance': w['resourceClass'],
                'wm_title': w['caption'],
                'workspace': w['desktops'][0]['x11DesktopNumber'] - 1,
                'desktop': w['desktops'][0]['id'],
                'pid': w['pid'],
                'id': w['internalId'],
                'frame_type': None,
                'window_type': w['windowType'],
                'width': int(w['width']),
                'height': int(w['height']),
                'x': w['x'],
                'y': w['y'],
                'focus': w['active'],
                'in_current_workspace': in_ws,
            })
        return out

    # ── Internal helpers ───────────────────────────────────────────────────

    def _get_active_window(self) -> dict:
        script = (
            'let result = JSON.stringify(["get_active_window",'
            ' [workspace.activeWindow, workspace.currentDesktop]]);'
        )
        result = self.kwin.run(script, script_name='get_active_window', response_expected=True)
        if not result or not result[0]:
            logger.error('KdeWindowInterface: could not determine active window')
            return dict(_EMPTY_WINDOW)
        w, desktop = result
        desktops = w.get('desktops', [])
        in_ws = any(d['id'] == desktop['id'] for d in desktops)
        return {
            'wm_class': w['resourceClass'],
            'wm_class_instance': w['resourceClass'],
            'wm_title': w['caption'],
            'workspace': (desktops[0]['x11DesktopNumber'] - 1) if desktops else None,
            'desktop': desktops[0]['id'] if desktops else None,
            'pid': w['pid'],
            'id': w['internalId'],
            'frame_type': None,
            'window_type': w['windowType'],
            'width': int(w['width']),
            'height': int(w['height']),
            'x': w['x'],
            'y': w['y'],
            'focus': w['active'],
            'in_current_workspace': in_ws,
        }
