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

import re

WORD_CHARS_REGEX_OPTION = "wordchars"
IMMEDIATE_OPTION = "immediate"
IGNORE_CASE_OPTION = "ignorecase"
MATCH_CASE_OPTION = "matchcase"
BACKSPACE_OPTION = "backspace"
OMIT_TRIGGER_OPTION = "omittrigger"
TRIGGER_INSIDE_OPTION = "triggerinside"

ABBREVIATION_OPTIONS = [
                        WORD_CHARS_REGEX_OPTION,
                        IMMEDIATE_OPTION,
                        IGNORE_CASE_OPTION,
                        MATCH_CASE_OPTION,
                        BACKSPACE_OPTION,
                        OMIT_TRIGGER_OPTION,
                        TRIGGER_INSIDE_OPTION
                        ]

def applySettings(targetDict, settings):
    """
    Central function for applying settings to to a dictionary
    
    @param targetDict: dictionary to apply the settings to
    @param settings: dictionary of configuration to be applied
    """
    if settings.has_key(WORD_CHARS_REGEX_OPTION):
        targetDict[WORD_CHARS_REGEX_OPTION] = re.compile(settings[WORD_CHARS_REGEX_OPTION], re.UNICODE)
    
    applyBooleanOption(IMMEDIATE_OPTION, targetDict, settings)    
    #if settings.has_key(IMMEDIATE_OPTION):
    #    targetDict[IMMEDIATE_OPTION] = (settings[IMMEDIATE_OPTION].lower()[0] == 't')

    applyBooleanOption(IGNORE_CASE_OPTION, targetDict, settings)
    #if settings.has_key(IGNORE_CASE_OPTION):
    #    targetDict[IGNORE_CASE_OPTION] = (settings[IGNORE_CASE_OPTION].lower()[0] == 't')
    
    applyBooleanOption(MATCH_CASE_OPTION, targetDict, settings)   
    #if settings.has_key(MATCH_CASE_OPTION):
    #    targetDict[MATCH_CASE_OPTION] = (settings[MATCH_CASE_OPTION].lower()[0] == 't')        
    
    applyBooleanOption(BACKSPACE_OPTION, targetDict, settings)    
    #if settings.has_key(BACKSPACE_OPTION):
    #    targetDict[BACKSPACE_OPTION] = (settings[BACKSPACE_OPTION].lower()[0] == 't')
    
    applyBooleanOption(OMIT_TRIGGER_OPTION, targetDict, settings)
    #if settings.has_key(OMIT_TRIGGER_OPTION):
    #    targetDict[OMIT_TRIGGER_OPTION] = (settings[OMIT_TRIGGER_OPTION].lower()[0] == 't')
     
    applyBooleanOption(TRIGGER_INSIDE_OPTION, targetDict, settings)   
    #if settings.has_key(TRIGGER_INSIDE_OPTION):
    #    targetDict[TRIGGER_INSIDE_OPTION] = (settings[TRIGGER_INSIDE_OPTION].lower()[0] == 't')
        
def applyBooleanOption(optionName, targetDict, settings):
    if settings.has_key(optionName):
        targetDict[optionName] = (settings[optionName].lower()[0] == 't')
        
class Abbreviation:
    
    global_settings = {}
    
    def __init__(self, abbreviation, config):
        """
        @param config: dictionary containing the config from the 'abbr' section
        """
        self.abbreviation = abbreviation
        self.expansion = config[abbreviation]
        self.settings = {}
        
        # Copy global settings
        for key, value in self.global_settings.iteritems():
            self.settings[key] = value
        
        # Apply local setting overrides
        ownSettings = {}
        startString = abbreviation + '.'
        offset = len(startString)
        for key, value in config.iteritems():
            if key.startswith(startString):
                ownSettings[key[offset:]] = value
                
        applySettings(self.settings, ownSettings)
        
        if self.settings[IGNORE_CASE_OPTION]:
            self.abbreviation = self.abbreviation.lower()
        
    def check_input(self, buffer):
        currentString = ''.join(buffer)
        
        if self.settings[IGNORE_CASE_OPTION]:
            matchString = currentString.lower()
            stringBefore, typedAbbr, stringAfter = matchString.rpartition(self.abbreviation)
            abbrStart = len(stringBefore)
            abbrEnd = abbrStart + len(typedAbbr)
            typedAbbr = currentString[abbrStart:abbrEnd]
        else:
            stringBefore, typedAbbr, stringAfter = currentString.rpartition(self.abbreviation)
            
        if len(typedAbbr) > 0:
            #splitList = matchString.split(self.abbreviation)
            #stringBefore = ''.join(splitList[:-1])
            #stringAfter = splitList[-1]
            
            # Check trigger character condition
            if not self.settings[IMMEDIATE_OPTION]:
                # If not immediate expansion, check last character
                if len(stringAfter) == 1:
                    # Have a character after abbr
                    if self.settings[WORD_CHARS_REGEX_OPTION].match(stringAfter):
                        # last character(s) is a word char, can't send expansion
                        return None
                    elif len(stringAfter) > 1:
                        # Abbr not at/near end of buffer any more, can't send
                        return None
                else:
                    # Nothing after abbr yet, can't expand yet
                    return None
            
            else:
                # immediate option enabled, check abbr is at end of buffer
                if len(stringAfter) > 0:
                    return None
                
            # Check chars ahead of abbr
            # length of stringBefore should always be > 0
            if len(stringBefore) > 0:
                if self.settings[WORD_CHARS_REGEX_OPTION].match(stringBefore[-1]):
                    # last char before is a word char
                    if not self.settings[TRIGGER_INSIDE_OPTION]:
                        # can't trigger when inside a word
                        return None
                
            expansion = self.__createExpansion()
            
            if expansion is not None:
                if self.settings[BACKSPACE_OPTION]:
                    # determine how many backspaces to send
                    expansion.backspaces = len(self.abbreviation) + len(stringAfter)
                
                if not self.settings[OMIT_TRIGGER_OPTION]:
                    expansion.string += stringAfter
                    
                if self.settings[MATCH_CASE_OPTION]:
                    if typedAbbr.istitle():
                        expansion.string = expansion.string.title()
                    elif typedAbbr.isupper():
                        expansion.string = expansion.string.upper()
                    elif typedAbbr.islower():
                        expansion.string = expansion.string.lower()
            
            return expansion
        
        return None
                
                
    def __createExpansion(self):
        if '%%' in self.expansion:
            try:
                firstpart, secondpart = self.expansion.split('%%')
                # count lefts and ups
                rows = secondpart.split('\n')
                result = Expansion(''.join([firstpart, secondpart]))
                result.lefts, result.ups = len(rows[0]), len(rows) - 1
                if not (self.settings[OMIT_TRIGGER_OPTION] or self.settings[IMMEDIATE_OPTION]):
                    result.lefts += 1
            except ValueError:
                print "Badly formatted abbreviation argument"
                return None
        else:
            result = Expansion(self.expansion)
        
        return result
    
class Expansion:
    
    def __init__(self, string):
        self.string = string
        self.ups = 0
        self.lefts = 0
        self.backspaces = 0
        
        

