import unittest

import lib.configurationservice as conf

class ConfigurationServiceTest(unittest.TestCase):
    
    def setUp(self):
        self.service = conf.ConfigurationService() 
        
    def testGetSetting(self):
        self.assertEqual(self.service.get_setting("interface"), "XLib")
        
    def testGetAbbrDefaults(self):
        defaultsDict = self.service.get_abbreviation_defaults()
        self.assertEqual(defaultsDict["wordchars"], "\w")
        self.assertEqual(defaultsDict["backspace"], True)
        self.assertEqual(defaultsDict["immediate"], False)
        
    def testGetAbbrSettings(self):
        abbrContext = self.service.get_abbr_contexts()[0]
        settings = self.service.get_abbr_settings(abbrContext)
        self.assertEqual(settings["trigger"], "brb")
        self.assertEqual(settings["expanded"], "be right back")