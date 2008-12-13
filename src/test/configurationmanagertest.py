import unittest

import lib.configurationmanager as conf
from lib.phrase import *

CONFIG_FILE = "../../config/abbr.ini"

class LegacyImporterTest(unittest.TestCase):
    
    def setUp(self):
        self.importer = conf.LegacyImporter()
        self.importer.load_config(CONFIG_FILE)
        
    def testGlobalSettings(self):
        # Test old global defaults using a phrase that has no custom options defined
        # Locate otoh phrase
        otohPhrase = None
        for phrase in self.importer.phrases:
            if phrase.abbreviation == "otoh":
                otohPhrase = phrase
                break
                
        self.assert_(otohPhrase is not None)
        
        self.assertEqual(otohPhrase.immediate, False)
        self.assertEqual(otohPhrase.ignoreCase, False)
        self.assertEqual(otohPhrase.matchCase, False)
        self.assertEqual(otohPhrase.backspace, True)
        self.assertEqual(otohPhrase.omitTrigger, False)
        self.assertEqual(otohPhrase.triggerInside, False)
        
    def testPhraseCount(self):
        self.assertEqual(len(self.importer.phrases), 23)
        
    def testPhrase(self):
        # Locate brb phrase
        brbPhrase = None
        for phrase in self.importer.phrases:
            if phrase.abbreviation == "brb":
                brbPhrase = phrase
                break
                
        self.assert_(brbPhrase is not None)
        
        self.assertEqual(brbPhrase.phrase, "be right back")
        self.assertEqual(brbPhrase.description, "be right back")
        self.assertEqual(brbPhrase.mode, PhraseMode.ABBREVIATION)
        self.assertEqual(brbPhrase.immediate, True)
        
        