#  Copyright (C) 2026 David King
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
#
#####################################################################

from gi.repository import GLib
from pydbus import SessionBus
import json
import os
import subprocess
import tempfile
import time
import threading
import glob
import queue

from autokey.sys_interface.abstract_interface import AbstractSysInterface, AbstractWindowInterface, WindowInfo, queue_method

logger = __import__("autokey.logger").logger.get_logger(__name__)

#  Toggle extra debug log messages useful for tracing
VERBOSE=False

#  The name of the KWinListener DBus service.
DBUS_SERVICE_NAME='org.autokey.KWinListener'

#  The definition for a DBus service that listens for a message from a
#  KWin script.
#
#  The XML in the docstring in this class is NOT a comment, it is the
#  DBus introspection detail that pydbus uses when it publishes this
#  service.
class KWinListener(object):
    """
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
            logger.debug(f'KWinListener queued a Response message:\n{json.loads(message)}')
        return True

    def Signal(self, message):
        self.signal_queue.put(message)
        if VERBOSE:
            logger.debug(f'KWinListener queued a Signal message:\n{json.loads(message)}')
        return True

    def Shutdown(self):
        self.signal_queue.shutdown()
        self.response_queue.shutdown()
        loop.quit()
        return True

class KWinInterface():

    def __init__(self, timeout=1):
        self.timeout = timeout
        self.response_cache = {}
        self.signal_scripts = {}
        self.signal_response_cache = {}

        #  Write KDE version to debug log
        try:
            proc = subprocess.run(['plasmashell', '--version'], capture_output=True, check=True)
            kde_version = proc.stdout.decode('utf-8').split(' ')[1].strip()
            logger.debug(f'KDE Plasma version = {kde_version}')
        except subprocess.CalledProcessError:
            logger.exception('KDE Plasma version check failed')

        #  Start the DBus service thread
        self.loop = GLib.MainLoop()
        self.dbus_thread = threading.Thread(target=self._dbus_service)
        self.dbus_thread.start()

        #  Delete any old script files from the tmp directory
        fn_spec = os.path.join(tempfile.gettempdir(), 'autokey.kwin.script.*.js')
        for fn in glob.glob(fn_spec):
            os.unlink(fn)

        #  Preload the KWin signal scripts
        self._preload_signal_scripts()

    #  Method that runs the DBus service in a seperate thread
    def _dbus_service(self):
        self.listener = KWinListener()
        bus = SessionBus()
        dbus_service = bus.publish(DBUS_SERVICE_NAME, self.listener)
        self.loop.run()

    #  Method to sutdown the DBus service thread and clean up KWin
    #  scripts and their temp files
    def cancel(self):
        self.loop.quit()
        self.dbus_thread.join()

        #  Shut down the signal scripts
        bus = SessionBus()
        for script_name, script_id in self.signal_scripts.items():
            obj = bus.get('org.kde.KWin', f'/Scripting/{script_id}')
            obj.stop()

        #  Erase the temporary script files
        fn_spec = os.path.join(tempfile.gettempdir(), 'autokey.kwin.script.*.js')
        for fn in glob.glob(fn_spec):
            os.unlink(fn)

    #  Method that loads a kwin_script into KWin.  Called by run() below.
    def _load_script(self, kwin_script, response_expected=False):
        if response_expected:
            service_path = '/' + DBUS_SERVICE_NAME.replace('.','/')
            kwin_script = kwin_script + f' callDBus("{DBUS_SERVICE_NAME}", "{service_path}", "{DBUS_SERVICE_NAME}", "Response", result);'

        bus = SessionBus()
        obj = bus.get('org.kde.KWin', '/Scripting')

        #  Save the KWin script in a temporary file
        (f, self.script_fn) = tempfile.mkstemp(prefix='autokey.kwin.script.', suffix='.js')
        with open(self.script_fn, 'w') as script_file:
            script_file.write(kwin_script)

        #  Load the script file into KWin
        return 'Script' + str(obj.loadScript(self.script_fn))

    #  Method that loads the KWin signal scripts.  Called by __init__()
    #  above.
    def _preload_signal_scripts(self):
        service_path = '/' + DBUS_SERVICE_NAME.replace('.','/')
        self.signal_scripts = {
            'get_active_window': """function send_active_window(client) {
    result = ['get_active_window', [client, workspace.currentDesktop]];
    callDBus("<service_name>", "<service_path>", "<service_name>", "Signal", JSON.stringify(result));
}
result = ['get_active_window', [workspace.activeWindow, workspace.currentDesktop]];
callDBus("<service_name>", "<service_path>", "<service_name>", "Signal", JSON.stringify(result));
workspace.windowActivated.connect(send_active_window);""".replace('<service_name>', DBUS_SERVICE_NAME).replace('<service_path>', service_path),

            'get_active_desktop_index': """function send_active_window(previous_desktop) {
    result = ['get_active_desktop_index', workspace.currentDesktop];
    callDBus("<service_name>", "<service_path>", "<service_name>", "Signal", JSON.stringify(result));
}
result = ['get_active_desktop_index', workspace.currentDesktop];
callDBus("<service_name>", "<service_path>", "<service_name>", "Signal", JSON.stringify(result));
workspace.currentDesktopChanged.connect(send_active_window);""".replace('<service_name>', DBUS_SERVICE_NAME).replace('<service_path>', service_path)
        }
        bus = SessionBus()
        for script_name, kwin_script in self.signal_scripts.items():
            #  Save the KWin script in a temporary file
            (f, fn) = tempfile.mkstemp(prefix=f'autokey.kwin.script.{script_name}.', suffix='.js')
            with open(fn, 'w') as script_file:
                script_file.write(kwin_script)

            #  Load the script file into KWin
            obj = bus.get('org.kde.KWin', '/Scripting')
            script_id = 'Script' + str(obj.loadScript(fn))

            #  Save the script id for later reference
            self.signal_scripts[script_name] = script_id

            #  Start the script
            obj = bus.get('org.kde.KWin', f'/Scripting/{script_id}')
            obj.run()

    #  Method that runs a kwin_script
    def run(self, kwin_script, script_name=None, response_expected=False):
        #  If this is a KWin signal script, then it should have a cached
        #  response.  Return that.
        if script_name in self.signal_scripts:
            #  Process the contents of the signal queue into the signal
            #  response cache
            try:
                while True:
                    response = json.loads(self.listener.signal_queue.get(block=False))
                    if VERBOSE:
                        logger.debug('Caching a response from the signal_queue for ' + response[0])
                    self.signal_response_cache[response[0]] = response[1]
            except queue.Empty:
                #  Once the queue has been emptied, return the cached
                #  response.
                if script_name in self.signal_response_cache:
                    if VERBOSE:
                        logger.debug(f'Returning a cached response for {script_name}')
                    return self.signal_response_cache[script_name]
            logger.warning(f'The {script_name} KWin script should have a cached response and it does not, AutoKey will run the KWin script.')

        #  Otherwise, run the script ...
        script_id = self._load_script(kwin_script, response_expected=response_expected)
        bus = SessionBus()
        obj = bus.get('org.kde.KWin', f'/Scripting/{script_id}')
        obj.run()

        #  Read contents of queue, cache what we read, and return a live
        #  result for the script that called us, or a cached result if
        #  we timed out waiting for a reply to appear on the queue.
        #  Timeout value is set when KWinInterface is instantiated.
        reply = None
        if response_expected:
            try:
                one_time_timeout = self.timeout
                while True:
                    item = json.loads(self.listener.response_queue.get(timeout=one_time_timeout))
                    one_time_timeout = 0
                    if VERBOSE:
                        logger.debug('Caching a response from the response_queue for ' + item[0])
                    #  Put a timestamp at the front of the result so we
                    #  can tell how old it is.
                    self.response_cache[item[0]] = [time.time(), item[1]]
                    if item[0] == script_name:
                        reply = item[1]
            except queue.Empty:
                if not reply:
                    #  If this script is in the cache
                    if script_name in self.response_cache:
                        #  and it's result isn't too old
                        if time.time() - self.response_cache[script_name][0] < 30:
                            if VERBOSE:
                                logger.debug(f'Returning a cached response for {script_name}')
                            reply = self.response_cache[script_name][1]
            if not reply:
                logger.warning(f'Timed out waiting for a response from the {script_name} KWin script and there is no recent cached result to reply with.  Returning "None"')

        #  Remove the script from Kwin
        obj.stop()
        os.unlink(self.script_fn)

        return reply

class KdeMouseInterface():
    def __init__(self):
        super().__init__()

    def mouse_location(self):
        """
        Returns the x/y coordinates of the mouse pointer

        :return: [x, y]
        :rtype: list
        """
        kwin_script = 'let result = JSON.stringify(["mouse_location", workspace.cursorPos]);'
        result = self.mediator.windowInterface.kwin.run(kwin_script, script_name='mouse_location', response_expected=True)
        if result:
            return [result['x'], result['y']]

class KdeWindowInterface(AbstractWindowInterface):
    def __init__(self):
        super().__init__()
        self.kwin = KWinInterface()

    def cancel(self):
        self.kwin.cancel()

    def get_window_info(self, window=None, traverse: bool=True) -> WindowInfo:
        """
        Ask KWin for title and class of the currently focused window.

        :return: (wm_title, wm_class)
        :rtype: WindowInfo
        """
        result = self.get_active_window()
        if result:
            return WindowInfo(wm_title=result['wm_title'], wm_class=result['wm_class'])
        else:
            return WindowInfo(wm_title='unknown', wm_class='unknown')

    def get_window_list(self):
        """
        Ask KWin for a list of all the windows on the desktop

        :return: An array containing information about each window
        :rtype: list of dictionaries
        """
        kwin_script = 'let result = JSON.stringify(["get_window_list", [workspace.windowList(), workspace.currentDesktop]]);'
        result = self.kwin.run(kwin_script, script_name='get_window_list', response_expected=True)
        window_list = []
        if result:
            for window in result[0]:
                if not window['desktopWindow'] and len(window['desktops']) > 0 and 'Xwayland Video Bridge' not in window['caption']:
                    in_current_workspace = False
                    for desktop in window['desktops']:
                        if desktop['id'] == result[1]['id']:
                            in_current_workspace = True
                            break
                    window_list.append({
                        'wm_class': window['resourceClass'],
                        'wm_class_instance': window['resourceClass'],
                        'wm_title': window['caption'],
                        'workspace': window['desktops'][0]['x11DesktopNumber'] - 1,
                        'desktop': window['desktops'][0]['id'],
                        'pid': window['pid'],
                        'id': window['internalId'],
                        'frame_type': None,
                        'window_type': window['windowType'],
                        'width': int(window['width']),
                        'height': int(window['height']),
                        'x': window['x'],
                        'y': window['y'],
                        'focus': window['active'],
                        'in_current_workspace': in_current_workspace
                    })
        return window_list

    def get_window_title(self, window=None, traverse=True) -> str:
        """
        Returns the window title of the currently focused window.

        :return: window title
        :rtype: string
        """
        result = self.get_active_window()
        if result:
            return result['wm_title']

    def get_window_class(self, window=None, traverse=True) -> str:
        """
        Returns the window class of the currently focused window.

        :return: window class
        :rtype: string
        """
        result = self.get_active_window()
        if result:
            return result['wm_class']

    def get_screen_size(self):
        """
        Returns the width and height of the display

        :return: [width, height]
        :rtype: list
        """
        kwin_script = 'let result = JSON.stringify(["get_screen_size", workspace.activeScreen.geometry]);'
        result = self.kwin.run(kwin_script, script_name='get_screen_size', response_expected=True)
        if result:
           return [result['width'], result['height']]

    ####################################################################
    #  The following methods support the window API
    ####################################################################

    def get_active_window(self):
        """
        Ask KWin for the details for the currently focused window

        :return: A dictionary containing information a window
        :rtype: dictionary
        """
        kwin_script = 'let result = JSON.stringify(["get_active_window", [workspace.activeWindow, workspace.currentDesktop]]);'
        result = self.kwin.run(kwin_script, script_name='get_active_window', response_expected=True)
        if result and result[0]:
            window = result[0]
            in_current_workspace = False
            for desktop in window['desktops']:
                if desktop['id'] == result[1]['id']:
                    in_current_workspace = True
                    break
            active_window = {
                'wm_class': window['resourceClass'],
                'wm_class_instance': window['resourceClass'],
                'wm_title': window['caption'],
                'workspace': window['desktops'][0]['x11DesktopNumber'] - 1,
                'desktop': window['desktops'][0]['id'],
                'pid': window['pid'],
                'id': window['internalId'],
                'frame_type': None,
                'window_type': window['windowType'],
                'width': int(window['width']),
                'height': int(window['height']),
                'x': window['x'],
                'y': window['y'],
                'focus': window['active'],
                'in_current_workspace': in_current_workspace
            }
        else:
            logger.error(f"Unable to determine the active window.")
            active_window = {
                'wm_class': '',
                'wm_class_instance': '',
                'wm_title': '',
                'workspace': None,
                'desktop': None,
                'pid': None,
                'id': None,
                'frame_type': None,
                'window_type': None,
                'width': None,
                'height': None,
                'x': None,
                'y': None,
                'focus': False,
                'in_current_workspace': False
            }
        return active_window

    def get_active_desktop_index(self):
        kwin_script = 'let result = JSON.stringify(["get_active_window", workspace.currentDesktop]);'
        result = self.kwin.run(kwin_script, script_name='get_active_desktop_index', response_expected=True)
        if result:
           return result['x11DesktopNumber'] - 1

    def close_window(self, window_id):
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    w.closeWindow();
}""".replace('<window_id>', window_id)
        self.kwin.run(kwin_script)

    def activate_window(self, window_id):
        if not window_id:
            logger.error('valid window_id not provided for activate_window()')
            return
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    workspace.activeWindow = w;
}""".replace('<window_id>', window_id)
        self.kwin.run(kwin_script)

    def move_resize_window(self, window_id, x, y , width, height):
        if not window_id:
            logger.error('valid window_id not provided for move_resize_window()')
            return
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    let obj = Object.assign({}, w.frameGeometry);
    obj.x = <x>;
    obj.y = <y>;
    obj.width = <width>;
    obj.height = <height>;
    w.frameGeometry = obj;
}""".replace('<window_id>', window_id)
        kwin_script = kwin_script.replace('<x>', str(x))
        kwin_script = kwin_script.replace('<y>', str(y))
        kwin_script = kwin_script.replace('<width>', str(width))
        kwin_script = kwin_script.replace('<height>', str(height))
        self.kwin.run(kwin_script)

    def move_to_workspace(self, window_id, workspace_number):
        if not window_id:
            logger.error('invalid window_id specified for move_to_workspace()')
            return
        try:
            workspace_number = int(workspace_number)
        except:
            logger.error(f'invalid workspace_number specified for move_to_workspace(): "{workspace_number}"')
            return
        kwin_script = """let d = workspace.desktops.find((d) => d.x11DesktopNumber == <workspace_number>);
if (d) {
    const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
    if (w) {
        w.desktops = [d];
    }
}""".replace('<window_id>', window_id)
        kwin_script = kwin_script.replace('<workspace_number>', str(workspace_number + 1))
        self.kwin.run(kwin_script)

    def switch_workspace(self, workspace_number):
        try:
            workspace_number = int(workspace_number)
        except:
            logger.error(f'invalid workspace_number specified for switch_workspace(): "{workspace_number}"')
            return
        kwin_script = """let d = workspace.desktops.find((d) => d.x11DesktopNumber == <workspace_number>);
if (d) {
    workspace.currentDesktop = d;
}""".replace('<workspace_number>', str(workspace_number + 1))
        self.kwin.run(kwin_script)

    def get_properties(self, window_id):
        if not window_id:
            logger.error('valid window_id not provided for get_properties()')
            return
        kwin_script = """let w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    let s = workspace.clientArea(KWin.MaximizeArea, w);
    result = JSON.stringify(['get_properties', [w, s]]);
} else {
    result = JSON.stringify(['get_properties', [null, null]]);
}""".replace('<window_id>', window_id)
        result = self.kwin.run(kwin_script, script_name='get_properties', response_expected=True)
        if result:
            (window, screen) = result
            return {
                'is_above': window['keepAbove'],
                'is_fullscreen': window['fullScreen'],
                'is_hidden': window['hidden'],
                'is_maximized_vert': (window['height'] == screen['height']),
                'is_maximized_horz': (window['width'] == screen['width']),
                'is_shaded': window['shade'],
                'is_skip_pager': window['skipPager'],
                'is_skip_taskbar': window['skipTaskbar']
            }
        else:
            return

    def set_properties(window_id, prop, value):
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    w.<property> = <value>;
}""".replace('<window_id>', window_id);
        kwin_script = kwin_script.replace('<property>', prop)
        kwin_script = kwin_script.replace('<value>', 'true' if value else 'false')
        self.kwin.run(kwin_script)

    def stick_window(self, window_id):
        logger.warning('stick_window() not implemented for KDE/Wayland.  The sticky property is not exposed in the KWin script API.')
        return

    def unstick_window(self, window_id):
        logger.warning('unstick_window() not implemented for KDE/Wayland:  The sticky property is not exposed in the KWin script API.')
        return

    def maximize_window(self, window_id, direction):
        #  direction:
        #    1 - horizontal
        #    2 - vertical
        #    3 - both
        if not window_id:
            logger.error('valid window_id not provided for maximize_window()')
            return
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    w.setMaximize(<maximize>);
}""".replace('<window_id>', window_id)
        if direction == 1:
            kwin_script = kwin_script.replace('<maximize>', 'false, true')
        elif direction == 2:
            kwin_script = kwin_script.replace('<maximize>', 'true, false')
        elif direction == 3:
            kwin_script = kwin_script.replace('<maximize>', 'true, true')
        else:
            logger.warning('maximize_window(direction) called with invalid value.  Must be 1 for horizontal, 2 for vertical, or 3 for both.')
            return
        self.kwin.run(kwin_script)

    def unmaximize_window(self, window_id, direction):
        #  direction:
        #    1 - horizontal
        #    2 - vertical
        #    3 - both
        if not window_id:
            logger.error('valid window_id not provided for unmaximize_window()')
            return
        if direction not in [1,2,3]:
            logger.warning('unmaximize_window(direction) called with invalid value.  Must be 1 for horizontal, 2 for vertical, or 3 for both.')
            return
        kwin_script = """const direction = <direction>;
const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    const s = workspace.clientArea(KWin.MaximizeArea, w);
    vert = (w.height > s.height);
    horz = (w.width == s.width);
    if (direction == 1) {
        w.setMaximize(vert, false);
    } else if (direction == 2){
        w.setMaximize(false, horz);
    } else if (direction == 3) {
        w.setMaximize(false, false);
    }
}""".replace('<window_id>', window_id)
        kwin_script = kwin_script.replace('<direction>', str(direction))
        self.kwin.run(kwin_script)

    def make_fullscreen_window(self, window_id):
        if not window_id:
            logger.error('valid window_id not provided for make_fullscreen_window()')
            return
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    w.fullScreen = true;
}""".replace('<window_id>', window_id)
        self.kwin.run(kwin_script)

    def unmake_fullscreen_window(self, window_id):
        if not window_id:
            logger.error('valid window_id not provided for unmake_fullscreen_window()')
            return
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    w.fullScreen = false;
}""".replace('<window_id>', window_id)
        self.kwin.run(kwin_script)

    def make_above_window(self, window_id):
        if not window_id:
            logger.error('valid window_id not provided make_above_window()')
            return
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    w.keepAbove = true;
}""".replace('<window_id>', window_id)
        self.kwin.run(kwin_script)

    def unmake_above_window(self, window_id):
        if not window_id:
            logger.error('valid window_id not provided for unmake_above_window()')
            return
        kwin_script = """const w = workspace.windowList().find((w) => w.internalId == '<window_id>');
if (w) {
    w.keepAbove = false;
}""".replace('<window_id>', window_id)
        self.kwin.run(kwin_script)

