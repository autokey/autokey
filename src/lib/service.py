#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2008 Chris Dekter

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import time, logging, threading
import iomediator, ui, model
from iomediator import Key
from configmanager import *
from phrasemenu import *
from plugin.manager import PluginManager, PluginError

logger = logging.getLogger("service")

MAX_STACK_LENGTH = 150

def threaded(f):
    
    def wrapper(*args):
        t = threading.Thread(target=f, args=args, name="Phrase-thread")
        t.setDaemon(False)
        t.start()
        
    wrapper.__name__ = f.__name__
    wrapper.__dict__ = f.__dict__
    wrapper.__doc__ = f.__doc__
    return wrapper

class Service:
    """
    Handles general functionality and dispatching of results down to the correct
    execution service (phrase or script).
    """
    
    def __init__(self, app):
        logger.info("Starting service")
        self.configManager = app.configManager
        ConfigManager.SETTINGS[SERVICE_RUNNING] = False
        self.mediator = None
        self.app = app
        self.inputStack = []
        self.lastStackState = ''
        self.lastMenu = None
        self.phraseRunner = PhraseRunner(self)
        
    def start(self):
        self.mediator = iomediator.IoMediator(self)
        ConfigManager.SETTINGS[SERVICE_RUNNING] = True
        logger.info("Service now marked as running")
        
    def unpause(self):
        ConfigManager.SETTINGS[SERVICE_RUNNING] = True
        logger.info("Unpausing - service now marked as running")
        
    def pause(self):
        ConfigManager.SETTINGS[SERVICE_RUNNING] = False
        logger.info("Pausing - service now marked as stopped")
        
    def is_running(self):
        return ConfigManager.SETTINGS[SERVICE_RUNNING]
            
    def shutdown(self):
        logger.info("Service shutting down")
        if self.mediator is not None: self.mediator.shutdown()
        save_config(self.configManager)
            
    def handle_mouseclick(self):
        logger.debug("Received mouse click - resetting buffer")        
        self.inputStack = []
        
        # If we had a menu and receive a mouse click, means we already
        # hid the menu. Don't need to do it again
        self.lastMenu = None
        
    def handle_hotkey(self, key, modifiers, windowName):
        logger.debug("Key: %s, modifiers: %s", repr(key), modifiers)
        
        # Always check global hotkeys
        for hotkey in self.configManager.globalHotkeys:
            hotkey.check_hotkey(modifiers, key, windowName)
            
        if self.__shouldProcess(windowName):
            self.inputStack = []
            itemMatch = None
            menu = None

            for item in self.configManager.hotKeys:
                if item.check_hotkey(modifiers, key, windowName):
                    itemMatch = item
                    break

            if itemMatch is not None:
                if not itemMatch.prompt:
                    logger.info("Matched hotkey phrase/script with prompt=False")
                else:
                    logger.info("Matched hotkey phrase/script with prompt=True")
                    menu = PopupMenu(self, [], [itemMatch])
                    
            else:
                logger.debug("No phrase/script matched hotkey")
                for folder in self.configManager.hotKeyFolders:
                    if folder.check_hotkey(modifiers, key, windowName):
                        menu = PopupMenu(self, [folder], [])

            
            if menu is not None:
                logger.debug("Folder matched hotkey - showing menu")
                if self.lastMenu is not None:
                    self.lastMenu.remove_from_desktop()
                self.lastStackState = ''
                self.lastMenu = menu
                self.lastMenu.show_on_desktop()
            
            if itemMatch is not None:
                self.__processItem(itemMatch)
        
    def handle_keypress(self, key, windowName):
        logger.debug("Key: %s", key)
        
        if self.__shouldProcess(windowName):
            if self.__updateStack(key):
                currentInput = ''.join(self.inputStack)
                item, menu = self.__checkTextMatches([], self.configManager.abbreviations,
                                                    currentInput, windowName, True)
                if not item or menu:
                    item, menu = self.__checkTextMatches(self.configManager.allFolders,
                                                         self.configManager.allItems,
                                                         currentInput, windowName)
                                                         
                if item:
                    self.__processItem(item, currentInput)
                elif menu:
                    if self.lastMenu is not None:
                        self.lastMenu.remove_from_desktop()
                    self.lastMenu = menu
                    self.lastMenu.show_on_desktop()
                
                logger.debug("Input stack at end of handle_keypress: %s", self.inputStack)
                
                
    @threaded
    def item_selected(self, event, item):
        time.sleep(0.25) # wait for window to be active
        self.lastMenu = None # if an item has been selected, the menu has been hidden
        self.__processItem(item, self.lastStackState)
        
    def calculate_extra_keys(self, buffer):
        """
        Determine extra keys pressed since the given buffer was built
        """
        extraBs = len(self.inputStack) - len(buffer)
        if extraBs > 0:
            extraKeys = ''.join(self.inputStack[len(buffer)])
        else:
            extraBs = 0
            extraKeys = ''
        return (extraBs, extraKeys)

    def __updateStack(self, key):
        """
        Update the input stack in non-hotkey mode, and determine if anything
        further is needed.
        
        @return: True if further action is needed
        """
        if self.lastMenu is not None:
            if not ConfigManager.SETTINGS[MENU_TAKES_FOCUS]:
                self.lastMenu.remove_from_desktop()
                
            self.lastMenu = None
            
        if key == Key.BACKSPACE:
            # handle backspace by dropping the last saved character
            self.inputStack = self.inputStack[:-1]
            return False
            
        elif len(key) > 1:
            # non-simple key
            self.inputStack = []
            return False
        else:
            # Key is a character
            self.inputStack.append(key)
            if len(self.inputStack) > MAX_STACK_LENGTH:
                self.inputStack.pop(0)
            return True
            
    def __checkTextMatches(self, folders, items, buffer, windowName, immediate=False):
        """
        Check for an abbreviation/predictive match among the given folder and items 
        (scripts, phrases).
        
        @return: a tuple possibly containing an item to execute, or a menu to show
        """
        itemMatches = []
        folderMatches = []
        
        for item in items:
            if item.check_input(buffer, windowName):
                if not item.prompt and immediate:
                    return (item, None)
                else:
                    itemMatches.append(item)
                    
        for folder in folders:
            if folder.check_input(buffer, windowName):
                folderMatches.append(folder)
                break # There should never be more than one folder match anyway
        
        if self.__menuRequired(folderMatches, itemMatches, buffer):
            self.lastStackState = buffer
            return (None, PopupMenu(self, folderMatches, itemMatches))
        elif len(itemMatches) == 1:
            return (itemMatches[0], None)
        else:
            return (None, None)
            
                
    def __shouldProcess(self, windowName):
        """
        Return a boolean indicating whether we should take any action on the keypress
        """
        return windowName not in (ui.CONFIG_WINDOW_TITLE, ui.SELECTOR_DIALOG_TITLE) and self.is_running()
        
    def __processItem(self, item, buffer=''):
        if isinstance(item, model.Phrase):
            self.phraseRunner.execute(item, buffer)
        else:
            self.scriptRunner.execute(item, buffer)
        
        self.inputStack = []
        self.lastStackState = ''
        
    def __haveMatch(self, data):
        folderMatch, itemMatches = data
        if folder is not None:
            return True
        if len(items) > 0:
            return True
            
        return False
        
    def __menuRequired(self, folders, items, buffer):
        """
        @return: a boolean indicating whether a menu is needed to allow the user to choose
        """
        if len(folders) > 0:
            # Folders always need a menu
            return True
        if len(items) == 1:
            return items[0].should_prompt(buffer)
        elif len(items) > 1:
            # More than one 'item' (phrase/script) needs a menu
            return True
            
        return False
        

class PhraseRunner:
    
    def __init__(self, service):
        self.service = service
        self.pluginManager = PluginManager()
        
    def execute(self, phrase, buffer):
        mediator = self.service.mediator
        expansion = phrase.build_phrase(buffer)
        try:
            self.pluginManager.process_expansion(expansion, buffer)
        except PluginError, pe:
            logger.warn("A plug-in reported an error: " + pe.message)
            self.app.show_notify("A plug-in reported an error.", True, pe.message)
            
        phrase.parsePositionTokens(expansion)

        # Check for extra keys that have been typed since this invocation started
        mediator.acquire_lock()
        extraBs, extraKeys = self.service.calculate_extra_keys(buffer)
        mediator.release_lock()
        
        #self.ignoreCount = len(expansion.string) + expansion.backspaces + extraBs + len(extraKeys) + expansion.lefts
        
        mediator.send_backspace(expansion.backspaces + extraBs)
        mediator.send_string(expansion.string)
        mediator.send_string(extraKeys)
        mediator.send_left(expansion.lefts)
        mediator.flush()
    
        ConfigManager.SETTINGS[INPUT_SAVINGS] += (len(expansion.string) - phrase.calculate_input(buffer))
        #return len(expansion.string)