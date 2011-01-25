#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Chris Dekter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os, os.path, logging, logging.handlers, Queue, subprocess

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import SIGNAL, Qt, QObject, QEvent

import service
from configmanager import *
from model import *

CONFIG_DIR = os.path.expanduser("~/.config/autokey")
LOCK_FILE = CONFIG_DIR + "/autokey.pid"
LOG_FILE = CONFIG_DIR + "/autokey.log"
MAX_LOG_SIZE = 5 * 1024 * 1024 # 5 megabytes
MAX_LOG_COUNT = 3
LOG_FORMAT = "%(levelname)s - %(name)s - %(message)s"

def create_abbreviation(abbr, contents):
    """
    Create a text abbreviation.
    
    When the given abbreviation is typed, it will be replaced with the given
    text.
    
    @param abbr: the abbreviation that will trigger the expansion
    @param contents: the expansion text
    @return: the created Phrase instance
    """
    if not CONFIG.check_abbreviation_unique(abbr, None):
        raise Exception("The specified abbreviation is already in use")
    
    s = Phrase(contents[:15], contents)
    set_abbreviation(s, abbr)   
    CONFIG.add_item(s)
    return s
    
def create_hotkey(modifiers, key, contents):
    """
    Create a text hotkey.
    
    When the given hotkey is pressed, it will be replaced with the given
    text. Modifiers must be given as a list of strings, with the following
    values permitted:
    
    <control>
    <alt>
    <super>
    <shift>
    
    The key must be an unshifted character (i.e. lowercase)
    
    @param modifiers: modifiers to use with the hotkey (as a list)
    @param key: the hotkey
    @param contents: the expansion text
    @return: the created Phrase instance
    """
    modifiers.sort()
    if not CONFIG.check_hotkey_unique(modifiers, key, None):
        raise Exception("The specified hotkey and modifier combination is already in use")
    
    s = Phrase(contents[:15], contents)
    set_hotkey(s, modifiers, key)
    CONFIG.add_item(s)
    return s    
    
def create_script(tagName):
    """
    Create a script from a loaded script file.
    
    The code attached to the given tag name is taken from any script that
    has previously been loaded using load_script_file() and a Script instance
    is created.
    
    @param tagName: tag to which the desired code is attached
    @return: the created Script instance
    """
    code = CONFIG.scripts[tagName]
    s = Script(tagName, code)
    CONFIG.add_item(s)
    return s
    
def load_script_file(fileName):
    """
    Load a script file.
    
    @param fileName: full or relative path to the script file
    """
    CONFIG.load_script_file(fileName)

def start(debug=False):
    """
    Start the AutoKey back end.
    
    This function must be called last. Any configuration functions called
    after this function will have no effect.
    
    @param debug: enable debug logging to the console
    """
    CONFIG.prepare()
    a = AppStandAlone(debug)
    CONFIG.shutdownHotkey.set_closure(a.exit)
    CONFIG.toggleServiceHotkey.set_closure(a.toggle_service)
    try:
        a.main()
    except KeyboardInterrupt:
        a.exit()
        
def set_option(name, value):
    """
    Set a global option.
    
    The following options are available:
    ENABLE_QT4_WORKAROUND (True or False)
    INTERFACE_TYPE (iomediator.X_RECORD_INTERFACE, iomediator.X_EVDEV_INTERFACE, iomediator.ATSPI_INTERFACE)
    UNDO_USING_BACKSPACE (True or False)
    
    @param name: name of the option (e.g. INTERFACE_TYPE)
    @param value: value to set for the option
    """
    CONFIG.SETTINGS[name] = value
    
def set_abbreviation(item, abbr):
    """
    Set an abbreviation.
    
    This function sets the abbreviation for a Script or Phrase instance.
    
    @param item: the Script or Phrase instance to be modified
    @param abbr: the abbreviation to be used
    """
    item.modes.append(TriggerMode.ABBREVIATION)
    item.abbreviation = abbr
    
def set_hotkey(item, modifiers, key):
    """
    Set a hotkey.
    
    This function sets the hotkey for a Script or Phrase instance. @see create_hotkey()
    
    @param item: the Script or Phrase instance to be modified
    @param modifiers: modifiers to use with the hotkey (as a list)
    @param key: the hotkey
    """    
    item.modes.append(TriggerMode.HOTKEY)
    item.set_hotkey(modifiers, key)
    
class AppStandAlone:
    
    def __init__(self, debug):
        self.app = QApplication(sys.argv)
        
        try:
            
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            # Initialise logger
            rootLogger = logging.getLogger()
            
            if debug:
                rootLogger.setLevel(logging.DEBUG)
                handler = logging.StreamHandler(sys.stdout)
            else:           
                rootLogger.setLevel(logging.INFO)
                handler = logging.handlers.RotatingFileHandler(LOG_FILE, 
                                        maxBytes=MAX_LOG_SIZE, backupCount=MAX_LOG_COUNT)
            
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            rootLogger.addHandler(handler)
            
            if self.__verifyNotRunning():
                self.__createLockFile()
                
            self.initialise()
            
        except Exception, e:
            logging.exception("Fatal error starting AutoKey: " + str(e))
            sys.exit(1)
            
        self.handler = CallbackEventHandler(self.app)
        
    def initialise(self):
        logging.info("Initialising application")
        self.configManager = CONFIG
        self.service = service.Service(self)
        self.service.start()
            
    def main(self):
        self.app.exec_()
        
    def exit(self):
        self.app.quit()
        self.service.shutdown(False)

    def toggle_service(self):
        """
        Convenience method for toggling the expansion service on or off.
        """
        if self.service.is_running():
            self.service.pause()
        else:
            self.service.unpause()
            
    def exec_in_main(self, callback, *args):
        self.handler.postEventWithCallback(callback, *args)
        
    def __createLockFile(self):
        f = open(LOCK_FILE, 'w')
        f.write(str(os.getpid()))
        f.close()
        
    def __verifyNotRunning(self):
        if os.path.exists(LOCK_FILE):
            f = open(LOCK_FILE, 'r')
            pid = f.read()
            f.close()
            
            # Check that the found PID is running and is autokey
            p = subprocess.Popen(["ps", "-p", pid, "-o", "command"], stdout=subprocess.PIPE)
            p.wait()
            output = p.stdout.readlines()
            if len(output) > 1:
                # process exists
                if "autokey" in output[1]:
                    logging.error("AutoKey is already running - exiting")
                    sys.exit(1)
         
        return True           
        
        
class CallbackEventHandler(QObject):

    def __init__(self, app):
        self.app = app
        QObject.__init__(self)
        self.queue = Queue.Queue()

    def customEvent(self, event):
        while True:
            try:
                callback, args = self.queue.get_nowait()
            except Queue.Empty:
                break
            try:
                callback(*args)
            except Exception:
                logging.warn("callback event failed: %r %r", callback, args, exc_info=True)

    def postEventWithCallback(self, callback, *args):
        self.queue.put((callback, args))
        self.app.postEvent(self, QEvent(QEvent.User))
        

class ConfigStandAlone:
    
    SETTINGS = ConfigManager.SETTINGS
    
    def __init__(self):
        # Needed by Service but not actually used in standalone version
        self.hotKeyFolders = []
        self.allFolders = []
        self.allItems = []
        self.globalHotkeys = []

        self.abbreviations = []
        self.hotKeys = []
        self.folder = Folder("saFolder")
        
        self.scripts = {}
        
    def add_item(self, item):
        self.allItems.append(item)
        self.folder.add_item(item)
        
    def load_script_file(self, fileName):
        f = open(fileName, 'r')
        inScriptBlock = False
        currentBlock = []
        
        for line in f:
            if line.startswith('<'):
                # Tag line starts a script block
                if inScriptBlock:
                    # Already in a script block, finalise last block
                    self.__finaliseBlock(tagName, currentBlock)
                    
                inScriptBlock = True
                tagName = line.strip()[1:-1]
                currentBlock = []
                
            elif inScriptBlock:
                currentBlock.append(line)
                
        if inScriptBlock:
            self.__finaliseBlock(tagName, currentBlock)
        
    def __finaliseBlock(self, tagName, lines):
        self.scripts[tagName] = ''.join(lines)
        
    def check_abbreviation_unique(self, abbreviation, targetPhrase):
        """
        Checks that the given abbreviation is not already in use.
        
        @param abbreviation: the abbreviation to check
        @param targetPhrase: the phrase for which the abbreviation to be used 
        """
        for item in self.allItems:
            if TriggerMode.ABBREVIATION in item.modes:
                if item.abbreviation == abbreviation:
                    return item is targetPhrase
        
        return True
            
    def check_hotkey_unique(self, modifiers, hotKey, targetPhrase):
        """
        Checks that the given hotkey is not already in use. Also checks the 
        special hotkeys configured from the advanced settings dialog.
        
        @param modifiers: modifiers for the hotkey
        @param hotKey: the hotkey to check
        @param targetPhrase: the phrase for which the hotKey to be used         
        """
        for item in self.allItems:
            if TriggerMode.HOTKEY in item.modes:
                if item.modifiers == modifiers and item.hotKey == hotKey:
                    return item is targetPhrase     

        for item in self.globalHotkeys:
            if item.enabled:
                if item.modifiers == modifiers and item.hotKey == hotKey:
                    return False

        return True
        
    def prepare(self):
        self.shutdownHotkey = GlobalHotkey()
        self.shutdownHotkey.set_hotkey(["<ctrl>"], "k")
        self.shutdownHotkey.enabled = True
        self.globalHotkeys.append(self.shutdownHotkey)
        
        self.configHotkey = GlobalHotkey()
        
        self.toggleServiceHotkey = GlobalHotkey()
        self.toggleServiceHotkey.set_hotkey(["<ctrl>", "<shift>"], "k")
        self.toggleServiceHotkey.enabled = True    
        self.globalHotkeys.append(self.toggleServiceHotkey)
        
        for item in self.allItems:
            if TriggerMode.HOTKEY in item.modes:
                self.hotKeys.append(item)
            if TriggerMode.ABBREVIATION in item.modes:
                self.abbreviations.append(item)
            
CONFIG = ConfigStandAlone()
