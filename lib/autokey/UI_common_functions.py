import importlib
from shutil import which
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