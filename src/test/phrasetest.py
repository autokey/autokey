import re, unittest

from lib.phrase import *

class PhraseTest(unittest.TestCase):
    
    def setUp(self):
        # Set up global settings
        """globals = {
                    WORD_CHARS_REGEX_OPTION : re.compile('[\w]', re.UNICODE),
                    IMMEDIATE_OPTION : False,
                    IGNORE_CASE_OPTION : False,
                    MATCH_CASE_OPTION : False,
                    BACKSPACE_OPTION : True,
                    OMIT_TRIGGER_OPTION : False,
                    TRIGGER_INSIDE_OPTION : False
                   }"""
        
        self.defaultPhrase = Phrase("xp@", "expansion@autokey.com")
        self.defaultPhrase.set_abbreviation("xp@")
        self.defaultPhrase.set_modes([PhraseMode.ABBREVIATION])
        self.defaultFolder = PhraseFolder("Folder")
        self.defaultFolder.add_phrase(self.defaultPhrase)        
        
    def testImmediateOption(self):
        
        # Test default setting (false)
        self.assertEqual(self.defaultPhrase.check_input("xp@", ""), False)
        self.assertEqual(self.defaultPhrase.calculate_input("xp@ "), 4)
        
        # Test true setting
        phrase = Phrase("xp@", "expansion@autokey.com")
        phrase.immediate = True
        phrase.set_abbreviation("xp@")
        phrase.set_modes([PhraseMode.ABBREVIATION])
        self.defaultFolder.add_phrase(phrase)
        
        self.assertEqual(phrase.check_input("xp@", ""), True)
        result = phrase.build_phrase("xp@")
        self.assertEqual(result.string, "expansion@autokey.com")
        self.assertEqual(result.backspaces, 3)
        self.assertEqual(phrase.calculate_input("xp@"), 3)
        
        
    def testIgnoreCaseOption(self):
        
        # Test default setting (false)
        self.assertEqual(self.defaultPhrase.check_input("XP@ ", ""), False)
        
        # Test true setting
        phrase = Phrase("xp@", "expansion@autokey.com")
        phrase.ignoreCase = True
        phrase.set_abbreviation("xp@")
        phrase.set_modes([PhraseMode.ABBREVIATION])
        self.defaultFolder.add_phrase(phrase)
        self.assertEqual(phrase.check_input("XP@ ", ""), True)
        
        result = phrase.build_phrase("XP@ ")
        self.assertEqual(result.string, "expansion@autokey.com ")
        
    def testMatchCaseOption(self):
        phrase = Phrase("xp@", "expansion@autokey.com")
        phrase.ignoreCase = True
        phrase.matchCase = True
        phrase.set_abbreviation("xp@")
        phrase.set_modes([PhraseMode.ABBREVIATION])        
        self.defaultFolder.add_phrase(phrase)
        
        result = phrase.build_phrase("asdf XP@ ")
        self.assertEqual(result.string, "EXPANSION@AUTOKEY.COM ")        
        
        result = phrase.build_phrase("ASDF Xp@ ")
        self.assertEqual(result.string, "Expansion@Autokey.Com ")
        
        result = phrase.build_phrase("Asdf xp@ ")
        self.assertEqual(result.string, "expansion@autokey.com ")        
        
    def testBackspaceOption(self):        
        # Test default setting (true)
        result = self.defaultPhrase.build_phrase("xp@ ")
        self.assertEqual(result.backspaces, 4)
        
        # Test false setting
        phrase = Phrase("xp@", "expansion@autokey.com")
        phrase.backspace = False
        phrase.set_abbreviation("xp@")
        phrase.set_modes([PhraseMode.ABBREVIATION])        
        self.defaultFolder.add_phrase(phrase)
        
        result = phrase.build_phrase("xp@ ")
        self.assertEqual(result.backspaces, 0)
        
    def testOmitTriggerOption(self):        
        # Test default setting (false)
        result = self.defaultPhrase.build_phrase("xp@\n")
        self.assertEqual(result.string, "expansion@autokey.com\n")
        
        # Test true setting
        phrase = Phrase("xp@", "expansion@autokey.com")
        phrase.omitTrigger = True
        phrase.set_abbreviation("xp@")
        phrase.set_modes([PhraseMode.ABBREVIATION])        
        self.defaultFolder.add_phrase(phrase)
        
        result = phrase.build_phrase("xp@.")
        self.assertEqual(result.string, "expansion@autokey.com")
        self.assertEqual(result.backspaces, 4)
        
    def testTriggerInsideOption(self):        
        # Test default setting (false)
        self.assertEqual(self.defaultPhrase.check_input("asdfxp@\n", ""), False)

        # when separated by a non-word char, should still trigger
        self.assertEqual(self.defaultPhrase.check_input("asdf.xp@ ", ""), True)
        
        # Test true setting
        phrase = Phrase("xp@", "expansion@autokey.com")
        phrase.triggerInside = True
        phrase.set_abbreviation("xp@")
        phrase.set_modes([PhraseMode.ABBREVIATION])        
        self.defaultFolder.add_phrase(phrase)
        self.assertEqual(phrase.check_input("asdfxp@.", ""), True)
        
        result = phrase.build_phrase("asdfxp@.")
        self.assertEqual(result.string, "expansion@autokey.com.")
                
    def testLefts(self):        
        # Test with omit trigger false
        phrase = Phrase("Positioning Phrase", "[udc]%%[/udc]")
        phrase.set_abbreviation("udc")
        phrase.set_modes([PhraseMode.ABBREVIATION])
        self.defaultFolder.add_phrase(phrase)
        
        result = phrase.build_phrase("udc ")
        self.assertEqual(result.lefts, 7)
        
        # Test with omit trigger true
        phrase.omitTrigger = True
        result = phrase.build_phrase("udc ")
        self.assertEqual(result.lefts, 6)
        
        # Test with immediate true
        phrase.omitTrigger = False
        phrase.immediate = True
        result = phrase.build_phrase("udc")
        self.assertEqual(result.lefts, 6)
        
    def testMultipleAbbrs(self):
        phrase = Phrase("Some abbr", "Some abbr")
        phrase.set_abbreviation("sdf")
        phrase.set_modes([PhraseMode.ABBREVIATION])        
        self.defaultFolder.add_phrase(phrase)
        input = "fgh xp@asdf sdf "
        
        # Abbreviation should not trigger
        self.assertEqual(self.defaultPhrase.check_input(input, ""), False)
        
        self.assertEqual(phrase.check_input(input, ""), True)
        
    def testSort(self):
        phrase1 = Phrase("abbr1", "Some abbr")
        phrase2 = Phrase("abbr2", "Some abbr")
        self.defaultFolder.add_phrase(phrase1)
        self.defaultFolder.add_phrase(phrase2)
        
        phrases = [phrase1, phrase2]
        
        phrase1.usageCount = 0
        phrase2.usageCount = 1

        phrases.sort(reverse=True)

        self.assertEqual(phrases[0].description, "abbr2")
        self.assertEqual(phrases[1].description, "abbr1")
        
    def testNoneMode(self):
        phrase = Phrase("Test Phrase", "Testing")
        folder = PhraseFolder("Folder")
        folder.set_abbreviation("asdf")
        folder.set_modes([PhraseMode.ABBREVIATION])
        folder.add_phrase(phrase)
        result = phrase.build_phrase("asdf ")
        
        self.assertEqual(result.backspaces, 5)
        self.assertEqual(result.string, "Testing")
        self.assertEqual(phrase.calculate_input("asdf "), 5)
        self.assertEqual(phrase.should_prompt("asdf "), False)
        
    def testWindowName(self):
        phrase = Phrase("Some abbr", "Some abbr")
        phrase.set_window_titles(".*Eclipse.*")
        phrase.set_abbreviation("sdf")
        phrase.set_modes([PhraseMode.ABBREVIATION])                
        self.defaultFolder.add_phrase(phrase)
        self.assertEqual(phrase.check_input("sdf ", "blah - Eclipse Platform"), True)


class PredictivePhraseTest(unittest.TestCase):
    
    def setUp(self):
        self.phrase = Phrase("blah", "This is a test phrase")
        self.phrase.set_modes([PhraseMode.PREDICTIVE])
        folder = PhraseFolder("Folder")
        folder.add_phrase(self.phrase)
        
    def testPredict(self):
        self.assertEqual(self.phrase.check_input("This ", ""), True)
        self.assertEqual(self.phrase.check_input("This", ""), False)
        self.assertEqual(self.phrase.check_input("This i", ""), False)
        self.assertEqual(self.phrase.check_input("I don't have a problem. This ", ""), True)
        
    def testBuildPhrase(self):
        result = self.phrase.build_phrase("This ")
        self.assertEqual(result.backspaces, 0)
        self.assertEqual(result.string, "is a test phrase")
        
    def testCalcInput(self):
        self.assertEqual(self.phrase.calculate_input("This "), 5)
        
    def testShouldPrompt(self):
        self.assertEqual(self.phrase.should_prompt("This "), True)
        
class HotkeyPhrasetest(unittest.TestCase):
    
    def setUp(self):
        self.phrase = Phrase("blah", "This is a test phrase")
        self.phrase.set_modes([PhraseMode.HOTKEY])
        self.phrase.set_hotkey(["A", "B"], "n")
        folder = PhraseFolder("Folder")
        folder.add_phrase(self.phrase)
        
    def testHotkey(self):
        result = self.phrase.check_hotkey(["A", "B"], "n", "")
        self.assertEqual(result, True)
        
        result = self.phrase.check_hotkey(["B"], "n", "")
        self.assertEqual(result, False)
        
        result = self.phrase.check_hotkey(["A", "B"], "a", "")
        self.assertEqual(result, False)
        
    def testBuildPhrase(self):
        result = self.phrase.build_phrase("")
        self.assertEqual(result.string, "This is a test phrase") 
        
    def testCalcInput(self):
        self.assertEqual(self.phrase.calculate_input(''), 3)
        
class PhraseFolderTest(unittest.TestCase):
    
    def setUp(self):
        self.folder = PhraseFolder("Folder")
        self.folder.set_abbreviation("sdf")
        self.folder.set_modes([PhraseMode.ABBREVIATION])
                
    def testCheckInput(self):
        self.assertEqual(self.folder.check_input("sdf ", ""), True)
    
class E2ETest(unittest.TestCase):
    
    def setUp(self):
        self.topFolder = PhraseFolder("Top Folder")
        self.topFolder.set_abbreviation("top1")
        self.topFolder.set_modes([PhraseMode.ABBREVIATION])
        
        self.bottomFolder = PhraseFolder("Bottom Folder")
        self.bottomFolder.set_abbreviation("bottom1")
        self.bottomFolder.set_modes([PhraseMode.ABBREVIATION])
        self.topFolder.add_folder(self.bottomFolder)
        
        self.phrase = Phrase("blah", "The Phrase")
        self.phrase.set_abbreviation("asdf")
        self.phrase.set_hotkey(["A"], "n")
        self.phrase.set_modes([PhraseMode.ABBREVIATION, PhraseMode.HOTKEY, PhraseMode.PREDICTIVE])
        self.bottomFolder.add_phrase(self.phrase)
            
    def testCheckInput(self):
        self.assertEqual(self.topFolder.check_input("top1 ", ""), True)
        self.assertEqual(self.bottomFolder.check_input("bottom1 ", ""), True)
        self.assertEqual(self.phrase.check_input("asdf ", ""), True)
        self.assertEqual(self.phrase.check_input("The P", ""), True)
        self.assertEqual(self.phrase.check_hotkey(["A"], "n", ""), True)
        
    def testBuildPhraseDirect(self):
        result = self.phrase.build_phrase("asdf ")
        self.assertEqual(result.string, "The Phrase ")
        self.assertEqual(result.backspaces, 5)
        
        result = self.phrase.build_phrase("The P")
        self.assertEqual(result.string, "hrase")
        self.assertEqual(result.backspaces, 0)
        
        result = self.phrase.build_phrase("")
        self.assertEqual(result.string, "The Phrase")
        self.assertEqual(result.backspaces, 0)
        
    def testBackspacesIndirect(self):
        result = self.phrase.build_phrase("top1 ")
        self.assertEqual(result.backspaces, 5)
        
        result = self.phrase.build_phrase("bottom1 ")
        self.assertEqual(result.backspaces, 8)
