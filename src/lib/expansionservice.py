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
import iomediator, ui, configurationmanager
from iomediator import Key
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
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = False
        self.mediator = None
        self.app = app
        self.inputStack = []
        self.lastAbbr = None
        self.lastMenu = None
        self.clearAfter = 0  
        
    def start(self):
        self.mediator = iomediator.IoMediator(self)
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = True
        logger.info("Service now marked as running")
        
    def unpause(self):
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = True
        logger.info("Unpausing - service now marked as running")
        
    def pause(self):
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = False
        logger.info("Pausing - service now marked as stopped")
        
    def is_running(self):
        return self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING]
            
    def shutdown(self):
        logger.info("Service shutting down")
        if self.mediator is not None: self.mediator.shutdown()
        configurationmanager.save_config(self.configManager)
            
    def handle_mouseclick(self):
        logger.debug("Received mouse click - resetting buffers")        
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

            for item in self.configManager.hotKeyItems:
                if item.check_hotkey(modifiers, key, windowName):
                    itemMatch = item
                    break

            if itemMatch is not None:
                if not itemMatch.prompt:
                    logger.info("Matched hotkey phrase/script with prompt=False")
                else:
                    logger.info("Matched hotkey phrase with prompt=True")
                    menu = PopupMenu(self, [], [itemMatch])
                    
            else:
                logger.debug("No phrase/script matched hotkey")
                for folder in self.configManager.hotKeyFolders:
                    if folder.check_hotkey(modifiers, key, windowName):
                        menu = PopupMenu(self, folder, [])

            
            if menu is not None:
                if self.lastMenu is not None:
                    self.lastMenu.remove_from_desktop()
                self.lastStackState = '' # TODO this needs to somehow move to PhraseService!
                self.lastMenu = menu
                self.lastMenu.show_on_desktop()
            
            else:
                self.__processItem(itemMatch)
                     
        
        
    def handle_keypress(self, key, windowName):
        logger.debug("Key: %s", key)
        
        if self.__shouldProcess(windowName):
            if self.__updateStack(key):
                # TODO do the work
             
            

    def __updateStack(self, key):
        """
        Update the input stack in non-hotkey mode, and determine if anything
        further is needed.
        
        @return: True if further action is needed
        """
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
            
    def __checkTextMatches(self, folders, items):
        """
        Check for an abbreviation/predictive match among the given folder and items 
        (scripts, phrases).
        """
    
    def __shouldProcess(self, windowName):
        """
        Return a boolean indicating whether we should take any action on the keypress
        """
        return windowName != ui.CONFIG_WINDOW_TITLE and self.is_running():
        
    def __haveMatch(self, data):
        folderMatch, itemMatches = data
        if folder is not None:
            return True
        if len(items) > 0:
            return True
            
        return False
        
    def __menuRequired(self, folder, items):
        """
        @return: a boolean indicating whether a menu is needed to allow the user to choose
        """
        if folder is not None:
            # Folders always need a menu
            return True
        if len(items) > 1:
            # More than one 'item' (phrase/script) needs a menu
            return True
            
        return False
        

class ExpansionService:
    
    def __init__(self, app):
        self.lastStackState = ''
        self.pluginManager = PluginManager()



    
    def handle_keypress(self, key, windowName=""):
        # TODO - this method is really monolithic - refactor into several smaller ones
        
        # allow duplicate invocation of an abbreviation after a reasonable amount of time
        if self.clearAfter > 0:
            if self.clearAfter == 1:
                self.lastAbbr = None
            
            self.clearAfter -= 1
        
        if windowName in (ui.CONFIG_WINDOW_TITLE, ui.SELECTOR_DIALOG_TITLE) or not self.is_running():
            return

        if self.lastMenu is not None:
            if not self.configManager.SETTINGS[configurationmanager.MENU_TAKES_FOCUS]:
                self.lastMenu.remove_from_desktop()
                
            self.lastMenu = None
       

            currentInput = ''.join(self.inputStack)
            
            # Check abbreviation phrases first
            for phrase in self.configManager.abbrPhrases:
                if phrase.check_input(currentInput, windowName) and not phrase.prompt:
                    logger.debug("Matched abbreviation phrase with prompt=False")
                    if ConfigurationManager.SETTINGS[DETECT_UNWANTED_ABBR]:
                        # send only if not same as last abbreviation to prevent repeated autocorrect
                        if phrase.abbreviation != self.lastAbbr:
                            self.lastAbbr = phrase.abbreviation
                            self.clearAfter = self.__sendPhrase(phrase, currentInput) + len(self.lastAbbr) + 2
                        else:
                            # immediately clear last abbreviation to allow next invocation to trigger
                            self.lastAbbr = None
                    else:
                        self.__sendPhrase(phrase, currentInput)
                
                    return
                
            # Code below here only executes if no immediate abbreviation phrase is matched
            
            folderMatches = []
            phraseMatches = []            
            
            for folder in self.configManager.allFolders:
                if folder.check_input(currentInput, windowName):
                    folderMatches.append(folder)
                    
            for phrase in self.configManager.allPhrases:
                if phrase.check_input(currentInput, windowName):
                    phraseMatches.append(phrase)
                        
            if len(phraseMatches) > 0 or len(folderMatches) > 0:
                logger.debug("Matched abbrevation phrases/folders from full search")
                if len(phraseMatches) == 1 and not phraseMatches[0].should_prompt(currentInput):
                    # Single phrase match with no prompt
                    logger.debug("Single phrase match with no prompt - executing")
                    self.__sendPhrase(phraseMatches[0], currentInput)
                else:
                    logger.debug("Multiple phrase/folder matches or match requiring prompt - creating menu")
                    if self.lastMenu is not None:
                        self.lastMenu.remove_from_desktop()
                    self.lastStackState = currentInput
                    self.lastMenu = PhraseMenu(self, folderMatches, phraseMatches)
                    self.lastMenu.show_on_desktop()
                
        if len(self.inputStack) > MAX_STACK_LENGTH: 
            self.inputStack.pop(0)
            
        logger.debug("Input stack at end of handle_keypress: %s", self.inputStack)
    
    @threaded
    def phrase_selected(self, event, phrase):
        time.sleep(0.25) # wait for window to be active
        self.lastMenu = None # if a phrase has been selected, we can be sure the menu has been hidden
        self.__sendPhrase(phrase, self.lastStackState)
        
    def __sendPhrase(self, phrase, buffer=''):
        expansion = phrase.build_phrase(buffer)
        try:
            self.pluginManager.process_expansion(expansion, buffer)
        except PluginError, pe:
            logger.warn("A plug-in reported an error: " + pe.message)
            self.app.show_notify("A plug-in reported an error.", True, pe.message)
            
        phrase.parsePositionTokens(expansion)

        # Check for extra keys that have been typed since this invocation started
        # This looks pretty hacky, but if you can do better feel free to send a patch :)
        self.mediator.acquire_lock()
        extraBs = len(self.inputStack) - len(buffer)
        if extraBs > 0:
            extraKeys = ''.join(self.inputStack[len(buffer)])
        else:
            extraBs = 0
            extraKeys = ''
        self.mediator.release_lock()
        
        #self.ignoreCount = len(expansion.string) + expansion.backspaces + extraBs + len(extraKeys) + expansion.lefts
        self.inputStack = []
        
        self.mediator.send_backspace(expansion.backspaces + extraBs)
        self.mediator.send_string(expansion.string)
        self.mediator.send_string(extraKeys)
        self.mediator.send_left(expansion.lefts)
        self.mediator.flush()
    
        self.configManager.SETTINGS[configurationmanager.INPUT_SAVINGS] += (len(expansion.string) - phrase.calculate_input(buffer))
        self.lastStackState = ''
        return len(expansion.string)