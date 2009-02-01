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

import time
import iomediator, configurationmanager, ui
from iomediator import Key
from phrasemenu import *
from plugin.manager import PluginManager, PluginError

MAX_STACK_LENGTH = 50

class ExpansionService:
    
    def __init__(self, app):
        # Read configuration
        self.configManager = configurationmanager.get_config_manager()
        self.interfaceType = iomediator.XLIB_INTERFACE # permanently set to xlib for the time being
        self.mediator = None
        self.app = app
    
    def start(self):
        self.mediator = iomediator.IoMediator(self, self.interfaceType)
        self.mediator.start()
        self.inputStack = []
        self.lastStackState = ''
        self.lastMenu = None
        self.lastAbbr = None
        self.clearAfter = 0
        self.pluginManager = PluginManager()
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = True
        
    def unpause(self):
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = True
        
    def pause(self):
        #self.mediator.pause()
        self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING] = False
        
    def is_running(self):
        #if self.mediator is not None:
        #    return self.mediator.is_running()
        #else:
        #    return False
        return self.configManager.SETTINGS[configurationmanager.SERVICE_RUNNING]
        
    def switch_method(self, method):
        """
        @deprecated: 
        """
        if self.is_running():
            self.pause()
            restart = True
        else:
            restart = False
        
        self.interfaceType = method
        
        if restart:
            self.start()
            
    def shutdown(self):
        self.mediator.shutdown()
        configurationmanager.save_config(self.configManager)
            
    def handle_mouseclick(self):
        # Initial attempt at handling mouseclicks
        # Since we have no way of knowing where the caret is after the click,
        # just throw away the input buffer.        
        self.inputStack = []
        
    def handle_hotkey(self, key, modifiers, windowName):
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
                    self.__sendPhrase(phraseMatch)
                else:
                    menu = PhraseMenu(self, [], [phraseMatch])
                    
            else:
                for folder in self.configManager.hotKeyFolders:
                    if folder.check_hotkey(modifiers, key, windowName):
                        folderMatch = folder
                        break                    
                
                if folderMatch is not None:
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
        
        if windowName == ui.CONFIG_WINDOW_TITLE or not self.is_running():
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
                if len(phraseMatches) == 1 and not phraseMatches[0].should_prompt(currentInput):
                    # Single phrase match with no prompt
                    self.__sendPhrase(phraseMatches[0], currentInput)
                else:
                    # Multiple matches or match requiring prompt - create menu
                    if self.lastMenu is not None:
                        self.lastMenu.remove_from_desktop()
                    self.lastStackState = currentInput
                    self.lastMenu = PhraseMenu(self, folderMatches, phraseMatches)
                    self.lastMenu.show_on_desktop()
                
        if len(self.inputStack) > MAX_STACK_LENGTH: 
            self.inputStack.pop(0)
            
        #print self.inputStack
        
    def phrase_selected(self, event, phrase):
        time.sleep(0.1) # wait for window to be active
        self.__sendPhrase(phrase, self.lastStackState)
        
    def __sendPhrase(self, phrase, buffer=''):
        expansion = phrase.build_phrase(buffer)
        try:
            self.pluginManager.process_expansion(expansion)
        except PluginError, pe:
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