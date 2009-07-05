#!/usr/bin/env python

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

import time, logging
import iomediator, ui, configurationmanager
from iomediator import Key, threaded
from phrasemenu import *
from plugin.manager import PluginManager, PluginError

logger = logging.getLogger("phrase-service")

MAX_STACK_LENGTH = 50

class ExpansionService:
    
    def __init__(self, app):
        # Read configuration
        self.configManager = app.configManager
        #self.interfaceType = iomediator.X_RECORD_INTERFACE
        self.interfaceType = iomediator.X_EVDEV_INTERFACE # TODO make configurable
        self.mediator = None
        self.app = app
    
    def start(self):
        logger.info("Starting phrase service")
        self.mediator = iomediator.IoMediator(self, self.interfaceType)
        self.mediator.initialise()
        self.inputStack = []
        self.lastStackState = ''
        self.lastMenu = None
        self.lastAbbr = None
        self.clearAfter = 0
        self.pluginManager = PluginManager()
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = True
        logger.info("Phrase service now marked as running")
        
    def unpause(self):
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = True
        logger.info("Unpausing - phrase service now marked as running")
        
    def pause(self):
        #self.mediator.pause()
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = False
        logger.info("Pausing - phrase service now marked as stopped")
        
    def is_running(self):
        #if self.mediator is not None:
        #    return self.mediator.is_running()
        #else:
        #    return False
        return self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING]
        
    def switch_method(self, interface):
        """
        Switch keystroke interface to the new type
        """
        if self.is_running():
            self.pause()
            restart = True
        else:
            restart = False
        
        self.interfaceType = interface
        self.mediator.switch_interface(self.interfaceType)
        
        if restart:
            self.unpause()
            
    def shutdown(self):
        logger.info("Phrase service shutting down")
        self.mediator.shutdown()
        configurationmanager.save_config(self.configManager)
            
    def handle_mouseclick(self):
        # Initial attempt at handling mouseclicks
        # Since we have no way of knowing where the caret is after the click,
        # just throw away the input buffer.
        logger.debug("Received mouse click - resetting buffer")        
        self.inputStack = []
        
    def handle_hotkey(self, key, modifiers, windowName):
        logger.debug("Phrase service received hotkey")
        # Always check global hotkeys
        for hotkey in self.configManager.globalHotkeys:
            hotkey.check_hotkey(modifiers, key, windowName)
        
        # Check other hotkeys if service enabled and not in config window
        if not windowName == ui.CONFIG_WINDOW_TITLE and self.is_running():
            self.inputStack = []
            folderMatch = None
            phraseMatch = None
            menu = None
            
            # Check for a phrase match first
            for phrase in self.configManager.hotKeyPhrases:
                if phrase.check_hotkey(modifiers, key, windowName):
                    phraseMatch = phrase
                    break

            if phraseMatch is not None:
                if not phraseMatch.prompt:
                    logger.info("Matched hotkey phrase with prompt=False - executing")
                    self.__sendPhrase(phraseMatch)
                else:
                    logger.info("Matched hotkey phrase with prompt=True - executing")
                    menu = PhraseMenu(self, [], [phraseMatch])
                    
            else:
                for folder in self.configManager.hotKeyFolders:
                    if folder.check_hotkey(modifiers, key, windowName):
                        folderMatch = folder
                        break                    
                
                if folderMatch is not None:
                    logger.info("Matched hotkey folder - displaying")
                    menu = PhraseMenu(self, [folderMatch], [])
                
            if menu is not None:
                if self.lastMenu is not None:
                    self.lastMenu.remove_from_desktop()
                self.lastStackState = ''
                self.lastMenu = menu
                self.lastMenu.show_on_desktop()

    
    def handle_keypress(self, key, windowName=""):
        # TODO - this method is really monolithic - refactor into several smaller ones
        
        # allow duplicate invocation of an abbreviation after a reasonable amount of time
        if self.clearAfter > 0:
            if self.clearAfter == 1:
                self.lastAbbr = None
            
            self.clearAfter -= 1
        
        if windowName in (ui.CONFIG_WINDOW_TITLE, ui.SELECTOR_DIALOG_TITLE) or not self.is_running():
            return

        if self.lastMenu is not None and not self.configManager.SETTINGS[configurationmanager.MENU_TAKES_FOCUS]:
            # don't need to worry about hiding the menu if it has keyboard focus
            self.lastMenu.remove_from_desktop()
            self.lastMenu = None
       
        if key == Key.BACKSPACE:
            # handle backspace by dropping the last saved character
            self.inputStack = self.inputStack[:-1]
            
        elif len(key) > 1:
            # FIXME exception occurs if key is None
            # non-simple key
            self.inputStack = []
            
        else:
            # Key is a character
            self.inputStack.append(key)
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
            
        logger.debug("Input stack at end of handle_keypress: " + repr(self.inputStack))
    
    @threaded
    def phrase_selected(self, event, phrase):
        time.sleep(0.25) # wait for window to be active
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