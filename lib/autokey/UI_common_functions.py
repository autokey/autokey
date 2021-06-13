import dbus
import importlib
import os.path
from shutil import which
import re
import subprocess
import sys
import time

from . import common
import autokey.model.helpers

logger = __import__("autokey.logger").logger.get_logger(__name__)

common_modules = ['argparse', 'collections', 'enum', 'faulthandler', 
            'gettext', 'inspect', 'itertools', 'logging', 'os', 'select', 'shlex',
            'shutil', 'subprocess', 'sys', 'threading', 'time', 'traceback', 'typing',
            'warnings', 'webbrowser', 'dbus', 'pyinotify']
gtk_modules = ['gi', 'gi.repository.Gtk', 'gi.repository.Gdk', 'gi.repository.Pango',
            'gi.repository.Gio', 'gi.repository.GtkSource']
qt_modules = ['PyQt5', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtCore',
            'PyQt5.Qsci']

common_programs = ['wmctrl', 'ps']
# Checking some of these appears to be redundant as some are provided by the same packages on my system but 
# better safe than sorry.
optional_programs = ['visgrep', 'import', 'png2pat', 'xte', 'xmousepos']
gtk_programs = ['zenity']
qt_programs = ['kdialog']

def checkModuleImports(modules):
    missing_modules = []
    for module in modules:
        spec = importlib.util.find_spec(module)
        if spec is None: #module has not been imported/found correctly
            logger.error("Python module \""+module+"\" was not found/able to be imported correctly. Check that it is installed correctly")
            missing_modules.append(module)

    return missing_modules

def checkProgramImports(programs, optional=False):
    missing_programs = []
    for program in programs:
        if which(program) is None:
            # file not found by shell
            status="Commandline program \""+program+"\" was not found/able to be used correctly by AutoKey."
            suggestion="Check that \""+program+"\" exists on your system and is in the $PATH seen by Autokey."
            if optional:
                logger.info(status +
                        " This program is optional for Autokey operation, but if you wish to use functionality associated with it, " + suggestion)
            else:
                logger.error(status + " " + suggestion)
            missing_programs.append(program)
    return missing_programs

def checkOptionalPrograms():
    if common.USING_QT:
        checkProgramImports(optional_programs, optional=True)
    else:
        checkProgramImports(optional_programs, optional=True)

def getErrorMessage(item_type, missing_items):
    error_message = ""
    for item in missing_items:
         error_message+= item_type+": "+item+"\n"
    return error_message

def checkRequirements():
    errorMessage = ""
    if common.USING_QT:
        missing_programs = checkProgramImports(common_programs+qt_programs)
        missing_modules = checkModuleImports(common_modules+qt_modules)
    else:
        missing_programs = checkProgramImports(common_programs+gtk_programs)
        missing_modules = checkModuleImports(common_modules+gtk_modules)
    errorMessage += getErrorMessage("Python Modules",missing_modules)
    errorMessage += getErrorMessage("Programs",missing_programs)
    return errorMessage


def create_storage_directories():
    """Create various storage directories, if those do not exist."""
    # Create configuration directory
    makedir_if_not_exists(common.CONFIG_DIR)
    # Create data directory (for log file)
    makedir_if_not_exists(common.DATA_DIR)
    # Create run directory (for lock file)
    makedir_if_not_exists(common.RUN_DIR)

def makedir_if_not_exists(d):
    if not os.path.exists(d):
        os.makedirs(d)

def create_lock_file():
    with open(common.LOCK_FILE, "w") as lock_file:
        lock_file.write(str(os.getpid()))

def read_pid_from_lock_file() -> str:
    with open(common.LOCK_FILE, "r") as lock_file:
        pid = lock_file.read()
    try:
        # Check if the pid file contains garbage
        int(pid)
    except ValueError:
        logger.exception("AutoKey pid file contains garbage instead of a usable process id: " + pid)
        sys.exit(1)
    return pid


def get_process_details(pid):
    with subprocess.Popen(["ps", "-p", pid, "-o", "command"], stdout=subprocess.PIPE) as p:
        output = p.communicate()[0].decode()
    return output

def check_pid_is_a_running_autokey(pid):
    output = get_process_details(pid)

def is_existing_running_autokey():
    if os.path.exists(common.LOCK_FILE):
        pid = read_pid_from_lock_file()
        # Check that the found PID is running and is autokey
        output = get_process_details(pid)
        if "autokey" in output:
            logger.debug("AutoKey is already running as pid %s", pid)
            return True
    return False

def test_Dbus_response(app):
    bus = dbus.SessionBus()
    try:
        dbus_service = bus.get_object("org.autokey.Service", "/AppService")
        dbus_service.show_configure(dbus_interface="org.autokey.Service")
        sys.exit(0)
    except dbus.DBusException as e:
        pid = read_pid_from_lock_file()
        message="AutoKey is already running as pid {} but is not responding".format(pid)
        logger.exception(
            "Error communicating with Dbus service. {}".format(message))
        app.show_error_dialog(
            message=message,
            details=str(e))
        sys.exit(1)


# def init_global_hotkeys(app, configManager):
#     logger.info("Initialise global hotkeys")
#     configManager.toggleServiceHotkey.set_closure(app.toggle_service)
#     configManager.configHotkey.set_closure(app.show_configure_signal.emit)
#     This line replaces the above line in the gtk app. Need to find out
#     what the difference is before continuing.
#     configManager.configHotkey.set_closure(app.show_configure_async)


def hotkey_created(app_service, item):
    logger.debug("Created hotkey: %r %s", item.modifiers, item.hotKey)
    app_service.mediator.interface.grab_hotkey(item)

def hotkey_removed(app_service, item):
    logger.debug("Removed hotkey: %r %s", item.modifiers, item.hotKey)
    app_service.mediator.interface.ungrab_hotkey(item)

def path_created_or_modified(configManager, configWindow, path):
    time.sleep(0.5)
    changed = configManager.path_created_or_modified(path)
    set_file_watched(configManager.app.monitor, path, True)
    if changed and configWindow is not None:
        configWindow.config_modified()

def set_file_watched(appmonitor, path, watch):
    if not appmonitor.has_watch(path) and os.path.isdir(path): 
        appmonitor.suspend()
        if watch:
            appmonitor.add_watch(path)
        else:
            appmonitor.remove_watch(path)
        appmonitor.unsuspend()

def path_removed(configManager, configWindow, path):
    time.sleep(0.5)
    changed = configManager.path_removed(path)
    set_file_watched(configManager.app.monitor, path, False)
    if changed and configWindow is not None:
        configWindow.config_modified()


def save_item_filter(app, item):
    filter_regex = app.get_filter_text()
    try:
        item.set_window_titles(filter_regex)
    except re.error:
        logger.error(
            "Invalid window filter regex: '{}'. Discarding without saving.".format(filter_regex)
        )
    item.set_filter_recursive(app.get_is_recursive())


def get_hotkey_text(app, key):
    if key in app.KEY_MAP:
        keyText = app.KEY_MAP[key]
    else:
        keyText = key
    return keyText


def save_hotkey_settings_dialog(app, item):
    mode = autokey.model.helpers.TriggerMode.HOTKEY
    if mode not in item.modes:
        item.modes.append(mode)

    modifiers = app.build_modifiers()

    if app.key in app.REVERSE_KEY_MAP:
        key = app.REVERSE_KEY_MAP[app.key]
    else:
        key = app.key

    if key is None:
        raise RuntimeError("Attempt to set hotkey with no key")
    logger.info("Item {} updated with hotkey {} and modifiers {}".format(item, key, modifiers))
    item.set_hotkey(modifiers, key)

def load_hotkey_settings_dialog(app, item):
    app.targetItem = item
    if autokey.model.helpers.TriggerMode.HOTKEY in item.modes:
        app.populate_hotkey_details(item)
    else:
        app.reset()

def load_global_hotkey_dialog(app, item):
    if item.enabled:
        app.populate_hotkey_details(item)
    else:
        app.reset()
