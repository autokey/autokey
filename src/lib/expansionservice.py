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

logger = logging.getLogger("phrase-service")

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

class ExpansionService:
    
    def __init__(self, app):
        logger.info("Starting phrase service")
        self.configManager = app.configManager
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = False
        self.interfaceType = self.configManager.SETTINGS[configurationmanager.INTERFACE_TYPE]
        self.mediator = None
        self.app = app
        self.inputStack = []
        self.recentEntryStack = []
        self.lastStackState = ''
        self.lastMenu = None
        self.lastAbbr = None
        self.clearAfter = 0
        self.pluginManager = PluginManager()
        
    def start(self):
        self.mediator = iomediator.IoMediator(self, self.interfaceType)
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = True
        logger.info("Phrase service now marked as running")
        
    def unpause(self):
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = True
        logger.info("Unpausing - phrase service now marked as running")
        
    def pause(self):
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = False
        logger.info("Pausing - phrase service now marked as stopped")
        
    def is_running(self):
        return self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING]
            
    def shutdown(self):
        logger.info("Phrase service shutting down")
        if self.mediator is not None: self.mediator.shutdown()
        configurationmanager.save_config(self.configManager)
            
    def handle_mouseclick(self):
        logger.debug("Received mouse click - resetting buffers")        
        self.inputStack = []
        self.recentEntryStack = []
        
        # set menu to none. If we had a menu and receive a mouse click, means we already
        # hid the menu. don't need to do it again
        self.lastMenu = None
        
    def handle_hotkey(self, key, modifiers, windowName):
        logger.debug("Phrase service received hotkey")
        logger.debug("Key: %s, modifiers: %s", repr(key), modifiers)
        
        # Always check global hotkeys
        for hotkey in self.configManager.globalHotkeys:
            hotkey.check_hotkey(modifiers, key, windowName)
        
        # Check other hotkeys if service enabled and not in config window
        if not windowName == ui.CONFIG_WINDOW_TITLE and self.is_running():
            self.inputStack = []
            self.recentEntryStack = []
            folderMatch = None
            phraseMatch = None
            menu = None
            
            # Check for a phrase match first
            for phrase in self.configManager.hotKeyPhrases:
                logger.debug("Phrase %s checking hotkey", phrase)
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
                logger.debug("No phrase matched hotkey")
                for folder in self.configManager.hotKeyFolders:
                    logger.debug("Folder %s checking hotkey", folder)
                    if folder.check_hotkey(modifiers, key, windowName):
                        folderMatch = folder
                        break                    
                
                if folderMatch is not None:
                    logger.info("Matched hotkey folder - displaying")
                    menu = PhraseMenu(self, [folderMatch], [])
                else:
                    logger.debug("No folder matched hotkey")
                
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

        if self.lastMenu is not None:
            if not self.configManager.SETTINGS[configurationmanager.MENU_TAKES_FOCUS]:
                self.lastMenu.remove_from_desktop()
                
            self.lastMenu = None
       
        if key == Key.BACKSPACE:
            # handle backspace by dropping the last saved character
            self.inputStack = self.inputStack[:-1]
            self.recentEntryStack = self.recentEntryStack[:-1]
            
        elif len(key) > 1:
            # FIXME exception occurs if key is None
            # non-simple key
            self.inputStack = []
            self.recentEntryStack = []
            
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
            else:
                # Not an abbreviation, check for recent entry. Only add 'sentences' delimited by \n or .
                if self.configManager.SETTINGS[configurationmanager.TRACK_RECENT_ENTRY]:
                    self.recentEntryStack.append(key)
                    recentEntry = None
                    currentInput = ''.join(self.recentEntryStack)
                    
                    if key == '\n':
                        # Capture a terminal command
                        recentEntry = currentInput[:-1].rsplit('\n', 1)[-1]
                    elif key == '.':
                        # Capture a sentence, but only if it starts with a capital
                        recentEntry = currentInput[:-1].rsplit('.', 1)[-1].strip()
                        if len(recentEntry) > 0:
                            if not recentEntry[0].isupper():
                                recentEntry = None
                 
                    if recentEntry is not None:
                        minLength = self.configManager.SETTINGS[configurationmanager.RECENT_ENTRY_MINLENGTH]
                        if len(recentEntry) > minLength:
                            self.configManager.add_recent_entry(recentEntry)
                            self.recentEntryStack = []
                
        if len(self.inputStack) > MAX_STACK_LENGTH: 
            self.inputStack.pop(0)
        if len(self.recentEntryStack) > MAX_STACK_LENGTH: 
            self.recentEntryStack.pop(0)
            
        logger.debug("Input stack at end of handle_keypress: %s", self.inputStack)
        logger.debug("Recent entry stack at end of handle_keypress: %s", self.recentEntryStack)
    
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
        self.recentEntryStack = []
        
        self.mediator.send_backspace(expansion.backspaces + extraBs)
        self.mediator.send_string(expansion.string)
        self.mediator.send_string(extraKeys)
        self.mediator.send_left(expansion.lefts)
        self.mediator.flush()
    
        self.configManager.SETTINGS[configurationmanager.INPUT_SAVINGS] += (len(expansion.string) - phrase.calculate_input(buffer))
        self.lastStackState = ''
        return len(expansion.string)