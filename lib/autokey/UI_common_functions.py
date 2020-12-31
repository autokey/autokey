import importlib
import os.path
from shutil import which
import subprocess
from . import common

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
            logger.error("Python module: \""+module+"\" was not found/able to be imported correctly on the system check that the module(s) are installed correctly")
            missing_modules.append(module)

    return missing_modules

def checkProgramImports(programs, optional=False):
    missing_programs = []
    for program in programs:
        if which(program) is None:
            # file not found by shell
            if optional:
                logger.info("Optional Commandline Program: \""+program+"\" was not found/able to be used correctly by AutoKey. Check that this program is correctly installed on your system.")
            else:
                logger.error("Commandline Program: \""+program+"\" was not found/able to be used correctly by AutoKey. Check that this program is correctly installed on your system.")
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

