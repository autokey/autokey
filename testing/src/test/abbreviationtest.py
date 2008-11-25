import unittest

import sys
sys.path.append("../")

from lib.abbreviation import *

class AbbreviationTest(unittest.TestCase):
    
    def setUp(self):
        # Set up global settings
        globals = {
                    WORD_CHARS_REGEX_OPTION : '[\w~]',
                    IMMEDIATE_OPTION : 'false',
                    IGNORE_CASE_OPTION : 'false',
                    MATCH_CASE_OPTION : 'false',
                    BACKSPACE_OPTION : 'true',
                    OMIT_TRIGGER_OPTION : 'false',
                    TRIGGER_INSIDE_OPTION : 'false'
                   }
        
        applySettings(Abbreviation.global_settings, globals)
        self.defaultAbbr = Abbreviation(["xp@"], {"xp@" : "expansion@autokey.com"})
        
    def testApplySettings(self):
        self.assertEqual(self.defaultAbbr.settings[IMMEDIATE_OPTION], False)
        self.assertEqual(self.defaultAbbr.settings[IGNORE_CASE_OPTION], False)
        self.assertEqual(self.defaultAbbr.settings[MATCH_CASE_OPTION], False)
        self.assertEqual(self.defaultAbbr.settings[BACKSPACE_OPTION], True)
        self.assertEqual(self.defaultAbbr.settings[OMIT_TRIGGER_OPTION], False)
        self.assertEqual(self.defaultAbbr.settings[TRIGGER_INSIDE_OPTION], False)
        
    def testImmediateOption(self):
        
        # Test default setting (false)
        self.assertEqual(self.defaultAbbr.check_input("xp@"), None)
        
        # Test true setting
        config = {
                  "xp@" : "expansion@autokey.com",
                  "xp@.immediate" : "true"
                  }
        keys = config.keys()
	keys.sort()
        abbr = Abbreviation(keys, config)
        result = abbr.check_input("xp@")
        self.assertEqual(result.string, "expansion@autokey.com")
        self.assertEqual(result.backspaces, 3)
        
    def testIgnoreCaseOption(self):
        
        # Test default setting (false)
        self.assertEqual(self.defaultAbbr.check_input("XP@ "), None)
        
        # Test true setting
        config = {
                  "xp@" : "expansion@autokey.com",
                  "xp@.ignorecase" : "true"
                  }
        keys = config.keys()
	keys.sort()
        abbr = Abbreviation(keys, config)
        result = abbr.check_input("XP@ ")
        self.assertEqual(result.string, "expansion@autokey.com ")
        
    def testMatchCaseOption(self):
        config = {
                  "xp@" : "expansion@autokey.com",
                  "xp@.ignorecase" : "true",
                  "xp@.matchcase" : "true"
                  }
        
        keys = config.keys()
	keys.sort()
        abbr = Abbreviation(keys, config)
        result = abbr.check_input("asdf XP@ ")
        self.assertEqual(result.string, "EXPANSION@AUTOKEY.COM ")        
        
        result = abbr.check_input("ASDF Xp@ ")
        self.assertEqual(result.string, "Expansion@Autokey.Com ")
        
        result = abbr.check_input("Asdf xp@ ")
        self.assertEqual(result.string, "expansion@autokey.com ")        
        
    def testBackspaceOption(self):
        
        # Test default setting (true)
        result = self.defaultAbbr.check_input("xp@ ")
        self.assertEqual(result.backspaces, 4)
        
        # Test false setting
        config = {
                  "xp@" : "expansion@autokey.com",
                  "xp@.backspace" : "false"
                  }
        keys = config.keys()
	keys.sort()
        abbr = Abbreviation(keys, config)
        result = abbr.check_input("xp@ ")
        self.assertEqual(result.backspaces, 0)
        
    def testOmitTriggerOption(self):
        
        # Test default setting (false)
        result = self.defaultAbbr.check_input("xp@\n")
        self.assertEqual(result.string, "expansion@autokey.com\n")
        
        # Test true setting
        config = {
                  "xp@" : "expansion@autokey.com",
                  "xp@.omittrigger" : "true"
                  }
        keys = config.keys()
	keys.sort()
        abbr = Abbreviation(keys, config)
        result = abbr.check_input("xp@.")
        self.assertEqual(result.string, "expansion@autokey.com")
        self.assertEqual(result.backspaces, 4)
        
    def testTriggerInsideOption(self):
        
        # Test default setting (false)
        self.assertEqual(self.defaultAbbr.check_input("asdfxp@\n"), None)

        # when separated by a non-word char, should still trigger
        result = self.defaultAbbr.check_input("asdf.xp@ ")
        self.assertEqual(result.string, "expansion@autokey.com ")
        
        # Test true setting
        config = {
                  "xp@" : "expansion@autokey.com",
                  "xp@.triggerinside" : "true"
                  }
        keys = config.keys()
	keys.sort()
        abbr = Abbreviation(keys, config)
        result = abbr.check_input("asdfxp@.")
        self.assertEqual(result.string, "expansion@autokey.com.")
                
    def testLefts(self):
        
        # Test with omit trigger false
        abbr = Abbreviation(["udc"], {"udc" : "[udc]%%[/udc]"})
        result = abbr.check_input("udc ")
        self.assertEqual(result.lefts, 7)
        
        # Test with omit trigger true
        config = {
                  "udc" : "[udc]%%[/udc]",
                  "udc.omittrigger" : "true"
                  }
        keys = config.keys()
	keys.sort()
        abbr = Abbreviation(keys, config)
        result = abbr.check_input("udc ")
        self.assertEqual(result.lefts, 6)
        
        # Test with immediate true
        config = {
                  "udc" : "[udc]%%[/udc]",
                  "udc.immediate" : "true"
                  }
        keys = config.keys()
	keys.sort()
        abbr = Abbreviation(keys, config)
        result = abbr.check_input("udc")
        self.assertEqual(result.lefts, 6)        
        
    def testMultipleAbbrs(self):
        
        abbr = Abbreviation(["sdf"], {"sdf" : "Some abbr"})
        input = "fgh xp@asdf sdf "
        
        # Abbreviation should not trigger
        self.assertEqual(self.defaultAbbr.check_input(input), None)
        
        result = abbr.check_input(input)
        self.assertEqual(result.string, "Some abbr ")
        
if __name__ == "__main__":
    unittest.main()
